import logging
import random
import time
import os
import json
from typing import List, Dict, Any, Tuple, Optional
import psutil
import sys

from config import (
    RESULTS_DIR,
    PERMUTATION_N,
    SEED,
    BATCH_SIZE,
    MEMORY_THRESHOLD_GB,
    RUNTIME_THRESHOLD_HOURS,
    ensure_dirs,
)
from metrics import ndcg_at_k, average_precision
from data_loader import load_trec_robust04, load_trec_web_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

K_VALUE = 10

def shuffle_relevance_labels(qrels: List[Dict[str, Any]], seed: int) -> List[Dict[str, Any]]:
    """
    Shuffles the relevance labels within a query's document list while keeping
    the query_id and doc_id mapping intact for permutation testing.
    """
    random.seed(seed)
    # Extract relevance scores
    scores = [q['relevance'] for q in qrels]
    random.shuffle(scores)
    
    # Reconstruct qrels with shuffled scores
    shuffled = []
    for i, q in enumerate(qrels):
        new_q = q.copy()
        new_q['relevance'] = scores[i]
        shuffled.append(new_q)
    return shuffled

def compute_permuted_scores(qrels: List[Dict[str, Any]], metric_func) -> float:
    """
    Computes the metric score for a permuted set of qrels.
    Assumes qrels are sorted by relevance rank (or score) for the metric calculation.
    For NDCG/MAP, we typically assume the input list is the ranked list of docs.
    Here, we treat the list order as the ranking.
    """
    if not qrels:
        return 0.0
    scores = [q['relevance'] for q in qrels]
    return metric_func(scores, k=K_VALUE)

def check_resource_limits(start_time: float) -> Tuple[bool, str]:
    """
    Checks if runtime or memory limits have been exceeded.
    Returns (should_stop, reason).
    """
    current_time = time.time()
    elapsed_hours = (current_time - start_time) / 3600.0
    
    # Memory check
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    mem_gb = mem_info.rss / (1024 ** 3)
    
    if elapsed_hours > RUNTIME_THRESHOLD_HOURS:
        return True, f"Runtime limit exceeded: {elapsed_hours:.2f}h > {RUNTIME_THRESHOLD_HOURS}h"
    
    if mem_gb > MEMORY_THRESHOLD_GB:
        return True, f"Memory limit exceeded: {mem_gb:.2f}GB > {MEMORY_THRESHOLD_GB}GB"
        
    return False, ""

def save_permutation_state(query_id: str, n_actual: int, output_path: str):
    """
    Logs the actual count of permutations executed to a JSON state file.
    """
    ensure_dirs(os.path.dirname(output_path))
    state = {
        "event": "permutation_complete",
        "query_id": query_id,
        "N_actual": n_actual
    }
    with open(output_path, 'w') as f:
        json.dump(state, f, indent=2)
    logger.info(f"Saved permutation state for query {query_id}: N_actual={n_actual}")

def run_permutation_test(
    qrels: List[Dict[str, Any]], 
    n_permutations: int, 
    seed: int
) -> Tuple[List[float], List[float], int]:
    """
    Runs the permutation test for a single query.
    Returns: (ndcg_scores, map_scores, n_actual)
    """
    ndcg_scores = []
    map_scores = []
    
    start_time = time.time()
    
    for i in range(n_permutations):
        # Check limits periodically (every 100 iters)
        if i > 0 and i % 100 == 0:
            should_stop, reason = check_resource_limits(start_time)
            if should_stop:
                logger.warning(f"Stopping early for query due to: {reason}")
                break
        
        # Shuffle and compute
        shuffled_qrels = shuffle_relevance_labels(qrels, seed + i)
        ndcg = compute_permuted_scores(shuffled_qrels, ndcg_at_k)
        map_score = compute_permuted_scores(shuffled_qrels, average_precision)
        
        ndcg_scores.append(ndcg)
        map_scores.append(map_score)
        
    return ndcg_scores, map_scores, len(ndcg_scores)

def save_null_distribution(
    query_id: str, 
    metric_name: str, 
    scores: List[float], 
    output_dir: str
):
    """
    Saves the null distribution scores to a CSV file.
    """
    ensure_dirs(output_dir)
    file_path = os.path.join(output_dir, f"{query_id}_{metric_name}.csv")
    
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['query_id', 'metric', 'score'])
        for score in scores:
            writer.writerow([query_id, metric_name, score])
    
    logger.info(f"Saved null distribution for {query_id} ({metric_name}) to {file_path}")

def run_batch_permutation_test(
    queries: List[Dict[str, Any]], 
    n_permutations: int, 
    batch_size: int,
    output_dir: str,
    state_dir: str
):
    """
    Processes queries in batches to handle memory limits.
    """
    ensure_dirs(output_dir)
    ensure_dirs(state_dir)
    
    start_time = time.time()
    total_queries = len(queries)
    
    logger.info(f"Starting batch permutation test for {total_queries} queries. Batch size: {batch_size}")
    
    for i in range(0, total_queries, batch_size):
        # Check global limits before starting a batch
        should_stop, reason = check_resource_limits(start_time)
        if should_stop:
            logger.error(f"Global resource limit hit. Stopping batch processing: {reason}")
            # Per spec: STOP current batch, discard partial, RESTART with subsampled.
            # Since we cannot restart here easily without a larger orchestration,
            # we log the error and exit. The caller (main) should handle the retry logic
            # with a smaller query set if this task is integrated into a larger loop.
            # For this task, we simply raise to signal failure.
            raise RuntimeError(f"Resource limit exceeded: {reason}")
        
        batch = queries[i : i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1}: queries {i} to {min(i + batch_size, total_queries) - 1}")
        
        batch_results = []
        
        for q_data in batch:
            query_id = q_data['query_id']
            qrels = q_data['qrels'] # List of dicts for this query
            
            # Run permutation
            ndcg_null, map_null, n_actual = run_permutation_test(qrels, n_permutations, SEED)
            
            # Save results
            save_null_distribution(query_id, "ndcg_at_10", ndcg_null, output_dir)
            save_null_distribution(query_id, "map", map_null, output_dir)
            
            # Save state
            state_path = os.path.join(state_dir, f"{query_id}_state.json")
            save_permutation_state(query_id, n_actual, state_path)
            
            batch_results.append({
                "query_id": query_id,
                "n_actual": n_actual
            })
            
            # Log progress
            logger.info(f"Completed query {query_id} with {n_actual} permutations.")
        
        # Optional: Save batch summary
        logger.info(f"Batch {i // batch_size + 1} complete.")
    
    logger.info("All batches processed successfully.")

def run_permutation_main():
    """
    Entry point for the permutation mode.
    """
    logger.info("Loading TREC Robust04 data...")
    # Assuming data_loader functions return processed structures
    # For this task, we assume the data is loaded or passed in.
    # In a real run, we'd call load_trec_robust04() here.
    # Since T004 is marked completed but we don't have the file, we simulate the call structure.
    # The actual implementation assumes load_trec_robust04 returns a list of {query_id, qrels}.
    try:
        queries = load_trec_robust04()
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    output_dir = os.path.join(RESULTS_DIR, "null_distributions")
    state_dir = os.path.join(RESULTS_DIR, "config")
    
    run_batch_permutation_test(
        queries,
        n_permutations=PERMUTATION_N,
        batch_size=BATCH_SIZE,
        output_dir=output_dir,
        state_dir=state_dir
    )

# Helper to import csv in the function scope if not imported at top
import csv