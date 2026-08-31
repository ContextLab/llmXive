import logging
import random
import time
import os
import json
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

import psutil

# Local imports matching the provided API surface
from config import (
    PERMUTATION_N,
    SEED,
    BATCH_SIZE,
    MEMORY_THRESHOLD_GB,
    RUNTIME_THRESHOLD_HOURS,
    DATA_RAW_PATH,
    RESULTS_PATH,
    ensure_dirs,
)
from metrics import ndcg_at_k, mean_average_precision
from data_loader import load_trec_robust04, load_trec_web_data, process_and_validate_qrels

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Ensure output directories exist
ensure_dirs()

# Global state tracking for batch processing
_batch_processing_state = {
    "start_time": None,
    "queries_processed": 0,
    "queries_skipped": 0,
    "queries_dropped": 0,
    "current_batch_queries": [],
    "should_stop": False,
}


def shuffle_relevance_labels(relevance_labels: List[int], seed: int) -> List[int]:
    """
    Shuffle the relevance labels for a single query.
    """
    shuffled = relevance_labels.copy()
    random.seed(seed)
    random.shuffle(shuffled)
    return shuffled


def compute_permuted_scores(shuffled_labels: List[int], metric_func) -> float:
    """
    Compute a metric score (NDCG@10 or MAP) for a single query with shuffled labels.
    """
    # For this specific implementation, we assume the metric function takes the relevance labels
    # and computes the score. In a real scenario, we might need document scores or a specific rank order.
    # Here we assume the labels are ordered by relevance rank or we are just scoring the distribution.
    # Given the context of permutation tests, we usually permute the labels against a fixed ranking.
    # However, without the specific ranking data structure in the prompt's API, we will compute
    # the metric on the shuffled labels directly as a proxy for the null distribution score.
    # NOTE: This assumes the input labels are already associated with a ranked list.
    if not shuffled_labels:
        return 0.0
    return metric_func(shuffled_labels)


def check_resource_limits() -> bool:
    """
    Check if runtime or memory limits have been exceeded.
    Returns True if limits are exceeded (should stop), False otherwise.
    """
    current_time = time.time()
    elapsed_hours = (current_time - _batch_processing_state["start_time"]) / 3600.0

    process = psutil.Process(os.getpid())
    memory_gb = process.memory_info().rss / (1024 ** 3)

    if elapsed_hours > RUNTIME_THRESHOLD_HOURS:
        logger.warning(
            f"Runtime threshold exceeded: {elapsed_hours:.2f} hours > {RUNTIME_THRESHOLD_HOURS} hours"
        )
        return True

    if memory_gb > MEMORY_THRESHOLD_GB:
        logger.warning(
            f"Memory threshold exceeded: {memory_gb:.2f} GB > {MEMORY_THRESHOLD_GB} GB"
        )
        return True

    return False


def save_permutation_state(query_id: str, n_actual: int, status: str) -> None:
    """
    Save the permutation state for a specific query to the JSON state file.
    """
    state_file = Path(RESULTS_PATH) / "config" / "permutation_state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing state if it exists
    if state_file.exists():
        with open(state_file, "r") as f:
            try:
                state_data = json.load(f)
            except json.JSONDecodeError:
                state_data = {}
    else:
        state_data = {}

    # Update state for the specific query
    state_data[query_id] = {
        "query_id": query_id,
        "N_actual": n_actual,
        "status": status,
    }

    with open(state_file, "w") as f:
        json.dump(state_data, f, indent=2)

    logger.info(
        f"Saved permutation state for query {query_id}: N_actual={n_actual}, status={status}"
    )


def run_permutation_test(
    query_id: str, relevance_labels: List[int], metric_func, n_permutations: int = PERMUTATION_N
) -> Tuple[List[float], List[float]]:
    """
    Run the permutation test for a single query.
    Returns a tuple of (null_scores, observed_scores) - actually just null_scores for now as observed is single.
    Returns (null_ndcg_scores, null_map_scores)
    """
    null_ndcg_scores = []
    null_map_scores = []

    # Check if relevance labels are empty (validation from T006)
    if not relevance_labels:
        logger.warning(f"Query {query_id} has empty relevance labels. Skipping.")
        save_permutation_state(query_id, 0, "skipped")
        _batch_processing_state["queries_skipped"] += 1
        return null_ndcg_scores, null_map_scores

    # Run permutations
    for i in range(n_permutations):
        seed = SEED + i
        shuffled_labels = shuffle_relevance_labels(relevance_labels, seed)
        ndcg_score = compute_permuted_scores(shuffled_labels, lambda x: ndcg_at_k(x, k=10))
        map_score = compute_permuted_scores(shuffled_labels, lambda x: mean_average_precision(x))

        null_ndcg_scores.append(ndcg_score)
        null_map_scores.append(map_score)

        # Log progress periodically
        if (i + 1) % 100 == 0:
            logger.debug(f"Query {query_id}: Completed {i + 1}/{n_permutations} permutations")

    save_permutation_state(query_id, n_permutations, "complete")
    return null_ndcg_scores, null_map_scores


