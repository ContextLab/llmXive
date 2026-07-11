"""
Main entry point for the llmXive MiniMax Sparse Attention follow-up project.

This script loads the frozen MiniMax-M3 model, disables the Index Branch,
injects the Local Gradient Magnitude heuristic, and runs a single RULER
"Needle In A Haystack" task to generate baseline vs. heuristic metrics.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from models.mini_max_wrapper import MiniMaxConfig, create_minimax_wrapper, MiniMaxWrapper
from heuristics.gradient_magnitude import HeuristicConfig, GradientMagnitudeHeuristic
from data.ruler_loader import load_ruler_dataset, ensure_directory
from utils.logging import setup_logger, HeuristicTimer, measure_heuristic
from analysis.metrics import calculate_exact_match, calculate_f1, validate_threshold
from models.entities import Block, HeuristicSelector

# Constants
RULER_TASK_TYPE = "needle_in_a_haystack"
OUTPUT_DIR = project_root / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "us1_baseline_vs_heuristic.csv"
DEFAULT_BATCH_SIZE = 2  # Small batch for CPU safety
DEFAULT_K_TOP = 100  # Default top-k blocks to select

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MiniMax Sparse Attention Heuristic Evaluation")
    parser.add_argument("--model-path", type=str, required=True, help="Path to GGUF model file")
    parser.add_argument("--task-id", type=str, default=None, help="Specific RULER task ID to run (default: first available)")
    parser.add_argument("--k-top", type=int, default=DEFAULT_K_TOP, help="Number of top blocks to keep")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Batch size for gradient calculation")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    return parser.parse_args()

def run_single_task(
    model: MiniMaxWrapper,
    heuristic: GradientMagnitudeHeuristic,
    task_data: Dict[str, Any],
    task_id: str,
    k_top: int
) -> Dict[str, Any]:
    """
    Executes a single RULER task with both dense baseline and heuristic injection.
    Returns a dictionary of metrics.
    """
    logger = logging.getLogger(__name__)
    
    # Extract task components
    context = task_data.get("context", "")
    needle = task_data.get("needle", "")
    question = task_data.get("question", "")
    answer = task_data.get("answer", "")
    
    # 1. Baseline Run (Dense Attention - Index Branch Enabled)
    # Note: The wrapper handles the actual inference. We assume the default state 
    # of the wrapper is the dense baseline unless Index Branch is disabled.
    # For this task, we explicitly ensure Index Branch is ENABLED for baseline.
    model.set_index_branch_enabled(True)
    
    baseline_start = time.time()
    baseline_response = model.generate(question, context=context)
    baseline_end = time.time()
    inference_time_dense = baseline_end - baseline_start
    
    baseline_score = calculate_exact_match(baseline_response, answer)
    logger.info(f"Baseline (Dense) Exact Match: {baseline_score:.4f} | Time: {inference_time_dense:.4f}s")

    # 2. Heuristic Run (Sparse Attention - Index Branch Disabled)
    # Disable Index Branch to force heuristic selection
    model.set_index_branch_enabled(False)
    heuristic.set_k_top(k_top)
    
    heuristic_start = time.time()
    # The heuristic needs to compute gradients. 
    # We pass the context and question to the wrapper which internally 
    # calls the heuristic's forward/backward hooks.
    heuristic_response = model.generate(question, context=context, use_heuristic=True)
    heuristic_end = time.time()
    
    heuristic_time = heuristic_end - heuristic_start
    inference_time_heuristic = heuristic_end - heuristic_start # Includes heuristic overhead
    
    heuristic_score = calculate_exact_match(heuristic_response, answer)
    logger.info(f"Heuristic (Sparse) Exact Match: {heuristic_score:.4f} | Time: {heuristic_time:.4f}s")

    # Calculate Delta
    delta = abs(baseline_score - heuristic_score)
    is_within_tolerance = validate_threshold(delta, threshold=0.02)
    
    return {
        "task_id": task_id,
        "baseline_score": baseline_score,
        "heuristic_score": heuristic_score,
        "delta": delta,
        "heuristic_time": heuristic_time,
        "inference_time": inference_time_heuristic,
        "within_tolerance": is_within_tolerance
    }

def main():
    args = parse_args()
    
    # Setup Logging
    logger = setup_logger(level=getattr(logging, args.log_level.upper()))
    logger.info("Starting llmXive MiniMax Sparse Attention Evaluation (T012)")

    # Ensure output directory exists
    ensure_directory(OUTPUT_DIR)

    # 1. Load Model
    logger.info(f"Loading model from: {args.model_path}")
    if not os.path.exists(args.model_path):
        logger.error(f"Model file not found: {args.model_path}")
        sys.exit(1)

    model_config = MiniMaxConfig(
        model_path=args.model_path,
        n_ctx=4096, # Default context, adjust if needed
        n_batch=DEFAULT_BATCH_SIZE,
        n_threads=4, # CPU optimization
        verbose=False
    )
    
    try:
        model = create_minimax_wrapper(model_config)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # 2. Initialize Heuristic
    heuristic_config = HeuristicConfig(
        batch_size=args.batch_size,
        k_top=args.k_top,
        cpu_only=True
    )
    heuristic = GradientMagnitudeHeuristic(config=heuristic_config)

    # 3. Load Data
    logger.info("Loading RULER dataset...")
    try:
        dataset = load_ruler_dataset(task_type=RULER_TASK_TYPE)
        if not dataset or len(dataset) == 0:
            logger.error(f"No data found for task type: {RULER_TASK_TYPE}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    # Select specific task
    if args.task_id:
        task_data = next((t for t in dataset if t.get("id") == args.task_id), None)
        if not task_data:
            logger.error(f"Task ID {args.task_id} not found in dataset.")
            sys.exit(1)
        tasks_to_run = [task_data]
    else:
        tasks_to_run = [dataset[0]] # Run first available task
        logger.info(f"Running default task: {tasks_to_run[0].get('id', 'unknown')}")

    results = []
    
    for task in tasks_to_run:
        task_id = task.get("id", "unknown")
        logger.info(f"Processing task: {task_id}")
        
        try:
            result = run_single_task(
                model=model,
                heuristic=heuristic,
                task_data=task,
                task_id=task_id,
                k_top=args.k_top
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}", exc_info=True)
            # Continue to next task or fail? For MVP, we log and stop if critical.
            # But let's try to collect what we can.
            continue

    # 4. Write Results
    if results:
        import pandas as pd
        df = pd.DataFrame(results)
        df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Results written to: {OUTPUT_FILE}")
        
        # Print summary
        logger.info("=== Summary ===")
        for r in results:
            logger.info(f"Task: {r['task_id']} | Baseline: {r['baseline_score']:.4f} | Heuristic: {r['heuristic_score']:.4f} | Delta: {r['delta']:.4f} | Tolerance: {r['within_tolerance']}")
    else:
        logger.warning("No results generated.")
        sys.exit(1)

    logger.info("Execution completed successfully.")

if __name__ == "__main__":
    main()
