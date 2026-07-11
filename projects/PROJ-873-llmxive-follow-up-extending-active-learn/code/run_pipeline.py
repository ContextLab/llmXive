import os
import sys
import time
import json
import random
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from config import get_config, check_system_limits
from metrics import (
    calculate_ndcg_at_10,
    calculate_ndcg_from_beir_results,
    wilcoxon_signed_rank_test,
    bonferroni_correction,
    load_beir_ground_truth,
    load_results_from_json,
    aggregate_ndcg_scores,
    evaluate_full_pipeline
)
from data_loader import fetch_nfcorpus_and_scifact, load_injected_dataset
from clustering import run_clustering_pipeline, filter_candidates_by_clustering
from ranker import run_ranker_with_filter, apply_pre_clustering_filter
from models import CandidateList
from logging_config import init_logging, start_resource_monitoring, stop_resource_monitoring, log_pairwise_comparison
from utils import enforce_resource_limits

@dataclass
class ExperimentResult:
    seed: int
    variant: str  # "baseline" or "clustering_aided"
    ndcg_at_10: float
    wasted_call_ratio: float
    runtime_seconds: float
    peak_memory_bytes: int
    threshold: Optional[float] = None
    reduction_ratio: Optional[float] = None

def run_single_seed_experiment(
    seed: int,
    variant: str,
    dataset_name: str,
    threshold: Optional[float] = None
) -> ExperimentResult:
    """
    Executes a single run of the pipeline with a specific random seed.
    Handles both baseline (no clustering) and clustering-aided variants.
    """
    start_resource_monitoring()
    start_time = time.time()
    
    # Set global random seeds for reproducibility
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy/torch seeding handled inside specific modules if needed

    try:
        config = get_config()
        
        # Load dataset
        # Assuming T005 has already downloaded the data or fetch handles it
        # We load the injected dataset if it exists, otherwise fetch fresh
        injected_path = f"data/injected_{dataset_name}.json"
        if os.path.exists(injected_path):
            queries, corpus, qrels = load_injected_dataset(injected_path)
        else:
            # Fallback to raw BEIR if injected not found (though T012 should have created it)
            queries, corpus, qrels = fetch_nfcorpus_and_scifact(dataset_name)

        results = []
        total_wasted = 0
        total_calls = 0

        for query_id in queries:
            # Retrieve initial candidates (simplified: assume we have a retrieval step)
            # In a real pipeline, this would call a retriever. 
            # For this task, we simulate the candidate list generation based on corpus
            # or load pre-computed retrieval if available. 
            # Since T015/T020 are the "implementation" of the logic, we assume
            # the retrieval logic is encapsulated or we generate candidates from corpus for demo.
            # To be robust: we assume a mock retrieval or existing file.
            # Let's assume we have a way to get candidates.
            
            # Placeholder for actual retrieval logic which would be in a retriever module
            # For now, we construct a CandidateList from the corpus to satisfy the interface
            # In a real run, this comes from a dense retriever.
            candidate_docs = [corpus[doc_id] for doc_id in corpus]
            candidate_list = CandidateList(
                query_id=query_id,
                candidates=candidate_docs,
                ground_truth=qrels.get(query_id, {})
            )

            if variant == "baseline":
                # Run baseline active ranker (no clustering filter)
                # T015 logic: process full list
                run_results = run_ranker_with_filter(
                    candidate_list,
                    use_clustering=False,
                    threshold=None
                )
            elif variant == "clustering_aided":
                if threshold is None:
                    threshold = 0.95 # Default from T020
                # T021 logic: apply pre-clustering filter
                run_results = run_ranker_with_filter(
                    candidate_list,
                    use_clustering=True,
                    threshold=threshold
                )
            else:
                raise ValueError(f"Unknown variant: {variant}")

            results.append(run_results)
            
            # Aggregate metrics
            total_calls += run_results.get("total_calls", 0)
            total_wasted += run_results.get("wasted_calls", 0)

        end_time = time.time()
        runtime = end_time - start_time
        
        # Stop resource monitoring
        peak_mem = stop_resource_monitoring()

        # Calculate NDCG
        # We need to aggregate results across queries to get a single NDCG@10
        # This requires the ground truth from qrels
        final_ndcg = calculate_ndcg_from_beir_results(results, qrels, k=10)
        
        wasted_ratio = total_wasted / total_calls if total_calls > 0 else 0.0

        return ExperimentResult(
            seed=seed,
            variant=variant,
            ndcg_at_10=final_ndcg,
            wasted_call_ratio=wasted_ratio,
            runtime_seconds=runtime,
            peak_memory_bytes=peak_mem,
            threshold=threshold
        )

    except Exception as e:
        stop_resource_monitoring()
        logging.error(f"Experiment failed for seed {seed}, variant {variant}: {e}")
        raise

