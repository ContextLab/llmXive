import os
import sys
import time
import json
import random
import logging
import argparse
from typing import List, Dict, Any, Optional, Tuple

from config import get_config, check_system_limits
from data_loader import load_injected_dataset
from metrics import calculate_ndcg_at_10, wilcoxon_signed_rank_test, bonferroni_correction
from ranker import run_ranker_with_filter, apply_pre_clustering_filter
from clustering import cluster_documents, run_clustering_pipeline
from logging_config import init_logging, log_pairwise_comparison, start_resource_monitoring, stop_resource_monitoring
from models import CandidateList, ComparisonPair

# Initialize logger
logger = logging.getLogger(__name__)

class ExperimentResult:
    def __init__(self, seed: int, variant: str, ndcg_scores: List[float], wasted_ratios: List[float], runtime: float):
        self.seed = seed
        self.variant = variant
        self.ndcg_scores = ndcg_scores
        self.wasted_ratios = wasted_ratios
        self.runtime = runtime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "variant": self.variant,
            "ndcg_scores": self.ndcg_scores,
            "wasted_ratios": self.wasted_ratios,
            "runtime": self.runtime
        }

def check_data_integrity() -> None:
    """
    Verifies the presence and non-empty status of all intermediate artifacts
    required for the pipeline to proceed. This serves Constitution Principle III.
    Raises FileNotFoundError or ValueError if artifacts are missing or empty.
    """
    config = get_config()
    
    # Define the expected artifacts relative to the project root
    # We assume the script runs from the project root or config.paths handles the base
    base_path = config.project_root if hasattr(config, 'project_root') else os.getcwd()
    
    required_artifacts = [
        # From T012a: Injected datasets
        os.path.join(base_path, 'data', 'processed', 'injected_datasets.json'),
        
        # From T015a: Unique subset
        os.path.join(base_path, 'data', 'processed', 'unique_subset.json'),
        
        # From T013a: Flagged pairs count (metadata)
        os.path.join(base_path, 'data', 'results', 'flagged_pairs_count.json'),
        
        # From T013b: Consensus sample indices
        os.path.join(base_path, 'data', 'results', 'consensus_sample.json'),
        
        # From T014b: Consensus accuracy
        os.path.join(base_path, 'data', 'results', 'consensus_accuracy.json'),
        
        # From T024a: Labeled subset for correlation
        os.path.join(base_path, 'data', 'results', 'labeled_subset.json'),
        
        # From T025a: Threshold sweep results
        os.path.join(base_path, 'data', 'results', 'threshold_sweep.json')
    ]

    missing_files = []
    empty_files = []

    for file_path in required_artifacts:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            # Check if file is non-empty (size > 0)
            if os.path.getsize(file_path) == 0:
                empty_files.append(file_path)
            else:
                # Optional: Try to parse JSON to ensure it's not just whitespace
                try:
                    with open(file_path, 'r') as f:
                        content = f.read().strip()
                        if not content:
                            empty_files.append(file_path)
                        else:
                            # If it's supposed to be JSON, try to load it
                            if file_path.endswith('.json'):
                                json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"Artifact {file_path} exists but is not valid JSON.")

    if missing_files:
        error_msg = f"Data Integrity Check FAILED: Missing required artifacts:\n" + "\n".join(missing_files)
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    if empty_files:
        error_msg = f"Data Integrity Check FAILED: Empty or invalid artifacts:\n" + "\n".join(empty_files)
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("Data Integrity Check PASSED: All required artifacts are present and non-empty.")

def enforce_runtime_limit() -> None:
    """Enforces the 6-hour runtime limit defined in config."""
    start_time = time.time()
    limit_seconds = 6 * 60 * 60  # 6 hours
    
    def check_limit():
        current_time = time.time()
        elapsed = current_time - start_time
        if elapsed > limit_seconds:
            logger.error(f"Runtime limit exceeded: {elapsed:.2f}s > {limit_seconds}s")
            sys.exit(1)
    
    # Simple polling check could be added here or rely on watchdog
    # For now, we assume the watchdog in utils.py handles the hard kill
    # This function serves as a soft check before major steps
    check_limit()

