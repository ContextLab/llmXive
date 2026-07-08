import math
from typing import List, Optional

def discount_factor(k: int) -> float:
    """Calculate the discount factor for position k (1-indexed)."""
    return 1.0 / math.log2(k + 1)

def dcg_at_k(relevance_labels: List[int], k: Optional[int] = None) -> float:
    """Calculate DCG at k."""
    if k is None:
        k = len(relevance_labels)
    else:
        k = min(k, len(relevance_labels))
    
    dcg = 0.0
    for i in range(k):
        dcg += (2 ** relevance_labels[i] - 1) * discount_factor(i + 1)
    return dcg

def idcg_at_k(relevance_labels: List[int], k: Optional[int] = None) -> float:
    """Calculate IDCG at k (Ideal DCG)."""
    if k is None:
        k = len(relevance_labels)
    else:
        k = min(k, len(relevance_labels))
    
    # Sort labels in descending order for ideal ranking
    sorted_labels = sorted(relevance_labels, reverse=True)
    return dcg_at_k(sorted_labels, k)

def ndcg_at_k(relevance_labels: List[int], k: Optional[int] = None) -> float:
    """Calculate NDCG at k."""
    dcg = dcg_at_k(relevance_labels, k)
    idcg = idcg_at_k(relevance_labels, k)
    if idcg == 0:
        return 0.0
    return dcg / idcg

def average_precision(relevance_labels: List[int], k: Optional[int] = None) -> float:
    """Calculate Average Precision (AP)."""
    if k is None:
        k = len(relevance_labels)
    else:
        k = min(k, len(relevance_labels))
    
    num_relevant = sum(1 for r in relevance_labels if r > 0)
    if num_relevant == 0:
        return 0.0
    
    ap = 0.0
    num_retrieved = 0
    for i in range(k):
        if relevance_labels[i] > 0:
            num_retrieved += 1
            ap += num_retrieved / (i + 1)
    
    return ap / num_relevant

def mean_average_precision(relevance_list: List[List[int]]) -> float:
    """Calculate Mean Average Precision (MAP) over a list of queries."""
    if not relevance_list:
        return 0.0
    return sum(average_precision(q) for q in relevance_list) / len(relevance_list)
