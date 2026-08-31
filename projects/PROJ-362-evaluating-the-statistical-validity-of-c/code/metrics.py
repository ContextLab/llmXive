"""
metrics.py - CPU-only implementation of NDCG@10 and MAP.

Provides functions for calculating Discounted Cumulative Gain (DCG),
Ideal DCG (IDCG), Normalized DCG (NDCG), Average Precision (AP),
and Mean Average Precision (MAP) for information retrieval evaluation.

All calculations are performed using pure Python and standard libraries
(math, typing) to ensure CPU-only execution without external heavy dependencies.
"""

import math
from typing import List, Optional, Dict, Any


def discount_factor(rank: int) -> float:
    """
    Calculate the discount factor for a given rank (1-indexed).
    Formula: 1 / log2(rank + 1)

    Args:
        rank: The rank position (1-based index).

    Returns:
        The discount factor.
    """
    if rank <= 0:
        return 0.0
    return 1.0 / math.log2(rank + 1)


def dcg_at_k(relevances: List[int], k: int) -> float:
    """
    Calculate Discounted Cumulative Gain at k.

    Args:
        relevances: List of relevance scores (integers) for documents in ranked order.
                    Index 0 corresponds to rank 1.
        k: The cutoff position for the calculation.

    Returns:
        The DCG@k score.
    """
    if not relevances:
        return 0.0

    dcg = 0.0
    limit = min(k, len(relevances))

    for i in range(limit):
        rank = i + 1  # 1-based rank
        rel = relevances[i]
        # DCG formula: sum( (2^rel - 1) / log2(r + 1) ) for r=1..k
        gain = (2 ** rel - 1)
        discount = math.log2(rank + 1)
        if discount > 0:
            dcg += gain / discount

    return dcg


def idcg_at_k(relevances: List[int], k: int) -> float:
    """
    Calculate Ideal DCG at k.
    This is the DCG of the perfect ranking (sorted by relevance descending).

    Args:
        relevances: List of relevance scores.
        k: The cutoff position.

    Returns:
        The IDCG@k score.
    """
    if not relevances:
        return 0.0

    # Sort relevances in descending order to simulate the ideal ranking
    sorted_relevances = sorted(relevances, reverse=True)
    return dcg_at_k(sorted_relevances, k)


def ndcg_at_k(relevances: List[int], k: int) -> float:
    """
    Calculate Normalized DCG at k.
    Formula: DCG@k / IDCG@k

    Args:
        relevances: List of relevance scores for the ranked documents.
        k: The cutoff position (e.g., 10 for NDCG@10).

    Returns:
        The NDCG@k score (0.0 to 1.0). Returns 0.0 if IDCG is 0.
    """
    dcg = dcg_at_k(relevances, k)
    idcg = idcg_at_k(relevances, k)

    if idcg == 0:
        # If there is no relevant document in the list, NDCG is undefined/0
        return 0.0

    return dcg / idcg


def average_precision(relevances: List[int]) -> float:
    """
    Calculate Average Precision (AP).
    AP is the average of precision values at each position where a relevant document is retrieved.

    Args:
        relevances: List of relevance scores (1 = relevant, 0 = not relevant, or higher integers).
                    For standard AP calculation, we treat any relevance > 0 as relevant.

    Returns:
        The Average Precision score.
    """
    if not relevances:
        return 0.0

    num_relevant = sum(1 for r in relevances if r > 0)
    if num_relevant == 0:
        return 0.0

    ap_sum = 0.0
    retrieved_count = 0

    for i, rel in enumerate(relevances):
        if rel > 0:
            retrieved_count += 1
            precision_at_i = retrieved_count / (i + 1)
            ap_sum += precision_at_i

    return ap_sum / num_relevant


def mean_average_precision(all_relevances: List[List[int]]) -> float:
    """
    Calculate Mean Average Precision (MAP) over a list of queries.

    Args:
        all_relevances: List of relevance lists, where each inner list represents
                        the relevance scores for one query's ranked documents.

    Returns:
        The Mean Average Precision score.
    """
    if not all_relevances:
        return 0.0

    ap_scores = [average_precision(relevances) for relevances in all_relevances]
    return sum(ap_scores) / len(ap_scores)