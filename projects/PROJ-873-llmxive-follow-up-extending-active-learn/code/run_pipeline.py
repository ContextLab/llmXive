"""
Main pipeline orchestration script.
Enforces strict execution ordering: data generation -> clustering -> ranking.
"""
import os
import sys
import time
import json
import random
import logging
import argparse
from typing import List, Dict, Any, Optional

# Local imports matching API surface
from config import get_config, check_system_limits
from logging_config import init_logging, start_resource_monitoring, stop_resource_monitoring
from utils import PartialRunError
from data_loader import (
    prepare_injected_datasets,
    validate_redundancy_clusters_on_trec_covid,
    load_injected_dataset
)
from clustering import run_clustering_pipeline
from ranker import run_ranker_with_filter, apply_pre_clustering_filter
from metrics import (
    calculate_ndcg_at_10,
    calculate_wasted_call_ratios,
    calculate_dynamic_sample_size,
    aggregate_ndcg_scores
)
from sampling import run_sampling_pipeline
from cross_dataset_generalization import run_cross_dataset_generalization_check
from unique_subset_generator import generate_unique_subset

# Custom exception for dependency failures
class PipelineDependencyError(Exception):
    """Raised when a required prerequisite artifact is missing or incomplete."""
    pass

def check_data_integrity() -> None:
    """
    Validates that all prerequisite artifacts exist and are non-empty before proceeding.
    This enforces the 'Producer before consumer' rule (T057).
    """
    required_artifacts = [
        "data/processed/injected_datasets.json",
        "data/processed/clusters.json"
    ]

    missing = []
    empty = []

    for artifact_path in required_artifacts:
        if not os.path.exists(artifact_path):
            missing.append(artifact_path)
            continue

        # Check for non-empty
        if os.path.getsize(artifact_path) == 0:
            empty.append(artifact_path)
            continue

        # Optional: Basic JSON validity check
        try:
            with open(artifact_path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            raise PipelineDependencyError(f"Artifact {artifact_path} is not valid JSON: {e}")

    if missing:
        raise PipelineDependencyError(
            f"Required artifacts missing (run data generation/clustering first): {missing}"
        )

    if empty:
        raise PipelineDependencyError(
            f"Required artifacts are empty (data generation likely failed): {empty}"
        )

    logging.info("Data integrity check passed. All prerequisite artifacts present.")

def run_single_seed_experiment(
    variant: str,
    budget: int,
    seed: int,
    injected_data_path: str,
    clusters_path: str
) -> Dict[str, Any]:
    """
    Executes a single seed run for a specific variant (baseline or clustering_aided).
    """
    logging.info(f"Running seed {seed} for variant {variant} with budget {budget}")
    random.seed(seed)

    # Load data
    injected_data = load_injected_dataset(injected_data_path)
    
    # Determine candidate list
    if variant == "clustering_aided":
        # Apply pre-clustering filter
        logging.info("Applying pre-clustering filter...")
        candidates = apply_pre_clustering_filter(injected_data, clusters_path)
    else:
        # Baseline: use full injected dataset (or unique subset if T014 logic applies)
        # For this implementation, we use the full injected dataset as the baseline candidate pool
        candidates = injected_data

    # Run the ranker
    results = run_ranker_with_filter(
        candidates=candidates,
        budget=budget,
        variant=variant
    )

    # Calculate metrics
    ndcg = calculate_ndcg_at_10(results.get("ranked_docs", []))
    wasted_ratio = calculate_wasted_call_ratios(results.get("comparisons", []))

    return {
        "seed": seed,
        "variant": variant,
        "budget": budget,
        "ndcg_at_10": ndcg,
        "wasted_ratio": wasted_ratio,
        "total_comparisons": results.get("total_comparisons", 0),
        "time_elapsed": results.get("time_elapsed", 0)
    }

def run_threshold_sweep(
    injected_data_path: str,
    budget: int,
    seeds: List[int]
) -> Dict[str, Any]:
    """
    Runs the MinHash-LSH threshold sweep as per T025.
    """
    logging.info("Starting threshold sweep analysis...")
    # Implementation of sweep logic would go here
    # For T057, we ensure the pipeline structure is correct
    return {"status": "sweep_completed"}

def main():
    parser = argparse.ArgumentParser(description="Run the LLMXIVE Active Learning Pipeline")
    parser.add_argument(
        "--variant",
        type=str,
        required=True,
        choices=["baseline", "clustering_aided"],
        help="Variant to run: 'baseline' or 'clustering_aided'"
    )
    parser.add_argument(
        "--budgets",
        type=int,
        nargs="+",
        default=[20, 50, 100],
        help="List of LLM call budgets to test"
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[42],
        help="List of random seeds for reproducibility"
    )
    parser.add_argument(
        "--cross-dataset",
        action="store_true",
        help="Run cross-dataset generalization check"
    )

    args = parser.parse_args()

    # Initialize logging
    init_logging()
    logging.info("Pipeline started.")

    # Enforce system limits (T004a/T023)
    check_system_limits()
    start_resource_monitoring()

    try:
        # ------------------------------------------------------------------
        # T057: STRICT EXECUTION ORDERING ENFORCEMENT
        # Ensure prerequisites are fully written and validated BEFORE any ranking.
        # ------------------------------------------------------------------
        check_data_integrity()
        # ------------------------------------------------------------------

        # Load configuration
        config = get_config()
        injected_data_path = "data/processed/injected_datasets.json"
        clusters_path = "data/processed/clusters.json"

        # Run experiments
        all_results = []
        for budget in args.budgets:
            for seed in args.seeds:
                result = run_single_seed_experiment(
                    variant=args.variant,
                    budget=budget,
                    seed=seed,
                    injected_data_path=injected_data_path,
                    clusters_path=clusters_path
                )
                all_results.append(result)

        # Save aggregated results
        output_path = f"data/results/{args.variant}_results.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        logging.info(f"Results saved to {output_path}")

        # Optional: Cross-dataset check
        if args.cross_dataset:
            run_cross_dataset_generalization_check()

    except PipelineDependencyError as e:
        logging.error(f"Pipeline failed due to missing dependencies: {e}")
        sys.exit(1)
    except PartialRunError as e:
        logging.warning(f"Pipeline partially completed due to resource limits: {e}")
        sys.exit(2)
    except Exception as e:
        logging.error(f"Pipeline failed with unexpected error: {e}")
        raise
    finally:
        stop_resource_monitoring()

if __name__ == "__main__":
    main()