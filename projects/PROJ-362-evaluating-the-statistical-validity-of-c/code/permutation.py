"""
Core permutation engine for statistical validity evaluation.

Implements shuffling of relevance labels N times per query to generate
null distributions for ranking metrics (NDCG@10, MAP).
"""

import logging
import random
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import os

from metrics import ndcg_at_k, average_precision
from config import PERMUTATION_COUNT, SEED, RESULTS_DIR, DATA_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def shuffle_relevance_labels(relevance_labels: List[int], seed: Optional[int] = None) -> List[int]:
    """
    Shuffle relevance labels in place (or return a new shuffled list).

    Args:
        relevance_labels: List of relevance scores (integers).
        seed: Optional seed for reproducibility.

    Returns:
        A new list with shuffled relevance labels.
    """
    if seed is not None:
        local_random = random.Random(seed)
        shuffled = relevance_labels.copy()
        local_random.shuffle(shuffled)
        return shuffled
    else:
        shuffled = relevance_labels.copy()
        random.shuffle(shuffled)
        return shuffled


def compute_permuted_scores(
    query_id: int,
    relevance_labels: List[int],
    metric_func,
    num_permutations: int,
    seed: Optional[int] = None
) -> Tuple[List[float], int]:
    """
    Compute metric scores for permuted relevance labels.

    Args:
        query_id: The query identifier (for logging).
        relevance_labels: Original relevance labels for the query.
        metric_func: Function to compute the metric (e.g., ndcg_at_k, average_precision).
        num_permutations: Number of permutations to perform.
        seed: Base seed for permutation generation.

    Returns:
        Tuple of (list of permuted scores, actual count of permutations executed).
    """
    permuted_scores = []
    actual_count = 0

    # Use a local random instance if seed is provided to ensure reproducibility
    rng = random.Random(seed) if seed is not None else random

    for i in range(num_permutations):
        # Generate a deterministic seed for this specific permutation
        perm_seed = rng.randint(0, 2**32 - 1)
        
        try:
            # Shuffle the labels
            shuffled_labels = shuffle_relevance_labels(relevance_labels, seed=perm_seed)
            
            # Compute the metric on shuffled labels
            # Note: For NDCG@k, we assume the document scores/rankings are fixed,
            # and we are permuting the relevance labels to see the distribution
            # under the null hypothesis that relevance is independent of ranking.
            score = metric_func(shuffled_labels)
            permuted_scores.append(score)
            actual_count += 1
        except Exception as e:
            logger.warning(f"Query {query_id}, Permutation {i}: Failed to compute score: {e}")
            # Continue to next permutation rather than failing the whole batch

    logger.info(f"Query {query_id}: Executed {actual_count} / {num_permutations} permutations successfully.")
    return permuted_scores, actual_count


def run_permutation_test(
    query_id: int,
    relevance_labels: List[int],
    metric_name: str,
    num_permutations: int = PERMUTATION_COUNT,
    seed: Optional[int] = SEED
) -> Dict[str, Any]:
    """
    Run a full permutation test for a single query and a specific metric.

    Args:
        query_id: The query identifier.
        relevance_labels: List of relevance scores for the documents in the query.
        metric_name: Name of the metric ('ndcg@10' or 'map').
        num_permutations: Number of permutations (default from config).
        seed: Base seed for reproducibility.

    Returns:
        Dictionary containing:
            - query_id: int
            - metric: str
            - null_distribution: List[float]
            - N_actual: int (actual number of permutations executed)
    """
    # Select metric function
    if metric_name == 'ndcg@10':
        metric_func = lambda labels: ndcg_at_k(labels, k=10)
    elif metric_name == 'map':
        # MAP requires a list of relevance labels for all docs in the ranking
        # average_precision function handles the list directly
        metric_func = average_precision
    else:
        raise ValueError(f"Unsupported metric: {metric_name}. Use 'ndcg@10' or 'map'.")

    logger.info(f"Starting permutation test for Query {query_id}, Metric: {metric_name}, N_target: {num_permutations}")

    scores, n_actual = compute_permuted_scores(
        query_id,
        relevance_labels,
        metric_func,
        num_permutations,
        seed
    )

    result = {
        'query_id': query_id,
        'metric': metric_name,
        'null_distribution': scores,
        'N_actual': n_actual
    }

    logger.info(f"Completed permutation test for Query {query_id}, Metric: {metric_name}. N_actual: {n_actual}")
    return result


def run_batch_permutation_test(
    queries_data: List[Dict[str, Any]],
    metrics: List[str],
    num_permutations: int = PERMUTATION_COUNT,
    seed: Optional[int] = SEED,
    output_dir: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Run permutation tests for a batch of queries and multiple metrics.

    Args:
        queries_data: List of dicts with 'query_id' and 'relevance_labels'.
        metrics: List of metric names to test (e.g., ['ndcg@10', 'map']).
        num_permutations: Number of permutations per query/metric.
        seed: Base seed.
        output_dir: Directory to save results (if provided).

    Returns:
        List of result dictionaries for each query/metric pair.
    """
    if output_dir is None:
        output_dir = str(Path(RESULTS_DIR) / "null_distributions")
    
    os.makedirs(output_dir, exist_ok=True)

    all_results = []
    total_tasks = len(queries_data) * len(metrics)
    completed = 0

    logger.info(f"Starting batch permutation test: {len(queries_data)} queries x {len(metrics)} metrics = {total_tasks} tasks.")

    for query_data in queries_data:
        query_id = query_data['query_id']
        relevance_labels = query_data['relevance_labels']

        for metric in metrics:
            completed += 1
            logger.info(f"Progress: {completed}/{total_tasks} - Query {query_id}, Metric {metric}")
            
            result = run_permutation_test(
                query_id=query_id,
                relevance_labels=relevance_labels,
                metric_name=metric,
                num_permutations=num_permutations,
                seed=seed
            )
            all_results.append(result)

            # Optional: Save individual null distribution immediately to avoid memory buildup
            # The saver module can handle the actual CSV writing, but we ensure the data is ready
            # For now, we just collect. The main.py or a saver module will write to CSV.
    
    logger.info(f"Batch permutation test complete. Total results: {len(all_results)}")
    return all_results

def run_permutation_main():
    """
    Entry point for running permutation tests via CLI or script execution.
    This function is intended to be called by main.py or run directly for testing.
    """
    # This is a placeholder for direct execution logic if needed.
    # In the actual pipeline, main.py orchestrates the data loading and calls run_batch_permutation_test.
    logger.info("Permutation module loaded. Use run_batch_permutation_test for execution.")

if __name__ == "__main__":
    run_permutation_main()
