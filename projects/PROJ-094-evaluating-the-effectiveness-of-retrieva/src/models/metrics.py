"""
Metrics calculation module for retrieval evaluation.

Implements Precision@K, Recall@K, DCG@K, IDCG@K, and nDCG@K calculations
against ground truth labels for code search evaluation.
"""
import math
from typing import List, Dict, Any, Optional, Set

def precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = 10) -> float:
    """
    Calculate Precision@K.

    Precision@K = (Number of relevant documents in top K) / K

    Args:
        retrieved_ids: List of retrieved document IDs in ranked order.
        relevant_ids: Set of ground truth relevant document IDs.
        k: The cutoff rank (default 10).

    Returns:
        Precision score between 0.0 and 1.0.
    """
    if k <= 0:
        return 0.0

    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0

    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return hits / k

def recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = 10) -> float:
    """
    Calculate Recall@K.

    Recall@K = (Number of relevant documents in top K) / (Total number of relevant documents)

    Args:
        retrieved_ids: List of retrieved document IDs in ranked order.
        relevant_ids: Set of ground truth relevant document IDs.
        k: The cutoff rank (default 10).

    Returns:
        Recall score between 0.0 and 1.0.
    """
    if not relevant_ids:
        return 0.0

    top_k = retrieved_ids[:k]
    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return hits / len(relevant_ids)

def dcg_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = 10) -> float:
    """
    Calculate Discounted Cumulative Gain (DCG)@K.

    DCG@K = sum_{i=1}^{k} (rel_i / log2(i + 1))
    where rel_i is 1 if the document at rank i is relevant, 0 otherwise.

    Args:
        retrieved_ids: List of retrieved document IDs in ranked order.
        relevant_ids: Set of ground truth relevant document IDs.
        k: The cutoff rank (default 10).

    Returns:
        DCG score (non-negative float).
    """
    if k <= 0:
        return 0.0

    dcg = 0.0
    top_k = retrieved_ids[:k]

    for i, doc_id in enumerate(top_k):
        if doc_id in relevant_ids:
            # i is 0-indexed, so rank is i+1. Formula uses log2(rank + 1)
            gain = 1.0
            discount = math.log2(i + 2)
            dcg += gain / discount

    return dcg

def ideal_dcg_at_k(relevant_ids: Set[str], k: int = 10) -> float:
    """
    Calculate Ideal DCG (IDCG)@K.

    IDCG is the DCG of the perfect ranking where all relevant documents
    appear first.

    Args:
        relevant_ids: Set of ground truth relevant document IDs.
        k: The cutoff rank (default 10).

    Returns:
        IDCG score (non-negative float).
    """
    if k <= 0:
        return 0.0

    num_relevant = min(len(relevant_ids), k)
    idcg = 0.0

    for i in range(num_relevant):
        gain = 1.0
        discount = math.log2(i + 2)
        idcg += gain / discount

    return idcg

def ndcg_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = 10) -> float:
    """
    Calculate Normalized DCG (nDCG)@K.

    nDCG@K = DCG@K / IDCG@K

    Args:
        retrieved_ids: List of retrieved document IDs in ranked order.
        relevant_ids: Set of ground truth relevant document IDs.
        k: The cutoff rank (default 10).

    Returns:
        nDCG score between 0.0 and 1.0.
    """
    idcg = ideal_dcg_at_k(relevant_ids, k)
    if idcg == 0.0:
        return 0.0

    dcg = dcg_at_k(retrieved_ids, relevant_ids, k)
    return dcg / idcg

def evaluate_metrics(
    retrieved_ids: List[str],
    relevant_ids: List[str],
    k_values: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Evaluate all retrieval metrics for a single query.

    Args:
        retrieved_ids: List of retrieved document IDs in ranked order.
        relevant_ids: List of ground truth relevant document IDs.
        k_values: List of K values to evaluate (default [1, 5, 10, 20]).

    Returns:
        Dictionary containing Precision@K, Recall@K, and nDCG@K for each K.
    """
    if k_values is None:
        k_values = [1, 5, 10, 20]

    relevant_set = set(relevant_ids)
    results = {
        "precision_at_k": {},
        "recall_at_k": {},
        "ndcg_at_k": {}
    }

    for k in k_values:
        results["precision_at_k"][k] = precision_at_k(retrieved_ids, relevant_set, k)
        results["recall_at_k"][k] = recall_at_k(retrieved_ids, relevant_set, k)
        results["ndcg_at_k"][k] = ndcg_at_k(retrieved_ids, relevant_set, k)

    return results
