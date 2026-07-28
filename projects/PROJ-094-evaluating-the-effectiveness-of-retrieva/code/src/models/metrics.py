"""
Metrics module for evaluating retrieval performance.

Calculates Precision@K, Recall@K, and nDCG@K against ground truth labels.
"""
import math
from typing import List, Dict, Any, Optional, Set

def precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Calculate Precision@K.

    Args:
        retrieved_ids: List of IDs of retrieved documents/snippets.
        relevant_ids: Set of IDs of ground truth relevant documents/snippets.
        k: The cutoff depth (e.g., 5, 10).

    Returns:
        Precision@K score (float between 0.0 and 1.0).
    """
    if k <= 0:
        return 0.0
    
    # Truncate retrieved list to k
    top_k_retrieved = retrieved_ids[:k]
    
    if not top_k_retrieved:
        return 0.0
    
    # Count relevant items in top_k
    relevant_count = sum(1 for doc_id in top_k_retrieved if doc_id in relevant_ids)
    
    return relevant_count / k

def recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Calculate Recall@K.

    Args:
        retrieved_ids: List of IDs of retrieved documents/snippets.
        relevant_ids: Set of IDs of ground truth relevant documents/snippets.
        k: The cutoff depth.

    Returns:
        Recall@K score (float between 0.0 and 1.0).
    """
    if not relevant_ids:
        return 0.0 if k <= 0 else 0.0
    
    # Truncate retrieved list to k
    top_k_retrieved = retrieved_ids[:k]
    
    if not top_k_retrieved:
        return 0.0
    
    # Count relevant items in top_k
    relevant_count = sum(1 for doc_id in top_k_retrieved if doc_id in relevant_ids)
    
    return relevant_count / len(relevant_ids)

def dcg_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Calculate Discounted Cumulative Gain (DCG)@K.
    
    Assumes binary relevance (1 if in relevant_ids, 0 otherwise).

    Args:
        retrieved_ids: List of IDs of retrieved documents/snippets.
        relevant_ids: Set of IDs of ground truth relevant documents/snippets.
        k: The cutoff depth.

    Returns:
        DCG@K score (float).
    """
    if k <= 0:
        return 0.0
    
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k]):
        # Relevance is 1 if the document is in the ground truth set, else 0
        rel = 1.0 if doc_id in relevant_ids else 0.0
        
        # Discount factor: log2(i + 2) where i is 0-indexed position
        # Position 0 -> log2(2), Position 1 -> log2(3), etc.
        discount = math.log2(i + 2)
        
        dcg += rel / discount
    
    return dcg

def ideal_dcg_at_k(relevant_ids: Set[str], k: int) -> float:
    """
    Calculate Ideal DCG (IDCG)@K.
    
    Assumes binary relevance. The ideal ranking places all relevant items
    at the top positions.

    Args:
        relevant_ids: Set of IDs of ground truth relevant documents/snippets.
        k: The cutoff depth.

    Returns:
        IDCG@K score (float).
    """
    if k <= 0:
        return 0.0
    
    num_relevant = len(relevant_ids)
    if num_relevant == 0:
        return 0.0
    
    # In the ideal case, we have min(num_relevant, k) relevant items at the top
    # each with relevance 1.0
    idcg = 0.0
    count = min(num_relevant, k)
    
    for i in range(count):
        discount = math.log2(i + 2)
        idcg += 1.0 / discount
    
    return idcg

def ndcg_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain (nDCG)@K.

    Args:
        retrieved_ids: List of IDs of retrieved documents/snippets.
        relevant_ids: Set of IDs of ground truth relevant documents/snippets.
        k: The cutoff depth.

    Returns:
        nDCG@K score (float between 0.0 and 1.0).
    """
    if k <= 0:
        return 0.0
    
    idcg = ideal_dcg_at_k(relevant_ids, k)
    
    if idcg == 0.0:
        return 0.0
    
    dcg = dcg_at_k(retrieved_ids, relevant_ids, k)
    
    return dcg / idcg

def evaluate_metrics(
    retrieved_ids: List[str],
    relevant_ids: List[str],
    k_values: Optional[List[int]] = None
) -> Dict[str, float]:
    """
    Evaluate all metrics (Precision@K, Recall@K, nDCG@K) for a single query.

    Args:
        retrieved_ids: List of IDs of retrieved documents/snippets.
        relevant_ids: List of IDs of ground truth relevant documents/snippets.
        k_values: List of K values to evaluate (e.g., [5, 10, 20]). 
                 Defaults to [5, 10, 20] if not provided.

    Returns:
        Dictionary containing metrics for each K value.
        Format: {
            "precision@5": float,
            "recall@5": float,
            "ndcg@5": float,
            "precision@10": float,
            ...
        }
    """
    if k_values is None:
        k_values = [5, 10, 20]
    
    relevant_set = set(relevant_ids)
    results = {}
    
    for k in k_values:
        p_key = f"precision@{k}"
        r_key = f"recall@{k}"
        n_key = f"ndcg@{k}"
        
        results[p_key] = precision_at_k(retrieved_ids, relevant_set, k)
        results[r_key] = recall_at_k(retrieved_ids, relevant_set, k)
        results[n_key] = ndcg_at_k(retrieved_ids, relevant_set, k)
    
    return results
