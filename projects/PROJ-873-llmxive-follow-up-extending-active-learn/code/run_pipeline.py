import os
import sys
import time
import json
import random
import logging
import argparse
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from config import get_config, PipelineConfig
from logging_config import init_logging, start_resource_monitoring, stop_resource_monitoring
from metrics import calculate_wasted_call_ratios, calculate_ndcg_at_10
from data_loader import load_injected_dataset
from models import CandidateList, ComparisonPair
from ranker import run_ranker_with_filter, apply_pre_clustering_filter
from clustering import cluster_documents
from sampling import run_sampling_pipeline

# Import the specific function for T048
from cross_dataset_generalization import run_cross_dataset_generalization_check

@dataclass
class ExperimentResult:
    variant: str
    seed: int
    ndcg_at_10: float
    wasted_call_ratio: float
    runtime_seconds: float
    peak_memory_mb: float

def check_data_integrity() -> None:
    """Verify required artifacts exist before proceeding."""
    config = get_config()
    required_files = [
        os.path.join(config.data_dir, 'processed', 'injected_datasets.json'),
        os.path.join(config.data_dir, 'processed', 'unique_subset.json'),
        os.path.join(config.data_dir, 'results', 'sample_config.json'),
        os.path.join(config.data_dir, 'results', 'consensus_sample.json'),
    ]
    
    for f in required_files:
        if not os.path.exists(f):
            raise FileNotFoundError(f"Required artifact missing: {f}")
    
    # Ensure consensus_sample.json is not empty
    with open(required_files[-1], 'r') as fh:
        data = json.load(fh)
        if not data:
            raise ValueError(f"Artifact {required_files[-1]} is empty")

def enforce_runtime_limit(max_hours: float) -> None:
    """Terminate if runtime exceeds threshold."""
    start = time.time()
    def handler(signum, frame):
        raise TimeoutError(f"Runtime exceeded {max_hours} hours")
    
    # Set timeout in seconds
    timeout_seconds = int(max_hours * 3600)
    # Note: signal.alarm only works on Unix, simplified for this implementation
    try:
        import signal
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout_seconds)
    except (AttributeError, ValueError):
        logging.warning("SIGALRM not available, skipping runtime limit enforcement")

def enforce_memory_limit(max_gb: float) -> None:
    """Terminate if memory exceeds threshold."""
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        new_limit = int(max_gb * 1024 * 1024 * 1024)
        resource.setrlimit(resource.RLIMIT_AS, (new_limit, hard))
    except (AttributeError, ValueError):
        logging.warning("RLIMIT_AS not available, skipping memory limit enforcement")

def run_single_seed_experiment(variant: str, seed: int, budget: int) -> ExperimentResult:
    """Run one seed of the experiment for a given variant."""
    random.seed(seed)
    np.random.seed(seed)
    
    start_time = time.time()
    start_resource_monitoring()
    
    # Load data
    injected_data = load_injected_dataset()
    
    # Run appropriate variant
    if variant == 'baseline':
        # Run baseline active ranker
        result = run_ranker_with_filter(injected_data, budget=budget, use_clustering=False)
    elif variant == 'clustering_aided':
        # Run clustering aided
        clusters = cluster_documents(injected_data)
        result = run_ranker_with_filter(injected_data, budget=budget, use_clustering=True, clusters=clusters)
    else:
        raise ValueError(f"Unknown variant: {variant}")
    
    peak_mem = stop_resource_monitoring()
    runtime = time.time() - start_time
    
    return ExperimentResult(
        variant=variant,
        seed=seed,
        ndcg_at_10=result['ndcg_at_10'],
        wasted_call_ratio=result['wasted_call_ratio'],
        runtime_seconds=runtime,
        peak_memory_mb=peak_mem
    )

def run_threshold_sweep() -> Dict[str, Any]:
    """Run the threshold sweep for clustering parameters."""
    # Placeholder for T025 implementation
    return {"status": "sweep_complete"}

def main():
    parser = argparse.ArgumentParser(description="Run the full pipeline")
    parser.add_argument('--variant', type=str, required=True, choices=['baseline', 'clustering_aided'],
                        help='Which variant to run')
    parser.add_argument('--budgets', type=int, nargs='+', default=[20, 50, 100],
                        help='LLM call budgets to test')
    parser.add_argument('--seeds', type=int, nargs='+', default=[1, 2, 3, 4, 5],
                        help='Random seeds to use')
    parser.add_argument('--cross-dataset', action='store_true',
                        help='Run cross-dataset generalization check (T048)')
    
    args = parser.parse_args()
    
    init_logging()
    config = get_config()
    
    if args.cross_dataset:
        # T048: Run Cross-Dataset Generalization Check
        logging.info("Executing Cross-Dataset Generalization Check (T048)...")
        try:
            result = run_cross_dataset_generalization_check()
            logging.info(f"T048 completed successfully. Results written to {result['output_file']}")
            return
        except Exception as e:
            logging.error(f"T048 failed: {e}")
            raise
    
    # Standard pipeline execution
    check_data_integrity()
    
    results = []
    for budget in args.budgets:
        for seed in args.seeds:
            logging.info(f"Running {args.variant} with budget={budget}, seed={seed}")
            try:
                res = run_single_seed_experiment(args.variant, seed, budget)
                results.append(asdict(res))
            except Exception as e:
                logging.error(f"Seed {seed} failed: {e}")
                continue
    
    # Write results
    output_path = os.path.join(config.data_dir, 'results', f'{args.variant}_results.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.info(f"Pipeline complete. Results saved to {output_path}")

if __name__ == '__main__':
    main()
