import os
import sys
import time
import json
import random
import logging
import argparse
from typing import List, Dict, Any, Optional

from config import get_config, PipelineConfig
from data_loader import prepare_injected_datasets, load_injected_dataset
from metrics import calculate_ndcg_at_10, calculate_wasted_call_ratios
from ranker import run_ranker_with_filter
from clustering import run_clustering_pipeline
from sampling import run_sampling_pipeline
from utils import ResourceWatchdog, enforce_resource_limits
from logging_config import init_logging, start_resource_monitoring, stop_resource_monitoring

# Initialize logging
init_logging()
logger = logging.getLogger(__name__)

class ExperimentResult:
    def __init__(self, seed: int, variant: str, ndcg: float, wasted_ratio: float, runtime: float, memory_peak_mb: float):
        self.seed = seed
        self.variant = variant
        self.ndcg = ndcg
        self.wasted_ratio = wasted_ratio
        self.runtime = runtime
        self.memory_peak_mb = memory_peak_mb

    def to_dict(self):
        return {
            "seed": self.seed,
            "variant": self.variant,
            "ndcg": self.ndcg,
            "wasted_ratio": self.wasted_ratio,
            "runtime": self.runtime,
            "memory_peak_mb": self.memory_peak_mb
        }

def check_data_integrity():
    """
    T041: Verify presence and non-empty status of intermediate artifacts.
    Ensures no silent failures in the pipeline (Constitution Principle III).
    """
    config = get_config()
    
    # Define required artifacts relative to config directories
    required_files = [
        os.path.join(config.processed_dir, 'injected_datasets.json'),
        os.path.join(config.processed_dir, 'unique_subset.json'),
        # consensus_sample.json is generated later in the pipeline, 
        # so we only check it if the pipeline is past the sampling stage.
        # For the initial integrity check before running the ranker, 
        # we ensure the data and unique subset exist.
    ]

    missing_files = []
    empty_files = []

    for f in required_files:
        if not os.path.exists(f):
            missing_files.append(f)
        elif os.path.getsize(f) == 0:
            empty_files.append(f)
    
    if missing_files:
        msg = f"Data integrity check failed: Missing required artifacts: {missing_files}"
        logger.error(msg)
        raise FileNotFoundError(msg)
    
    if empty_files:
        msg = f"Data integrity check failed: Empty required artifacts: {empty_files}"
        logger.error(msg)
        raise ValueError(msg)
    
    logger.info("Data integrity check passed: All required artifacts present and non-empty.")

def enforce_runtime_limit(max_hours: float):
    """Enforce runtime limit using watchdog."""
    watchdog = ResourceWatchdog(max_seconds=max_hours * 3600)
    watchdog.start()
    return watchdog

def enforce_memory_limit(max_gb: float):
    """Enforce memory limit using ulimit (should be set by validate_env.sh) and runtime check."""
    # This function can add additional runtime checks if needed
    pass

def run_single_seed_experiment(seed: int, variant: str, config: PipelineConfig):
    """Run the pipeline for a single seed and variant."""
    logger.info(f"Starting seed {seed} with variant {variant}")
    start_time = time.time()
    
    # Load injected dataset
    dataset = load_injected_dataset(config.processed_dir)
    
    # Run baseline or clustering-aided
    if variant == "baseline":
        # Baseline: process full candidate list without clustering
        # For this task, we assume the baseline logic is handled in run_ranker_with_filter
        # with no filter applied.
        results = run_ranker_with_filter(dataset, use_clustering=False, seed=seed)
    elif variant == "clustering_aided":
        # Clustering-aided: apply pre-clustering filter
        results = run_ranker_with_filter(dataset, use_clustering=True, seed=seed)
    else:
        raise ValueError(f"Unknown variant: {variant}")
    
    runtime = time.time() - start_time
    
    # Calculate metrics
    ndcg = results.get("ndcg@10", 0.0)
    wasted_ratio = results.get("wasted_ratio", 0.0)
    
    # Memory usage (approximate)
    import resource
    mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Convert KB to MB (Linux)
    
    return ExperimentResult(seed, variant, ndcg, wasted_ratio, runtime, mem_usage)

def run_threshold_sweep(config: PipelineConfig):
    """Run the parameter sweep for MinHash thresholds."""
    # This is handled by T025 tasks, but we include a stub for completeness
    logger.info("Threshold sweep not implemented in this task scope.")

def main():
    parser = argparse.ArgumentParser(description="Run the llmXive pipeline.")
    parser.add_argument("--variant", type=str, required=True, choices=["baseline", "clustering_aided"],
                        help="Variant to run: 'baseline' or 'clustering_aided'")
    parser.add_argument("--budgets", type=int, nargs="+", default=[20, 50, 100],
                        help="List of LLM call budgets")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1],
                        help="List of random seeds for reproducibility")
    
    args = parser.parse_args()
    
    config = get_config()
    init_logging()
    logger.info(f"Starting pipeline with variant={args.variant}, budgets={args.budgets}, seeds={args.seeds}")
    
    # Check data integrity before running
    try:
        check_data_integrity()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Data integrity check failed: {e}")
        sys.exit(1)
    
    # Enforce runtime limit (from config)
    watchdog = enforce_runtime_limit(config.max_runtime_hours)
    
    results = []
    for seed in args.seeds:
        try:
            result = run_single_seed_experiment(seed, args.variant, config)
            results.append(result.to_dict())
        except Exception as e:
            logger.error(f"Experiment failed for seed {seed}: {e}")
            # Continue with other seeds
            continue
    
    # Write results
    output_file = os.path.join(config.results_dir, f"experiment_results_{args.variant}_seeds_{args.seeds}.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results written to {output_file}")
    stop_resource_monitoring()
    watchdog.stop()

if __name__ == "__main__":
    main()