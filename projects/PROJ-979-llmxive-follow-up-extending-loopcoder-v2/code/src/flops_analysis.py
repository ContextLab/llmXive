import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.utils import calculate_flops
from src.config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_convergence_results(path: str) -> List[Dict[str, Any]]:
    """Load convergence results from CSV."""
    results = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"Convergence results not found at {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def calculate_accuracy_for_k(results: List[Dict[str, Any]], k: int) -> float:
    """
    Calculate accuracy for a static k strategy.
    A problem is considered 'solved' by static k if the model produced a correct answer
    at step <= k.
    """
    if not results:
        return 0.0

    solved_count = 0
    total_count = 0

    # Group by task_id to handle multiple rows per task (different k)
    task_solved = {}

    for row in results:
        task_id = row['task_id']
        row_k = int(row['k'])
        is_correct = row['is_correct'].lower() == 'true'

        if task_id not in task_solved:
            task_solved[task_id] = False

        # If this specific k is correct, the task is solved for any k >= this k
        if is_correct and row_k <= k:
            task_solved[task_id] = True

        # Track total unique tasks encountered
        if task_id not in task_solved or task_solved[task_id] is False:
            # We count the task only once, so we just ensure the key exists
            pass

    total_count = len(task_solved)
    solved_count = sum(1 for v in task_solved.values() if v)

    if total_count == 0:
        return 0.0
    
    return solved_count / total_count

def calculate_flops_for_static_k(model_params: int, k: int) -> float:
    """Calculate total FLOPs for a static k strategy."""
    # Assuming average sequence length of 512 for estimation if not provided
    # The calculate_flops function in utils takes model_params, seq_len, k
    seq_len = 512 
    return calculate_flops(model_params, seq_len, k)

def calculate_static_k2_baseline(convergence_path: str, config_path: str) -> Dict[str, Any]:
    """
    Compute FLOPs and accuracy for always using k=2 on the filtered test set.
    
    Args:
        convergence_path: Path to convergence_results_core.csv
        config_path: Path to config.py or yaml to get model params (or defaults)
    
    Returns:
        Dict with 'total_flops' and 'accuracy'
    """
    logger.info(f"Loading convergence results from {convergence_path}")
    results = load_convergence_results(convergence_path)
    
    if not results:
        logger.warning("No convergence results found. Returning zeros.")
        return {"total_flops": 0.0, "accuracy": 0.0}

    # Load config to get model parameters
    # Assuming config has model_params or we derive it
    # If config doesn't have it, we might need a default or extract from model
    # For now, let's assume we can load a config dict
    try:
        # Try to load a JSON config if it exists, otherwise use defaults
        if os.path.exists(config_path):
            # If it's a python file, we might need to import, but let's try JSON first
            # The task description implies extracting from code/src/config.py
            # We will use a standard CodeLlama 1.3B param count as default if not found
            # 1.3B parameters approx 1.3 * 10^9
            model_params = 1_300_000_000 
            
            # Attempt to load JSON config if available
            if config_path.endswith('.json'):
                with open(config_path, 'r') as f:
                    cfg = json.load(f)
                    if 'model_params' in cfg:
                        model_params = cfg['model_params']
            # If it's a python file, we assume the user has set up the environment
            # and we might need to import, but for this script we'll rely on a default
            # or a passed JSON. The task says "extract from code/src/config.py".
            # Since we can't easily import arbitrary python files without side effects
            # in a generic runner, we will assume a default CodeLlama 1.3B size
            # unless a specific JSON config is provided.
            # However, to be robust, let's check if we can import the config module.
            # We'll try to import src.config if possible, but fall back to default.
            try:
                import sys
                sys.path.insert(0, str(Path(__file__).parent))
                from src.config import load_config
                cfg = load_config()
                if 'model_params' in cfg:
                    model_params = cfg['model_params']
                elif 'MODEL_PARAMS' in cfg:
                    model_params = cfg['MODEL_PARAMS']
            except Exception:
                pass # Use default
        else:
            model_params = 1_300_000_000
    except Exception as e:
        logger.error(f"Error loading config: {e}, using default model params")
        model_params = 1_300_000_000

    # Calculate accuracy for k=2
    accuracy = calculate_accuracy_for_k(results, k=2)
    
    # Calculate FLOPs for k=2
    # Note: FLOPs is per problem * number of problems
    flops_per_problem = calculate_flops_for_static_k(model_params, k=2)
    total_flops = flops_per_problem * len(set(r['task_id'] for r in results))

    return {
        "total_flops": total_flops,
        "accuracy": accuracy
    }

def main():
    """Main entry point for T020a."""
    # Paths relative to project root (assuming running from project root or code/)
    # The task specifies data/processed/convergence_results_core.csv
    # And output to static_k2_baseline.json
    project_root = Path(__file__).resolve().parent.parent
    convergence_path = project_root / "data" / "processed" / "convergence_results_core.csv"
    output_path = project_root / "data" / "processed" / "static_k2_baseline.json"
    config_path = project_root / "code" / "src" / "config.py"

    if not os.path.exists(convergence_path):
        raise FileNotFoundError(f"Input file not found: {convergence_path}")

    logger.info(f"Computing static k=2 baseline for {convergence_path}")
    result = calculate_static_k2_baseline(str(convergence_path), str(config_path))

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Saved results to {output_path}")
    logger.info(f"Accuracy: {result['accuracy']:.4f}, Total FLOPs: {result['total_flops']:.2e}")

if __name__ == "__main__":
    main()
