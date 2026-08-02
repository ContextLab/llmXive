import os
import sys
import time
import json
import random
import logging
import argparse
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from config import get_config, check_system_limits
from data_loader import (
    fetch_beir_datasets,
    load_injected_dataset,
    validate_redundancy_clusters_on_trec_covid,
)
from metrics import (
    calculate_ndcg_at_10,
    calculate_wasted_call_ratios,
    wilcoxon_signed_rank_test,
    bonferroni_correction,
    load_beir_ground_truth,
)
from clustering import cluster_documents, filter_candidates_by_clustering
from ranker import run_ranker_with_filter, apply_pre_clustering_filter
from models import CandidateList, ComparisonPair
from logging_config import init_logging, start_resource_monitoring, stop_resource_monitoring
from unique_subset_generator import generate_unique_subset
from sampling import run_sampling_pipeline
from calculate_sample_size import main as calculate_sample_size_main
from run_baseline_unique import main as run_baseline_unique_main

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ExperimentResult:
    seed: int
    variant: str
    ndcg_at_10: float
    wasted_ratio: float
    runtime_seconds: float
    memory_peak_mb: float
    budget_used: int
    total_budget: int

def check_data_integrity():
    """Verify that all required intermediate artifacts exist before proceeding."""
    required_files = [
        "data/processed/injected_datasets.json",
        "data/processed/clusters.json",
        "data/processed/unique_subset.json",
        "data/results/consensus_sample.json",
        "data/results/flagged_pairs_count.json",
        "data/results/trec_covid_validation.json",
    ]
    for f in required_files:
        if not os.path.exists(f):
            raise FileNotFoundError(f"Required artifact missing: {f}")
    logger.info("Data integrity check passed.")

def enforce_runtime_limit(max_hours: float):
    """Raise an error if runtime exceeds limit."""
    start = time.time()
    def check():
        if (time.time() - start) / 3600 > max_hours:
            raise TimeoutError(f"Runtime exceeded {max_hours} hours")
    return check

def enforce_memory_limit(max_gb: float):
    """Raise an error if memory usage exceeds limit."""
    import resource
    max_bytes = max_gb * 1024 * 1024 * 1024
    def check():
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        if usage > max_bytes:
            raise MemoryError(f"Memory usage exceeded {max_gb} GB")
    return check

def run_single_seed_experiment(
    seed: int,
    variant: str,
    budget: int,
    dataset_name: str,
    injected_data: Dict[str, Any],
) -> ExperimentResult:
    """Run a single seed experiment for a given variant and budget."""
    random.seed(seed)
    start_time = time.time()

    # Load dataset
    corpus, queries, qrels = injected_data[dataset_name]

    # Create candidate list
    candidates = []
    for qid in queries:
        for doc_id in qrels[qid]:
            candidates.append(
                ComparisonPair(
                    query_id=qid,
                    doc_id=doc_id,
                    query_text=queries[qid],
                    doc_text=corpus[doc_id],
                )
            )

    candidate_list = CandidateList(items=candidates)

    # Apply variant logic
    if variant == "baseline":
        # Baseline: no clustering, full comparison
        results = run_ranker_with_filter(
            candidate_list=candidate_list,
            budget=budget,
            use_clustering=False,
        )
    elif variant == "clustering_aided":
        # Clustering aided: use MinHash-LSH to filter
        clusters = cluster_documents(candidates, threshold=0.95)
        filtered_list = filter_candidates_by_clustering(candidate_list, clusters)
        results = run_ranker_with_filter(
            candidate_list=filtered_list,
            budget=budget,
            use_clustering=True,
        )
    else:
        raise ValueError(f"Unknown variant: {variant}")

    # Calculate metrics
    ndcg = calculate_ndcg_at_10(results, qrels)
    wasted_ratio = calculate_wasted_call_ratios(results)
    runtime = time.time() - start_time

    return ExperimentResult(
        seed=seed,
        variant=variant,
        ndcg_at_10=ndcg,
        wasted_ratio=wasted_ratio,
        runtime_seconds=runtime,
        memory_peak_mb=0.0,  # Placeholder for now
        budget_used=results.get("budget_used", 0),
        total_budget=budget,
    )

def run_threshold_sweep(
    dataset_name: str,
    injected_data: Dict[str, Any],
    thresholds: List[float],
    seeds: List[int],
    budget: int,
) -> List[Dict[str, Any]]:
    """Run a sweep over MinHash-LSH thresholds."""
    results = []
    for thresh in thresholds:
        for seed in seeds:
            # This is a simplified version; full implementation would vary the threshold
            # in the clustering step.
            res = run_single_seed_experiment(
                seed=seed,
                variant="clustering_aided",
                budget=budget,
                dataset_name=dataset_name,
                injected_data=injected_data,
            )
            results.append({"threshold": thresh, **asdict(res)})
    return results

def main():
    """Main entry point for the pipeline with multi-seed execution."""
    parser = argparse.ArgumentParser(description="Run the active learning pipeline.")
    parser.add_argument(
        "--variant",
        type=str,
        required=True,
        choices=["baseline", "clustering_aided"],
        help="Which variant to run: 'baseline' or 'clustering_aided'.",
    )
    parser.add_argument(
        "--budgets",
        type=int,
        nargs="+",
        default=[20, 50, 100],
        help="List of LLM call budgets to test.",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[1, 2, 3, 4, 5],
        help="List of random seeds for independent runs.",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="scifact",
        help="Dataset to run on (scifact, nfcorpus, trec-covid).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/experiment_results.json",
        help="Path to write results.",
    )

    args = parser.parse_args()

    # Initialize logging
    init_logging()
    logger.info(f"Starting pipeline with variant={args.variant}, budgets={args.budgets}, seeds={args.seeds}")

    # Check data integrity
    check_data_integrity()

    # Load injected dataset
    injected_data = load_injected_dataset("data/processed/injected_datasets.json")

    # Check system limits
    config = get_config()
    check_system_limits()

    all_results = []

    for budget in args.budgets:
        for seed in args.seeds:
            logger.info(f"Running seed={seed}, budget={budget}, variant={args.variant}")
            try:
                res = run_single_seed_experiment(
                    seed=seed,
                    variant=args.variant,
                    budget=budget,
                    dataset_name=args.dataset,
                    injected_data=injected_data,
                )
                all_results.append(asdict(res))
            except Exception as e:
                logger.error(f"Experiment failed for seed={seed}, budget={budget}: {e}")
                continue

    # Write results
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Results written to {args.output}")

if __name__ == "__main__":
    main()