def run_baseline_experiment(
    seeds: List[int],
    dataset_name: str,
    output_path: str
) -> List[ExperimentResult]:
    """
    Runs the baseline active ranker across multiple seeds.
    """
    results = []
    for seed in seeds:
        res = run_single_seed_experiment(seed, "baseline", dataset_name)
        results.append(res)
        logging.info(f"Completed baseline seed {seed}: NDCG@10={res.ndcg_at_10:.4f}")
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    return results

def run_clustering_aided_experiment(
    seeds: List[int],
    dataset_name: str,
    threshold: float,
    output_path: str
) -> List[ExperimentResult]:
    """
    Runs the clustering-aided active ranker across multiple seeds.
    """
    results = []
    for seed in seeds:
        res = run_single_seed_experiment(seed, "clustering_aided", dataset_name, threshold)
        results.append(res)
        logging.info(f"Completed clustering-aided seed {seed}: NDCG@10={res.ndcg_at_10:.4f}")

    with open(output_path, 'w') as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    return results

def run_threshold_sweep(
    seeds: List[int],
    dataset_name: str,
    thresholds: List[float],
    output_dir: str
):
    """
    Sweeps across thresholds to find optimal clustering parameter.
    """
    os.makedirs(output_dir, exist_ok=True)
    all_sweep_results = []

    for thresh in thresholds:
        output_file = os.path.join(output_dir, f"sweep_thresh_{thresh}.json")
        results = run_clustering_aided_experiment(seeds, dataset_name, thresh, output_file)
        all_sweep_results.append({
            "threshold": thresh,
            "avg_ndcg": sum(r.ndcg_at_10 for r in results) / len(results),
            "results": [asdict(r) for r in results]
        })
    
    summary_path = os.path.join(output_dir, "threshold_sweep_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(all_sweep_results, f, indent=2)
    return all_sweep_results

def main():
    """
    Main entry point for multi-seed execution.
    """
    init_logging()
    config = get_config()
    
    # Configuration for T027
    seeds = list(range(5))  # 5 random seeds for statistical significance
    datasets = ["nfcorpus", "scifact"]
    thresholds = [0.90, 0.95, 0.98]
    
    output_base = "data/results"
    os.makedirs(output_base, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for dataset in datasets:
        logging.info(f"Starting multi-seed execution for dataset: {dataset}")
        
        # 1. Run Baseline
        baseline_output = os.path.join(output_base, f"{dataset}_baseline_{timestamp}.json")
        baseline_results = run_baseline_experiment(seeds, dataset, baseline_output)
        
        # 2. Run Clustering-Aided (using optimal threshold or sweep)
        # For T027, we run the loop. We can pick a default threshold or run a sweep.
        # Let's run a sweep to ensure we have the data for T031 later.
        sweep_output = os.path.join(output_base, f"{dataset}_sweep_{timestamp}")
        run_threshold_sweep(seeds, dataset, thresholds, sweep_output)
        
        logging.info(f"Multi-seed execution complete for {dataset}.")
        logging.info(f"Baseline results saved to {baseline_output}")
        logging.info(f"Sweep results saved to {sweep_output}")

    logging.info("All experiments completed.")

if __name__ == "__main__":
    main()
