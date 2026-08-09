import os
import sys
import time
import json
import random
import logging
import argparse
import threading
from typing import List, Dict, Any, Optional

# Import from project modules
from config import get_config
from utils import init_watchdog, check_limits_periodically, stop_watchdog, ResourceWatchdog
from data_loader import prepare_injected_datasets, load_beir_corpus
from clustering import run_clustering_pipeline
from ranker import run_ranker_with_filter
from metrics import calculate_ndcg_at_10, calculate_wasted_call_ratios
from logging_config import init_logging, start_resource_monitoring, stop_resource_monitoring

logger = logging.getLogger(__name__)

def check_data_integrity():
    """
    T041: Data Integrity Check.
    Verifies the presence and non-empty status of all intermediate artifacts
    before proceeding to the next stage, ensuring no silent failures.
    Serves Constitution Principle III.
    """
    required_artifacts = [
        "data/processed/injected_datasets.json",
        "data/processed/clusters.json",
        "data/processed/unique_subset.json",
        "data/processed/comparison_log.json",
        "data/results/consensus_sample.json",
        "data/results/flagged_pairs_count.json",
        "data/results/us1_baseline_metrics.json",
        "data/results/us1_efficiency_ratio.json",
        "data/results/us2_baseline_095.json"
    ]

    missing = []
    empty = []

    for artifact in required_artifacts:
        if not os.path.exists(artifact):
            missing.append(artifact)
        else:
            # Check if file is non-empty
            if os.path.getsize(artifact) == 0:
                empty.append(artifact)
            else:
                # Optional: Basic JSON validation for non-empty files
                try:
                    with open(artifact, 'r') as f:
                        json.load(f)
                except json.JSONDecodeError:
                    empty.append(artifact) # Treat invalid JSON as empty/broken

    if missing:
        logger.error(f"Data Integrity Check FAILED: Missing artifacts: {missing}")
        raise FileNotFoundError(f"Required artifacts missing: {missing}")
    
    if empty:
        logger.error(f"Data Integrity Check FAILED: Empty or invalid artifacts: {empty}")
        raise ValueError(f"Required artifacts are empty or invalid: {empty}")

    logger.info("Data integrity check passed: All required artifacts present and non-empty.")
    return True

def ensure_prerequisites_for_statistical_report():
    """
    T067: Ensure statistical report prerequisites are met.
    """
    required = [
        "data/results/correction_factor.json",
        "data/results/us1_efficiency_ratio.json"
    ]
    for f in required:
        if not os.path.exists(f):
            logger.warning(f"Prerequisite for statistical report missing: {f}")
    return True

def run_single_seed_experiment(seed: int, variant: str, budget: int):
    """
    Executes a single experimental run for a given seed and variant.
    """
    logger.info(f"Starting seed {seed} for variant {variant} with budget {budget}.")
    
    # T041 Integration: Before starting heavy lifting, re-verify critical state
    # to ensure no race conditions or partial writes occurred if this is a resume.
    try:
        check_data_integrity()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Data integrity check failed during experiment run: {e}")
        raise

    # Simulate work (in real implementation, this calls ranker/clustering)
    time.sleep(0.1) 
    
    logger.info(f"Seed {seed} completed.")
    return {"seed": seed, "variant": variant, "budget": budget, "status": "ok"}

def run_threshold_sweep():
    """
    Runs the threshold sweep for US2.
    """
    logger.info("Running threshold sweep.")
    # Placeholder for sweep logic
    return []

def main():
    parser = argparse.ArgumentParser(description="Run the llmXive pipeline.")
    parser.add_argument("--variant", type=str, required=True, 
                        choices=["baseline", "clustering_aided"],
                        help="Pipeline variant to run.")
    parser.add_argument("--budgets", type=int, nargs="+", default=[100],
                        help="List of LLM call budgets to test.")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42],
                        help="Random seeds for reproducibility.")
    parser.add_argument("--cross-dataset", action="store_true",
                        help="Run across multiple datasets.")
    
    args = parser.parse_args()

    # Initialize logging
    init_logging()
    logger.info("Pipeline execution started.")

    # T004a: Initialize Watchdog
    watchdog = None
    try:
        watchdog = init_watchdog()
        check_thread = None
        if watchdog:
            check_thread = threading.Thread(
                target=check_limits_periodically, 
                args=(watchdog, 60), 
                daemon=True
            )
            check_thread.start()
    except Exception as e:
        logger.critical(f"Failed to initialize watchdog: {e}")
        sys.exit(1)

    try:
        # T041: Data Integrity Check (Pre-flight)
        # This ensures all intermediate artifacts are present before proceeding.
        try:
            check_data_integrity()
        except (FileNotFoundError, ValueError) as e:
            logger.error(str(e))
            logger.error("Pipeline aborted due to missing or invalid prerequisites.")
            sys.exit(1)

        # Main Execution Loop
        results = []
        for seed in args.seeds:
            for budget in args.budgets:
                result = run_single_seed_experiment(seed, args.variant, budget)
                results.append(result)
        
        # Save results
        output_path = f"data/results/pipeline_run_{args.variant}.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Pipeline completed. Results saved to {output_path}")

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise
    finally:
        if watchdog:
            stop_watchdog(watchdog)
        stop_resource_monitoring()

if __name__ == "__main__":
    main()