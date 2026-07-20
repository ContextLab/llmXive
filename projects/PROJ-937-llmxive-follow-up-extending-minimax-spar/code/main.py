import os
import sys
import argparse
import logging
import gc
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Local imports based on API surface
from utils.config import Config, get_default_config, enforce_cpu, set_random_seed
from utils.logger import setup_logger, get_structured_logger, log_resource_usage
from data.loader import download_and_verify_ruler
from eval.baseline_runner import run_baseline_experiment, DenseAttentionRunner
from eval.metrics import calculate_metrics, calculate_exact_match, calculate_f1, calculate_perplexity
from heuristics.block_entropy import BlockEntropyHeuristic, HeuristicConfig as EntropyConfig
from heuristics.gradient_magnitude import GradientMagnitudeHeuristic, HeuristicConfig as GradientConfig
from heuristics.recency_bias import RecencyBiasHeuristic, HeuristicConfig as RecencyConfig
from heuristics.fallback import apply_fallback_if_needed, FallbackConfig
from models.mini_max_wrapper import MiniMaxConfig, create_minimax_wrapper

def parse_args():
    parser = argparse.ArgumentParser(description="llmXive Sparse Attention Evaluation")
    parser.add_argument("--device", type=str, default="cpu", help="Device to run on (cpu)")
    parser.add_argument("--heuristic", type=str, default="entropy", choices=["entropy", "gradient", "recency"],
                        help="Heuristic to use for sparse attention selection")
    parser.add_argument("--baseline", type=bool, default=True, help="Run dense attention baseline")
    parser.add_argument("--output_dir", type=str, default="results", help="Directory for results")
    parser.add_argument("--data_dir", type=str, default="data/raw", help="Directory for raw data")
    parser.add_argument("--threshold", type=float, default=0.5, help="Threshold for heuristic selection")
    parser.add_argument("--top_k", type=int, default=4, help="Number of top blocks to keep if fallback needed")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    return parser.parse_args()

def get_heuristic_instance(name: str, config: Config) -> Any:
    """Factory to instantiate the correct heuristic class based on name."""
    if name == "entropy":
        return BlockEntropyHeuristic(config)
    elif name == "gradient":
        return GradientMagnitudeHeuristic(config)
    elif name == "recency":
        return RecencyBiasHeuristic(config)
    else:
        raise ValueError(f"Unknown heuristic: {name}")

def run_single_task(task_id: str, heuristic_name: str, model_wrapper, config: Config, logger):
    """
    Executes a single RULER task using the specified heuristic.
    Returns a dict with metrics for this task.
    """
    logger.info(f"Running task {task_id} with heuristic {heuristic_name}")
    start_time = time.time()
    
    # 1. Load data for this specific task (simplified for integration)
    # In a full implementation, this would stream from the preprocessed chunks
    # For this integration, we assume the wrapper handles the task loading or we pass a subset
    
    try:
        # Run inference with the heuristic
        # The wrapper is expected to use the heuristic to select blocks
        # We simulate the call structure expected by the wrapper
        result = model_wrapper.run_inference_with_heuristic(
            task_id=task_id,
            heuristic_name=heuristic_name,
            threshold=config.get("threshold", 0.5),
            top_k=config.get("top_k", 4)
        )
        
        # Calculate metrics
        # result should contain 'prediction', 'ground_truth', 'task_type'
        metrics = calculate_metrics(
            predictions=[result['prediction']],
            ground_truths=[result['ground_truth']],
            task_type=result.get('task_type', 'default')
        )
        
        elapsed = time.time() - start_time
        metrics['task_id'] = task_id
        metrics['heuristic'] = heuristic_name
        metrics['elapsed_seconds'] = elapsed
        
        logger.info(f"Task {task_id} completed: F1={metrics.get('f1', 0):.4f}, PPL={metrics.get('perplexity', 0):.4f}")
        return metrics

    except Exception as e:
        logger.error(f"Error running task {task_id}: {str(e)}", exc_info=True)
        return {
            "task_id": task_id,
            "heuristic": heuristic_name,
            "error": str(e),
            "f1": 0.0,
            "exact_match": 0.0,
            "perplexity": float('inf')
        }

def main():
    args = parse_args()
    
    # Setup
    set_random_seed(args.seed)
    enforce_cpu(args.device)
    
    # Initialize logger
    logger = setup_logger("main", level=logging.INFO)
    log_resource_usage(logger)
    
    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load Config
    config = get_default_config()
    config.update({
        "threshold": args.threshold,
        "top_k": args.top_k,
        "device": args.device
    })
    
    # Initialize Model
    logger.info("Initializing MiniMax Model Wrapper...")
    model_config = MiniMaxConfig(device=args.device, frozen=True)
    model_wrapper = create_minimax_wrapper(model_config)
    
    results = []
    baseline_results = {}
    
    # 1. Run Baseline (Dense Attention) if requested (T022c integration)
    if args.baseline:
        logger.info("Running Dense Attention Baseline (T022c)...")
        # We run the baseline runner which generates the ground truth set
        # The runner returns a dict of task_id -> metrics
        baseline_results = run_baseline_experiment(
            model_wrapper=model_wrapper,
            data_dir=args.data_dir,
            output_dir=str(output_path / "baseline"),
            logger=logger
        )
        logger.info(f"Baseline complete. {len(baseline_results)} tasks processed.")
    
    # 2. Run Heuristic Execution (T023 Core Logic)
    logger.info(f"Starting Heuristic Execution: {args.heuristic}...")
    
    # Determine which tasks to run (subset for demo/CI, ideally full RULER)
    # In a real run, this would iterate over the full dataset
    task_ids = ["task_001", "task_002", "task_003"] # Placeholder for actual task list from loader
    
    for task_id in task_ids:
        # Run heuristic
        heuristic_metrics = run_single_task(
            task_id=task_id,
            heuristic_name=args.heuristic,
            model_wrapper=model_wrapper,
            config=config,
            logger=logger
        )
        
        # Compare against baseline
        baseline_metrics = baseline_results.get(task_id, {})
        if baseline_metrics:
            baseline_f1 = baseline_metrics.get('f1', 0.0)
            current_f1 = heuristic_metrics.get('f1', 0.0)
            heuristic_metrics['baseline_f1'] = baseline_f1
            heuristic_metrics['f1_delta'] = current_f1 - baseline_f1
            heuristic_metrics['baseline_perplexity'] = baseline_metrics.get('perplexity', 0.0)
            heuristic_metrics['perplexity_delta'] = heuristic_metrics.get('perplexity', 0.0) - baseline_metrics.get('perplexity', 0.0)
        
        results.append(heuristic_metrics)
        
        # Cleanup memory between tasks
        gc.collect()
    
    # 3. Output Results
    output_file = output_path / f"heuristic_results_{args.heuristic}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results written to {output_file}")
    
    # Return summary
    return results

if __name__ == "__main__":
    main()