"""
Metrics calculation module for llmXive.
Implements NDCG, cosine similarity proxy, and dynamic sample size calculation.
"""
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import wilcoxon
import os
import json

# Cache for the embedding model
_embedding_model = None

def get_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Get or initialize the sentence transformer model.
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model

def calculate_cosine_similarity_proxy(text1: str, text2: str, model_name: str = "all-MiniLM-L6-v2") -> float:
    """
    Calculate cosine similarity between two texts using the embedding model.
    """
    model = get_embedding_model(model_name)
    embeddings = model.encode([text1, text2], convert_to_numpy=True)
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(sim)

def is_wasted_call(similarity: float, threshold: float = 0.95) -> bool:
    """
    Determine if a call is 'wasted' based on similarity threshold.
    """
    return similarity > threshold

def calculate_ndcg_at_k(relevances: List[int], k: int) -> float:
    """
    Calculate NDCG@k given a list of relevance scores.
    """
    if not relevances:
        return 0.0
    
    dcg = 0.0
    idcg = 0.0
    
    # Sort relevances for IDCG
    sorted_relevances = sorted(relevances, reverse=True)
    
    for i, rel in enumerate(relevances[:k]):
        discount = np.log2(i + 2)
        dcg += (2 ** rel - 1) / discount
    
    for i, rel in enumerate(sorted_relevances[:k]):
        discount = np.log2(i + 2)
        idcg += (2 ** rel - 1) / discount
        
    if idcg == 0:
        return 0.0
    return dcg / idcg

def calculate_ndcg_at_10(relevances: List[int]) -> float:
    """
    Convenience function for NDCG@10.
    """
    return calculate_ndcg_at_k(relevances, 10)

def load_beir_ground_truth(dataset_name: str, split: str = "test") -> Dict[str, Dict[str, int]]:
    """
    Load ground truth qrels from BEIR dataset.
    Note: This assumes the data has been downloaded to data/raw/{dataset_name}.
    """
    # Implementation depends on where BEIR data is stored.
    # For now, returning a placeholder structure to avoid import errors if BEIR isn't local.
    # The actual loader logic is in data_loader.py.
    return {}

def load_results_from_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Load results from a JSON file.
    """
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as f:
        return json.load(f)

def aggregate_ndcg_scores(results: List[Dict[str, Any]]) -> float:
    """
    Aggregate NDCG scores from a list of results.
    """
    scores = [r.get("ndcg_at_10", 0.0) for r in results if "ndcg_at_10" in r]
    if not scores:
        return 0.0
    return float(np.mean(scores))

def calculate_wasted_call_ratios(comparisons: List[Dict[str, Any]], threshold: float = 0.95) -> float:
    """
    Calculate the ratio of wasted calls based on similarity threshold.
    """
    if not comparisons:
        return 0.0
    wasted = sum(1 for c in comparisons if c.get("similarity", 0) > threshold)
    return wasted / len(comparisons)

def wilcoxon_signed_rank_test(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """
    Perform Wilcoxon signed-rank test.
    Returns (statistic, p-value).
    """
    if len(group1) != len(group2):
        raise ValueError("Groups must be of equal length for paired test.")
    stat, pval = wilcoxon(group1, group2)
    return float(stat), float(pval)

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    corrected = [min(p * n, 1.0) for p in p_values]
    return corrected

def calculate_dynamic_sample_size(total_flagged: int, min_sample: int = 20, max_sample: int = 1000, percentage: float = 0.2) -> int:
    """
    Calculate the dynamic sample size for LLM consensus validation.
    
    Logic:
    - If total_flagged is 0, return 0.
    - Base size is percentage of total_flagged.
    - Enforce minimum sample size (min_sample).
    - Enforce maximum sample size (max_sample).
    
    Args:
        total_flagged: Total number of flagged pairs from T013a.
        min_sample: Minimum number of samples to validate.
        max_sample: Maximum number of samples to validate.
        percentage: Fraction of flagged pairs to sample.
    
    Returns:
        int: The calculated sample size.
    """
    if total_flagged <= 0:
        return 0
    
    calculated = int(total_flagged * percentage)
    final_size = max(min_sample, min(calculated, max_sample))
    
    return final_size

def validate_proxy_accuracy(sample_data: List[Dict[str, Any]]) -> float:
    """
    Validate the accuracy of the cosine similarity proxy against ground truth.
    """
    if not sample_data:
        return 0.0
    
    correct = 0
    total = 0
    
    for item in sample_data:
        proxy_wasted = item.get("proxy_wasted", False)
        ground_truth_wasted = item.get("ground_truth_wasted", False)
        
        if proxy_wasted == ground_truth_wasted:
            correct += 1
        total += 1
    
    if total == 0:
        return 0.0
    return correct / total

def validate_jaccard_cosine_correlation(jaccard_scores: List[float], cosine_scores: List[float]) -> float:
    """
    Calculate correlation between Jaccard and Cosine similarity scores.
    """
    if len(jaccard_scores) != len(cosine_scores) or len(jaccard_scores) == 0:
        return 0.0
    corr = np.corrcoef(jaccard_scores, cosine_scores)[0, 1]
    return float(corr) if not np.isnan(corr) else 0.0

class StatisticalTestResult:
    def __init__(self, test_name: str, statistic: float, p_value: float, significant: bool):
        self.test_name = test_name
        self.statistic = statistic
        self.p_value = p_value
        self.significant = significant

class BonferroniResult:
    def __init__(self, original_p: float, corrected_p: float, significant: bool):
        self.original_p = original_p
        self.corrected_p = corrected_p
        self.significant = significant

def main():
    """
    Main function for testing metrics module.
    """
    pass
