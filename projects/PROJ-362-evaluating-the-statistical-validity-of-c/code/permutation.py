"""
Permutation test engine for evaluating statistical validity of ranking metrics.
Implements batch processing to handle memory limits.
"""
import logging
import random
import time
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import os

import numpy as np

from config import SEED, PERMUTATION_N, RESULTS_DIR, ensure_dirs, MEMORY_THRESHOLD_GB
from metrics import ndcg_at_k, average_precision
from data_loader import load_trec_robust04, load_trec_web_data
from null_distribution_saver import save_null_distribution_csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('permutation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def shuffle_relevance_labels(relevance_labels: List[int], seed: int) -> List[int]:
    """
    Shuffle relevance labels for a permutation test.
    
    Args:
        relevance_labels: List of relevance scores for a query.
        seed: Random seed for reproducibility.
        
    Returns:
        Shuffled list of relevance labels.
    """
    random.seed(seed)
    shuffled = relevance_labels.copy()
    random.shuffle(shuffled)
    return shuffled

def compute_permuted_scores(
    query_id: int,
    doc_ids: List[int],
    permuted_labels: List[int],
    metric_name: str,
    k: int = 10
) -> float:
    """
    Compute a ranking metric score for permuted labels.
    
    Args:
        query_id: Query identifier.
        doc_ids: List of document IDs.
        permuted_labels: Permuted relevance labels.
        metric_name: Metric to compute ('ndcg' or 'map').
        k: Cut-off rank (default 10 for NDCG@10).
        
    Returns:
        Computed metric score.
    """
    # Create a simple ranking based on doc_ids order (assumed sorted by rank)
    # In a real scenario, we'd have scores, but for permutation we shuffle labels
    # and compute metric on the shuffled labels assuming doc order is the ranking.
    
    # For NDCG@k and MAP, we need relevance labels in rank order
    if metric_name == 'ndcg':
        score = ndcg_at_k(permuted_labels, k=k)
    elif metric_name == 'map':
        score = average_precision(permuted_labels)
    else:
        raise ValueError(f"Unknown metric: {metric_name}")
    
    return score

def check_resource_limits() -> bool:
    """
    Check if current memory usage is within limits.
    
    Returns:
        True if within limits, False otherwise.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_gb = process.memory_info().rss / (1024 ** 3)
        if memory_gb > MEMORY_THRESHOLD_GB:
            logger.warning(f"Memory limit exceeded: {memory_gb:.2f} GB > {MEMORY_THRESHOLD_GB} GB")
            return False
        return True
    except ImportError:
        logger.warning("psutil not available, skipping memory check")
        return True

def run_permutation_test(
    query_id: int,
    doc_ids: List[int],
    relevance_labels: List[int],
    metric_name: str,
    n_permutations: int,
    seed: int,
    k: int = 10
) -> Tuple[List[float], int]:
    """
    Run permutation test for a single query.
    
    Args:
        query_id: Query identifier.
        doc_ids: List of document IDs.
        relevance_labels: Original relevance labels.
        metric_name: Metric to compute ('ndcg' or 'map').
        n_permutations: Number of permutations to run.
        seed: Base seed for reproducibility.
        k: Cut-off rank.
        
    Returns:
        Tuple of (null_distribution_scores, actual_permutations_executed).
    """
    null_scores = []
    actual_count = 0
    
    for i in range(n_permutations):
        # Check resource limits periodically
        if i % 100 == 0 and not check_resource_limits():
            logger.warning(f"Stopping permutation test for query {query_id} at {i} permutations due to resource limits")
            break
        
        # Create a unique seed for this permutation
        perm_seed = seed + i
        
        # Shuffle labels
        shuffled_labels = shuffle_relevance_labels(relevance_labels, perm_seed)
        
        # Compute score
        score = compute_permuted_scores(query_id, doc_ids, shuffled_labels, metric_name, k)
        null_scores.append(score)
        actual_count += 1
    
    logger.info(f"Query {query_id}: Executed {actual_count} permutations for {metric_name}")
    return null_scores, actual_count

def save_null_distribution(
    query_id: int,
    metric_name: str,
    scores: List[float],
    output_dir: Path
):
    """
    Save null distribution for a single query and metric.
    
    Args:
        query_id: Query identifier.
        metric_name: Metric name.
        scores: List of permuted scores.
        output_dir: Output directory.
    """
    filename = f"query_{query_id}_{metric_name}.csv"
    filepath = output_dir / filename
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['query_id', 'metric', 'score'])
        for score in scores:
            writer.writerow([query_id, metric_name, score])
    
    logger.info(f"Saved null distribution for query {query_id}, metric {metric_name} to {filepath}")

def run_batch_permutation_test(
    queries: List[Dict[str, Any]],
    metric_names: List[str],
    n_permutations: int,
    seed: int,
    batch_size: int = 10,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run permutation tests on a batch of queries with memory management.
    
    Args:
        queries: List of query dictionaries with 'query_id', 'doc_ids', 'relevance_labels'.
        metric_names: List of metrics to compute (e.g., ['ndcg', 'map']).
        n_permutations: Number of permutations per query.
        seed: Base seed for reproducibility.
        batch_size: Number of queries to process in each batch.
        output_dir: Directory to save null distributions.
        
    Returns:
        Dictionary with batch results and statistics.
    """
    if output_dir is None:
        output_dir = Path(RESULTS_DIR) / 'null_distributions'
    
    ensure_dirs(output_dir)
    
    total_queries = len(queries)
    results = {
        'total_queries': total_queries,
        'batches_processed': 0,
        'queries_processed': 0,
        'permutations_executed': 0,
        'metrics': metric_names,
        'permutation_count': n_permutations
    }
    
    # Process in batches
    for batch_start in range(0, total_queries, batch_size):
        batch_end = min(batch_start + batch_size, total_queries)
        batch_queries = queries[batch_start:batch_end]
        
        logger.info(f"Processing batch {batch_start // batch_size + 1}: queries {batch_start} to {batch_end - 1}")
        
        batch_results = []
        batch_permutations = 0
        
        for query_data in batch_queries:
            query_id = query_data['query_id']
            doc_ids = query_data['doc_ids']
            relevance_labels = query_data['relevance_labels']
            
            # Skip queries with zero relevance (trivial case)
            if sum(relevance_labels) == 0:
                logger.warning(f"Skipping query {query_id}: all relevance labels are zero")
                continue
            
            query_results = {'query_id': query_id, 'metrics': {}}
            
            for metric_name in metric_names:
                # Run permutation test
                null_scores, actual_count = run_permutation_test(
                    query_id, doc_ids, relevance_labels, metric_name,
                    n_permutations, seed
                )
                
                query_results['metrics'][metric_name] = {
                    'null_scores': null_scores,
                    'actual_permutations': actual_count
                }
                
                # Save null distribution
                save_null_distribution(query_id, metric_name, null_scores, output_dir)
                
                batch_permutations += actual_count
            
            batch_results.append(query_results)
            results['queries_processed'] += 1
        
        results['batches_processed'] += 1
        results['permutations_executed'] += batch_permutations
        
        # Log batch progress
        logger.info(f"Batch {batch_start // batch_size + 1} complete: {len(batch_queries)} queries, {batch_permutations} permutations")
        
        # Check memory after each batch
        if not check_resource_limits():
            logger.warning("Memory limit reached, stopping batch processing")
            break
        
        # Small delay to allow system to reclaim memory
        time.sleep(0.1)
    
    logger.info(f"Batch processing complete. Processed {results['queries_processed']} queries in {results['batches_processed']} batches.")
    logger.info(f"Total permutations executed: {results['permutations_executed']}")
    
    return results

def run_permutation_main():
    """
    Main entry point for running permutation tests.
    """
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Run permutation tests on TREC data')
    parser.add_argument('--dataset', type=str, default='robust04', 
                      choices=['robust04', 'web'],
                      help='Dataset to use')
    parser.add_argument('--n-permutations', type=int, default=PERMUTATION_N,
                      help='Number of permutations per query')
    parser.add_argument('--batch-size', type=int, default=10,
                      help='Number of queries to process in each batch')
    parser.add_argument('--seed', type=int, default=SEED,
                      help='Random seed for reproducibility')
    parser.add_argument('--metrics', type=str, nargs='+', default=['ndcg', 'map'],
                      help='Metrics to compute')
    parser.add_argument('--limit-queries', type=int, default=None,
                      help='Limit to first N queries (for testing)')
    
    args = parser.parse_args()
    
    logger.info(f"Starting permutation test with {args.n_permutations} permutations")
    logger.info(f"Dataset: {args.dataset}, Batch size: {args.batch_size}")
    logger.info(f"Metrics: {args.metrics}, Seed: {args.seed}")
    
    # Load data
    if args.dataset == 'robust04':
        queries = load_trec_robust04()
    else:
        queries = load_trec_web_data()
    
    if args.limit_queries:
        queries = queries[:args.limit_queries]
        logger.info(f"Limiting to first {args.limit_queries} queries")
    
    logger.info(f"Loaded {len(queries)} queries")
    
    # Run batch permutation test
    results = run_batch_permutation_test(
        queries=queries,
        metric_names=args.metrics,
        n_permutations=args.n_permutations,
        seed=args.seed,
        batch_size=args.batch_size
    )
    
    # Save results summary
    summary_path = Path(RESULTS_DIR) / 'permutation_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved summary to {summary_path}")
    return results

if __name__ == '__main__':
    run_permutation_main()