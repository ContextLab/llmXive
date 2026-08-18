"""
Metric calculation functions (CPU-only).
"""

import math
from typing import List, Optional, Dict, Any

def discount_factor(rank: int) -> float:
    """
    Calculate the discount factor for a given rank (1-indexed).
    DCG uses log2(rank + 1).
    """
    return 1.0 / math.log2(rank + 1)

def dcg_at_k(relevance_labels: List[int], k: Optional[int] = None) -> float:
    """
    Calculate Discounted Cumulative Gain (DCG) at rank k.
    
    Args:
        relevance_labels: List of relevance scores (0-indexed list, 1-indexed rank).
        k: Rank cutoff. If None, uses all labels.
    
    Returns:
        DCG score.
    """
    if k is None:
        k = len(relevance_labels)
    
    dcg = 0.0
    for i, rel in enumerate(relevance_labels[:k]):
        # i is 0-indexed, so rank is i+1
        rank = i + 1
        dcg += rel * discount_factor(rank)
    
    return dcg

def idcg_at_k(relevance_labels: List[int], k: Optional[int] = None) -> float:
    """
    Calculate Ideal DCG (IDCG) at rank k.
    IDCG is the DCG of the sorted relevance labels (descending).
    
    Args:
        relevance_labels: List of relevance scores.
        k: Rank cutoff.
    
    Returns:
        IDCG score.
    """
    # Sort labels in descending order to get ideal ranking
    sorted_labels = sorted(relevance_labels, reverse=True)
    return dcg_at_k(sorted_labels, k)

def ndcg_at_k(relevance_labels: List[int], k: Optional[int] = None) -> float:
    """
    Calculate Normalized DCG (NDCG) at rank k.
    
    Args:
        relevance_labels: List of relevance scores.
        k: Rank cutoff.
    
    Returns:
        NDCG score (between 0 and 1).
    """
    dcg = dcg_at_k(relevance_labels, k)
    idcg = idcg_at_k(relevance_labels, k)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg

def average_precision(relevance_labels: List[int]) -> float:
    """
    Calculate Average Precision (AP).
    AP is the average of precision at each position where a relevant document is retrieved.
    
    Args:
        relevance_labels: List of relevance scores (binary or graded).
            For binary: 1 = relevant, 0 = non-relevant.
            For graded: Typically binarized (rel > 0) for AP calculation.
    
    Returns:
        Average Precision score.
    """
    ap = 0.0
    num_relevant = 0
    precision_sum = 0.0
    
    for i, rel in enumerate(relevance_labels):
        # Treat any relevance > 0 as relevant for AP
        is_relevant = rel > 0
        if is_relevant:
            num_relevant += 1
            precision_at_i = num_relevant / (i + 1)
            precision_sum += precision_at_i
    
    if num_relevant == 0:
        return 0.0
    
    return precision_sum / num_relevant

def mean_average_precision(relevance_lists: List[List[int]]) -> float:
    """
    Calculate Mean Average Precision (MAP) over a list of queries.
    
    Args:
        relevance_lists: List of lists, where each inner list is relevance labels for a query.
    
    Returns:
        MAP score.
    """
    if not relevance_lists:
        return 0.0
    
    ap_sum = 0.0
    for labels in relevance_lists:
        ap_sum += average_precision(labels)
    
    return ap_sum / len(relevance_lists)
