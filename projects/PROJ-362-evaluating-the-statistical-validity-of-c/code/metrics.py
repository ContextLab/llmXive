"""
Metrics module for ranking evaluation.
Implements CPU-only NDCG@k and MAP calculations with explicit relevance mapping.
"""
import math
from typing import List, Optional


def discount_factor(rank: int) -> float:
    """
    Calculate the discount factor for a given rank (1-indexed).
    Formula: 1 / log2(rank + 1)

    Args:
        rank: The position of the document (1-indexed).

    Returns:
        The discount factor.
    """
    if rank <= 1:
        return 1.0
    return 1.0 / math.log2(rank + 1)


def dcg_at_k(relevances: List[int], k: Optional[int] = None) -> float:
    """
    Calculate Discounted Cumulative Gain (DCG) at rank k.

    Args:
        relevances: List of relevance scores (0-indexed list, where index 0 is rank 1).
        k: The cutoff rank. If None, calculates DCG for all relevances.

    Returns:
        The DCG score.
    """
    if not relevances:
        return 0.0

    if k is not None:
        relevances = relevances[:k]

    dcg = 0.0
    for i, rel in enumerate(relevances):
        # i is 0-indexed, so rank is i + 1
        rank = i + 1
        dcg += (2 ** rel - 1) * discount_factor(rank)

    return dcg


def idcg_at_k(relevances: List[int], k: Optional[int] = None) -> float:
    """
    Calculate Ideal Discounted Cumulative Gain (IDCG) at rank k.
    IDCG is the DCG of the ideal ordering (sorted by relevance descending).

    Args:
        relevances: List of relevance scores.
        k: The cutoff rank. If None, calculates IDCG for all relevances.

    Returns:
        The IDCG score.
    """
    if not relevances:
        return 0.0

    # Sort relevances in descending order to get ideal ordering
    ideal_relevances = sorted(relevances, reverse=True)

    if k is not None:
        ideal_relevances = ideal_relevances[:k]

    return dcg_at_k(ideal_relevances, k)


def ndcg_at_k(relevances: List[int], k: Optional[int] = None) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain (NDCG) at rank k.
    NDCG = DCG / IDCG

    Args:
        relevances: List of relevance scores (0-indexed list, where index 0 is rank 1).
        k: The cutoff rank. If None, calculates NDCG for all relevances.

    Returns:
        The NDCG score (between 0.0 and 1.0). Returns 0.0 if IDCG is 0.
    """
    if not relevances:
        return 0.0

    dcg = dcg_at_k(relevances, k)
    idcg = idcg_at_k(relevances, k)

    if idcg == 0.0:
        return 0.0

    return dcg / idcg


def average_precision(relevances: List[int], k: Optional[int] = None) -> float:
    """
    Calculate Average Precision (AP) at rank k.
    AP is the average of precision scores at each relevant document.

    Args:
        relevances: List of relevance scores (0-indexed list, where index 0 is rank 1).
                   Relevance > 0 indicates a relevant document.
        k: The cutoff rank. If None, calculates AP for all relevances.

    Returns:
        The Average Precision score. Returns 0.0 if no relevant documents exist.
    """
    if not relevances:
        return 0.0

    if k is not None:
        relevances = relevances[:k]

    # Filter to only relevant documents (relevance > 0)
    # We need to track which positions are relevant
    relevant_count = 0
    precision_sum = 0.0

    for i, rel in enumerate(relevances):
        if rel > 0:
            relevant_count += 1
            # Precision at this position: relevant_count / (i + 1)
            precision_sum += relevant_count / (i + 1)

    if relevant_count == 0:
        return 0.0

    return precision_sum / relevant_count


def mean_average_precision(all_relevances: List[List[int]], k: Optional[int] = None) -> float:
    """
    Calculate Mean Average Precision (MAP) over a list of relevance lists.
    MAP is the mean of Average Precision scores for each query.

    Args:
        all_relevances: List of relevance lists (one per query).
        k: The cutoff rank. If None, calculates AP for all relevances.

    Returns:
        The Mean Average Precision score. Returns 0.0 if no queries exist.
    """
    if not all_relevances:
        return 0.0

    ap_scores = [average_precision(rels, k) for rels in all_relevances]

    return sum(ap_scores) / len(ap_scores)