import os
import sys
import time
import json
import random
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_config, PipelineConfig
from logging_config import init_logging, start_resource_monitoring, stop_resource_monitoring
from utils import validate_artifact_chain, DataFlowViolationError, PartialRunError
from data_loader import prepare_injected_datasets, fetch_beir_datasets, download_beir_dataset
from clustering import run_clustering_pipeline
from ranker import run_ranker_with_filter, load_cluster_results
from metrics import calculate_ndcg_at_10, calculate_wasted_call_ratios, calculate_dynamic_sample_size
from sampling import run_sampling_pipeline
from verify_proxy_chain import run_t013e_consensus_validation, run_t013f_correction_factor, run_t013d_final_ratio
from generate_statistical_report import generate_markdown_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

# Artifact paths for integrity checks
ARTIFACT_CHAIN = [
    "data/processed/injected_datasets.json",
    "data/processed/clusters.json",
    "data/processed/unique_subset.json",
    "data/processed/comparison_log.json",
    "data/results/flagged_pairs_count.json",
    "data/results/consensus_sample.json",
    "data/results/consensus_ground_truth.json",
    "data/results/correction_factor.json",
    "data/results/us1_efficiency_ratio.json"
]

def check_data_integrity(required_artifacts: List[str]) -> bool:
    """
    T041: Data Integrity Check.
    Verifies the presence and non-empty status of all intermediate artifacts
    before proceeding to the next stage.
    """
    logger.info("Starting Data Integrity Check (T041)...")
    missing = []
    empty = []

    for artifact_path in required_artifacts:
        path = Path(artifact_path)
        if not path.exists():
            missing.append(artifact_path)
            continue
        
        # Check if file is non-empty
        if path.stat().st_size == 0:
            empty.append(artifact_path)
            continue

        # Optional: Validate JSON schema for critical files
        if artifact_path.endswith('.json'):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    if not data: # Check for empty dict/list
                        empty.append(artifact_path)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in {artifact_path}")
                empty.append(artifact_path)

    if missing:
        logger.error(f"Missing required artifacts: {missing}")
        return False
    
    if empty:
        logger.error(f"Empty or invalid artifacts: {empty}")
        return False

    logger.info("Data Integrity Check passed.")
    return True

def ensure_prerequisites_for_statistical_report():
    """
    Ensures all prerequisites for T031 (Statistical Report) are met.
    Specifically checks for T013d and T013f outputs.
    """
    required = [
        "data/results/correction_factor.json",
        "data/results/us1_efficiency_ratio.json"
    ]
    if not check_data_integrity(required):
        raise DataFlowViolationError("Prerequisites for statistical report missing.")
    return True