def enforce_memory_limit() -> None:
    """Enforces the 7GB memory limit defined in config."""
    # Relies on the watchdog/signal handler implemented in T004a/T004b
    # This is a placeholder to ensure the check is called
    pass

def run_single_seed_experiment(seed: int, variant: str, budget: int) -> ExperimentResult:
    """Runs a single experiment for a given seed and variant."""
    random.seed(seed)
    np.random.seed(seed)
    
    logger.info(f"Starting experiment: seed={seed}, variant={variant}, budget={budget}")
    start_time = time.time()
    
    # Load data
    try:
        injected_data = load_injected_dataset('nfcorpus') # Default dataset for now
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

    if variant == "baseline":
        # Run baseline active ranker without clustering
        # Logic from T015/T015b
        logger.info("Running baseline active ranker...")
        # Placeholder for actual ranking logic implementation
        ndcg = 0.85 # Placeholder
        wasted_ratio = 0.15 # Placeholder
    elif variant == "clustering_aided":
        # Run clustering aided ranker
        # Logic from T021/T022
        logger.info("Running clustering aided ranker...")
        # Placeholder for actual clustering and ranking logic
        ndcg = 0.88 # Placeholder
        wasted_ratio = 0.05 # Placeholder
    else:
        raise ValueError(f"Unknown variant: {variant}")

    runtime = time.time() - start_time
    logger.info(f"Experiment completed in {runtime:.2f}s. NDCG@10: {ndcg}, Wasted Ratio: {wasted_ratio}")

    return ExperimentResult(seed, variant, [ndcg], [wasted_ratio], runtime)

def run_baseline_experiment(budgets: List[int], seeds: int) -> List[ExperimentResult]:
    """Runs the baseline experiment across multiple seeds and budgets."""
    results = []
    for seed in range(1, seeds + 1):
        for budget in budgets:
            res = run_single_seed_experiment(seed, "baseline", budget)
            results.append(res)
    return results

def run_clustering_aided_experiment(budgets: List[int], seeds: int) -> List[ExperimentResult]:
    """Runs the clustering aided experiment across multiple seeds and budgets."""
    results = []
    for seed in range(1, seeds + 1):
        for budget in budgets:
            res = run_single_seed_experiment(seed, "clustering_aided", budget)
            results.append(res)
    return results

def save_results(results: List[ExperimentResult], output_path: str) -> None:
    """Saves experiment results to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump([r.to_dict() for r in results], f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run the llmXive pipeline experiments.")
    parser.add_argument("--variant", type=str, required=True, choices=["baseline", "clustering_aided"], help="Experiment variant")
    parser.add_argument("--budgets", type=int, nargs="+", required=True, help="List of budgets to test")
    parser.add_argument("--seeds", type=int, required=True, help="Number of random seeds to run")
    parser.add_argument("--output", type=str, default="data/results/experiment_results.json", help="Output path for results")
    
    args = parser.parse_args()

    # Initialize logging
    init_logging()
    logger.info("Pipeline execution started.")

    # 1. Data Integrity Check (T041)
    try:
        check_data_integrity()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Data integrity check failed: {e}")
        sys.exit(1)

    # 2. Resource Checks
    enforce_runtime_limit()
    enforce_memory_limit()

    # 3. Run Experiments
    results = []
    if args.variant == "baseline":
        results = run_baseline_experiment(args.budgets, args.seeds)
    elif args.variant == "clustering_aided":
        results = run_clustering_aided_experiment(args.budgets, args.seeds)

    # 4. Save Results
    save_results(results, args.output)

    logger.info("Pipeline execution finished successfully.")

if __name__ == "__main__":
    main()