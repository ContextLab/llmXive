"""
Execute the single RULER 'Needle In A Haystack' task for User Story 1.

This script:
1. Loads the MiniMax model (frozen, Index Branch disabled).
2. Loads the 'Needle In A Haystack' task from the RULER dataset.
3. Runs inference with the dense baseline.
4. Runs inference with the Local Gradient Magnitude heuristic injected.
5. Computes Exact Match scores, timing metrics, and delta.
6. Writes results to `data/processed/us1_baseline_vs_heuristic.csv`.
"""
import os
import sys
import csv
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from models.mini_max_wrapper import create_minimax_wrapper, MiniMaxConfig
from heuristics.gradient_magnitude import GradientMagnitudeHeuristic, HeuristicConfig
from data.ruler_loader import load_ruler_dataset
from analysis.metrics import calculate_exact_match, validate_accuracy_delta
from utils.logging import setup_logger, HeuristicTimer, measure_heuristic

# Configure logging
logger = setup_logger("us1_experiment", level=logging.INFO)

def run_inference_with_baseline(
    wrapper, 
    prompt: str, 
    task_config: Dict[str, Any]
) -> tuple:
    """
    Run inference using the standard dense attention path (heuristic disabled).
    Returns (score, inference_time).
    """
    logger.info("Running dense baseline inference...")
    
    # Start timing
    start_time = time.perf_counter()
    
    # Disable heuristic injection for baseline
    wrapper.disable_heuristic()
    
    # Run inference (assuming wrapper has a run method that returns the answer string)
    # Note: The actual extraction of the answer depends on the model's output format.
    # We assume the wrapper returns the generated text which we then parse or match.
    # For RULER NIAH, we typically look for the specific needle string in the output.
    output = wrapper.run(prompt, max_tokens=task_config.get("max_tokens", 100))
    
    end_time = time.perf_counter()
    inference_time = end_time - start_time
    
    # Calculate score (Exact Match)
    # We need the target needle from the task config to compare
    target_needle = task_config.get("needle")
    score = calculate_exact_match(output, target_needle)
    
    logger.info(f"Baseline inference time: {inference_time:.4f}s, Score: {score}")
    return score, inference_time

def run_inference_with_heuristic(
    wrapper, 
    prompt: str, 
    task_config: Dict[str, Any],
    heuristic: GradientMagnitudeHeuristic
) -> tuple:
    """
    Run inference with the Local Gradient Magnitude heuristic injected.
    Returns (score, heuristic_time, inference_time).
    """
    logger.info("Running heuristic-injected inference...")
    
    # Enable heuristic
    wrapper.enable_heuristic(heuristic)
    
    # Start total timing
    start_total = time.perf_counter()
    
    # Run inference
    output = wrapper.run(prompt, max_tokens=task_config.get("max_tokens", 100))
    
    end_total = time.perf_counter()
    total_time = end_total - start_total
    
    # The heuristic_time is tracked internally by the wrapper or heuristic
    # We assume the wrapper exposes the accumulated heuristic time after run
    heuristic_time = wrapper.get_heuristic_accumulated_time()
    inference_time = total_time - heuristic_time
    
    # Calculate score
    target_needle = task_config.get("needle")
    score = calculate_exact_match(output, target_needle)
    
    logger.info(f"Heuristic time: {heuristic_time:.4f}s, Inference time: {inference_time:.4f}s, Score: {score}")
    return score, heuristic_time, inference_time

def main():
    logger.info("Starting User Story 1 Experiment: Needle In A Haystack")
    
    # 1. Setup Paths
    data_dir = project_root / "data"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / "us1_baseline_vs_heuristic.csv"
    
    # 2. Load Model
    # Use default config from T006/T008
    model_config = MiniMaxConfig(
        model_path=os.getenv("MINIMAX_MODEL_PATH", "MiniMaxAI/MiniMax-M3"),
        index_branch_disabled=True
    )
    wrapper = create_minimax_wrapper(model_config)
    
    # 3. Setup Heuristic
    heuristic_config = HeuristicConfig(
        top_k=5,  # Default from T011
        cpu_only=True
    )
    heuristic = GradientMagnitudeHeuristic(heuristic_config)
    
    # 4. Load Task Data
    # T004 ensures data is downloaded to data/raw/
    # We load the specific "Needle In A Haystack" task
    try:
        dataset = load_ruler_dataset(task_type="needle_in_a_haystack")
        if not dataset:
            raise ValueError("No 'Needle In A Haystack' tasks found in the dataset.")
        
        # Select the first task for this single-task execution
        task_data = dataset[0]
        task_id = task_data.get("id", "niah_001")
        prompt = task_data.get("prompt")
        
    except Exception as e:
        logger.error(f"Failed to load Ruler dataset: {e}")
        sys.exit(1)
    
    # 5. Execute Baseline
    try:
        baseline_score, baseline_inference_time = run_inference_with_baseline(
            wrapper, prompt, task_data
        )
    except Exception as e:
        logger.error(f"Baseline execution failed: {e}")
        sys.exit(1)
    
    # 6. Execute Heuristic
    try:
        heuristic_score, heuristic_time, heuristic_inference_time = run_inference_with_heuristic(
            wrapper, prompt, task_data, heuristic
        )
    except Exception as e:
        logger.error(f"Heuristic execution failed: {e}")
        sys.exit(1)
    
    # 7. Compute Metrics
    delta = baseline_score - heuristic_score
    is_valid = validate_accuracy_delta(delta, tolerance=0.02)
    
    logger.info(f"Results: Baseline={baseline_score}, Heuristic={heuristic_score}, Delta={delta}")
    logger.info(f"Delta within 2% tolerance: {is_valid}")
    
    # 8. Write Output
    row = {
        "task_id": task_id,
        "baseline_score": baseline_score,
        "heuristic_score": heuristic_score,
        "delta": delta,
        "heuristic_time": heuristic_time,
        "inference_time": heuristic_inference_time
    }
    
    file_exists = output_path.exists()
    with open(output_path, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    
    logger.info(f"Results written to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())