def run_single_seed_experiment(seed: int, variant: str, budgets: List[int]):
    """
    Executes the pipeline for a single seed and variant.
    """
    logger.info(f"Starting experiment for seed={seed}, variant={variant}")
    random.seed(seed)
    
    # 1. Prepare Data (T012/T043)
    logger.info("Step 1: Preparing injected datasets...")
    prepare_injected_datasets() # Writes data/processed/injected_datasets.json

    # 2. Integrity Check (T041) - Pre-Clustering
    if not check_data_integrity(["data/processed/injected_datasets.json"]):
        raise RuntimeError("Data integrity check failed before clustering.")

    # 3. Clustering (T020)
    if variant == "clustering_aided":
        logger.info("Step 2: Running clustering pipeline...")
        run_clustering_pipeline() # Writes data/processed/clusters.json

    # 4. Integrity Check (T041) - Pre-Ranking
    deps = ["data/processed/injected_datasets.json"]
    if variant == "clustering_aided":
        deps.append("data/processed/clusters.json")
    
    if not check_data_integrity(deps):
        raise RuntimeError("Data integrity check failed before ranking.")

    # 5. Unique Subset Generation (Implicit in T014/T021)
    logger.info("Step 3: Generating unique subset...")
    # This is typically called inside ranker or as a separate step, 
    # ensuring data/processed/unique_subset.json exists.
    # Assuming unique_subset_generator.py is invoked here or inside ranker logic.
    # For this task, we ensure the pipeline calls the generator.
    from unique_subset_generator import generate_unique_subset
    generate_unique_subset() 

    # 6. Ranking & Comparison (T014)
    logger.info("Step 4: Running ranker and logging comparisons...")
    # This generates data/processed/comparison_log.json and data/results/unique_subset.json
    # Note: run_ranker_with_filter handles the actual execution.
    # We must ensure it writes the log.
    load_cluster_results() # Helper to load if needed
    run_ranker_with_filter(variant, budgets, seed)

    # 7. Integrity Check (T041) - Pre-Sampling
    if not check_data_integrity(["data/processed/comparison_log.json"]):
        raise RuntimeError("Comparison log missing.")

    # 8. Sampling (T013c)
    logger.info("Step 5: Running sampling pipeline...")
    run_sampling_pipeline() # Writes data/results/consensus_sample.json

    # 9. Consensus Validation (T013e)
    logger.info("Step 6: Running consensus validation...")
    run_t013e_consensus_validation() # Writes data/results/consensus_ground_truth.json

    # 10. Correction Factor (T013f)
    logger.info("Step 7: Calculating correction factor...")
    run_t013f_correction_factor() # Writes data/results/correction_factor.json

    # 11. Final Ratio (T013d)
    logger.info("Step 8: Calculating final efficiency ratio...")
    run_t013d_final_ratio() # Writes data/results/us1_efficiency_ratio.json

    # 12. Baseline Metrics (T014/T016)
    logger.info("Step 9: Calculating baseline metrics...")
    # Assuming this logic is embedded or called here
    from run_baseline_unique import run_baseline_on_unique
    run_baseline_on_unique() # Writes data/results/us1_baseline_metrics.json

    # 13. Threshold Sweep (T025b) if applicable
    if variant == "clustering_aided":
        logger.info("Step 10: Running threshold sweep...")
        # Run sweep logic
        from validate_threshold_sweep import validate_sweep_completeness
        # ... (sweep execution logic)

    logger.info(f"Experiment completed for seed={seed}")

def run_threshold_sweep(seeds: List[int]):
    """
    Runs the threshold sweep for sensitivity analysis.
    """
    logger.info("Running threshold sweep...")
    # Implementation of T025b logic
    pass

def main():
    parser = argparse.ArgumentParser(description="llmXive Pipeline Runner")
    parser.add_argument("--variant", type=str, required=True, 
                        choices=["baseline", "clustering_aided"],
                        help="Pipeline variant to run")
    parser.add_argument("--budgets", type=int, nargs="+", default=[20, 50, 100],
                        help="List of LLM call budgets")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42],
                        help="List of random seeds")
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
        # Initial Integrity Check
        logger.info("Performing initial data integrity check...")
        if not check_data_integrity([]): # Start with empty, build up
            logger.warning("No initial artifacts found. Starting fresh.")

        # Run Experiments
        for seed in args.seeds:
            run_single_seed_experiment(seed, args.variant, args.budgets)

        # Cross-dataset check if requested
        if args.cross_dataset:
            logger.info("Running cross-dataset generalization check...")
            from cross_dataset_generalization import run_cross_dataset_generalization_check
            run_cross_dataset_generalization_check()

        # Statistical Report (T031)
        logger.info("Generating statistical report...")
        ensure_prerequisites_for_statistical_report()
        generate_markdown_report()

    except DataFlowViolationError as e:
        logger.error(f"Data flow violation: {e}")
        sys.exit(1)
    except PartialRunError as e:
        logger.warning(f"Partial run detected: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise
    finally:
        if watchdog:
            stop_watchdog(watchdog)
        stop_resource_monitoring()

if __name__ == "__main__":
    main()