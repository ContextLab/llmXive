"""
Metrics module for evaluating retrieval performance.
Implements Precision@K, Recall@K, DCG@K, and nDCG@K calculations.
"""
import math
from typing import List, Dict, Any, Optional, Set

def precision_at_k(relevant_ids: Set[int], retrieved_ids: List[int], k: int) -> float:
    """
    Calculate Precision@K.
    
    Args:
        relevant_ids: Set of IDs of relevant documents (ground truth).
        retrieved_ids: List of IDs of retrieved documents in order.
        k: The cutoff rank.
        
    Returns:
        Precision@K value between 0.0 and 1.0.
    """
    if k <= 0:
        return 0.0
    
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
        
    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return hits / len(top_k)

def recall_at_k(relevant_ids: Set[int], retrieved_ids: List[int], k: int) -> float:
    """
    Calculate Recall@K.
    
    Args:
        relevant_ids: Set of IDs of relevant documents (ground truth).
        retrieved_ids: List of IDs of retrieved documents in order.
        k: The cutoff rank.
        
    Returns:
        Recall@K value between 0.0 and 1.0.
    """
    total_relevant = len(relevant_ids)
    if total_relevant == 0:
        return 0.0
        
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
        
    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return hits / total_relevant

def dcg_at_k(relevant_ids: Set[int], retrieved_ids: List[int], k: int) -> float:
    """
    Calculate Discounted Cumulative Gain at K.
    
    Args:
        relevant_ids: Set of IDs of relevant documents (ground truth).
        retrieved_ids: List of IDs of retrieved documents in order.
        k: The cutoff rank.
        
    Returns:
        DCG@K value.
    """
    dcg = 0.0
    top_k = retrieved_ids[:k]
    
    for i, doc_id in enumerate(top_k):
        if doc_id in relevant_ids:
            # Relevance is binary (1 if relevant, 0 otherwise)
            relevance = 1.0
            # Discount factor: log2(i + 1 + 1) -> log2(i + 2)
            discount = math.log2(i + 2)
            dcg += relevance / discount
            
    return dcg

def ideal_dcg_at_k(relevant_ids: Set[int], k: int) -> float:
    """
    Calculate Ideal DCG at K (IDCG).
    This assumes the most relevant documents are ranked first.
    Since relevance is binary here, we just take the first min(|relevant|, k) items.
    
    Args:
        relevant_ids: Set of IDs of relevant documents (ground truth).
        k: The cutoff rank.
        
    Returns:
        IDCG@K value.
    """
    num_relevant = len(relevant_ids)
    if num_relevant == 0:
        return 0.0
        
    # In ideal case, all relevant docs are at the top
    num_items_to_consider = min(num_relevant, k)
    
    idcg = 0.0
    for i in range(num_items_to_consider):
        relevance = 1.0
        discount = math.log2(i + 2)
        idcg += relevance / discount
        
    return idcg

def ndcg_at_k(relevant_ids: Set[int], retrieved_ids: List[int], k: int) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain at K.
    
    Args:
        relevant_ids: Set of IDs of relevant documents (ground truth).
        retrieved_ids: List of IDs of retrieved documents in order.
        k: The cutoff rank.
        
    Returns:
        nDCG@K value between 0.0 and 1.0.
    """
    dcg = dcg_at_k(relevant_ids, retrieved_ids, k)
    idcg = ideal_dcg_at_k(relevant_ids, k)
    
    if idcg == 0.0:
        return 0.0
        
    return dcg / idcg

def evaluate_metrics(
    relevant_ids: Set[int], 
    retrieved_ids: List[int], 
    k_values: List[int] = [1, 3, 5, 10]
) -> Dict[str, float]:
    """
    Evaluate all metrics for a single query.
    
    Args:
        relevant_ids: Set of IDs of relevant documents (ground truth).
        retrieved_ids: List of IDs of retrieved documents in order.
        k_values: List of K values to evaluate (e.g., [1, 3, 5, 10]).
        
    Returns:
        Dictionary containing all metrics for all K values.
        Format: {'P@1': ..., 'R@1': ..., 'nDCG@1': ..., 'P@3': ...}
    """
    results = {}
    
    for k in k_values:
        p_k = precision_at_k(relevant_ids, retrieved_ids, k)
        r_k = recall_at_k(relevant_ids, retrieved_ids, k)
        ndcg_k = ndcg_at_k(relevant_ids, retrieved_ids, k)
        
        results[f'P@{k}'] = p_k
        results[f'R@{k}'] = r_k
        results[f'nDCG@{k}'] = ndcg_k
        
    return results