def save_null_distribution(
    query_id: str, null_ndcg_scores: List[float], null_map_scores: List[float]
) -> None:
    """
    Save the null distribution scores for a query to a CSV file.
    """
    output_dir = Path(RESULTS_PATH) / "null_distributions"
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / f"query_{query_id}_null_distributions.csv"

    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["query_id", "metric", "score"])

        for score in null_ndcg_scores:
            writer.writerow([query_id, "ndcg_at_10", score])

        for score in null_map_scores:
            writer.writerow([query_id, "map", score])

    logger.info(f"Saved null distribution for query {query_id} to {file_path}")


def run_batch_permutation_test(
    queries_data: List[Dict[str, Any]],
    n_permutations: int = PERMUTATION_N,
    batch_size: int = BATCH_SIZE,
) -> None:
    """
    Process queries in batches to handle memory limits.
    """
    _batch_processing_state["start_time"] = time.time()
    _batch_processing_state["queries_processed"] = 0
    _batch_processing_state["queries_skipped"] = 0
    _batch_processing_state["queries_dropped"] = 0
    _batch_processing_state["should_stop"] = False

    total_queries = len(queries_data)
    logger.info(f"Starting batch permutation test for {total_queries} queries.")

    # Process queries in batches
    for i in range(0, total_queries, batch_size):
        if _batch_processing_state["should_stop"]:
            logger.warning("Stopping batch processing due to resource limits.")
            break

        batch_queries = queries_data[i : i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1}: {len(batch_queries)} queries")

        for query_data in batch_queries:
            query_id = query_data["query_id"]
            relevance_labels = query_data["relevance_labels"]

            # Check resource limits before processing each query
            if check_resource_limits():
                logger.warning(
                    f"Resource limits exceeded. Dropping query {query_id} and stopping batch."
                )
                _batch_processing_state["queries_dropped"] += 1
                _batch_processing_state["should_stop"] = True

                # Log dropped query to subsampling log
                subsampling_log = Path(RESULTS_PATH) / "subsampling_log.csv"
                with open(subsampling_log, "a", newline="") as f:
                    writer = csv.writer(f)
                    if not os.path.exists(subsampling_log) or os.path.getsize(subsampling_log) == 0:
                        writer.writerow(["query_id", "reason", "timestamp"])
                    writer.writerow([query_id, "resource_limit_exceeded", time.strftime("%Y-%m-%d %H:%M:%S")])

                continue

            # Run permutation test
            try:
                null_ndcg_scores, null_map_scores = run_permutation_test(
                    query_id, relevance_labels, None, n_permutations
                )

                # Save null distribution
                save_null_distribution(query_id, null_ndcg_scores, null_map_scores)

                _batch_processing_state["queries_processed"] += 1

            except Exception as e:
                logger.error(f"Error processing query {query_id}: {e}")
                # Continue with next query but log the error
                continue

        logger.info(
            f"Batch {i // batch_size + 1} completed. Processed: {_batch_processing_state['queries_processed']}, "
            f"Skipped: {_batch_processing_state['queries_skipped']}, Dropped: {_batch_processing_state['queries_dropped']}"
        )

    logger.info("Batch permutation test completed.")


def run_permutation_main() -> None:
    """
    Main entry point for the permutation test execution.
    Loads data and runs the batch permutation test.
    """
    # Load data (assuming TREC Robust 2004 for this example)
    # In a real scenario, we might load multiple datasets
    try:
        qrels_data = load_trec_robust04()
        logger.info(f"Loaded {len(qrels_data)} queries from TREC Robust 2004")
    except Exception as e:
        logger.error(f"Failed to load TREC Robust 2004 data: {e}")
        return

    # Run batch permutation test
    run_batch_permutation_test(qrels_data)


if __name__ == "__main__":
    run_permutation_main()