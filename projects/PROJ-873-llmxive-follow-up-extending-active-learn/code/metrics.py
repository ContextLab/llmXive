import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import wilcoxon
import os
import json
import logging
from config import get_config

logger = logging.getLogger(__name__)

# Global model cache
_embedding_model = None

def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: all-MiniLM-L6-v2")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

def calculate_cosine_similarity_proxy(text1: str, text2: str) -> float:
    model = get_embedding_model()
    embeddings = model.encode([text1, text2])
    return float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])

def is_wasted_call(similarity: float, threshold: float = 0.95) -> bool:
    return similarity > threshold

def calculate_ndcg_at_k(relevances: List[int], k: int) -> float:
    dcg = 0.0
    for i, rel in enumerate(relevances[:k]):
        dcg += (2 ** rel - 1) / np.log2(i + 2)
    idcg = sum((2 ** rel - 1) / np.log2(i + 2) for i, rel in enumerate(sorted(relevances[:k], reverse=True)))
    return dcg / idcg if idcg > 0 else 0.0

def calculate_ndcg_at_10(relevances: List[int]) -> float:
    return calculate_ndcg_at_k(relevances, 10)

def load_beir_ground_truth(dataset_name: str, queries: List[str]) -> Dict[str, List[int]]:
    # Placeholder for BEIR ground truth loading logic
    # In a real implementation, this would load from BEIR dataset
    return {q: [1] * 10 for q in queries}

def load_results_from_json(filepath: str) -> List[Dict[str, Any]]:
    with open(filepath, 'r') as f:
        return json.load(f)

def aggregate_ndcg_scores(results: List[Dict[str, Any]]) -> float:
    if not results:
        return 0.0
    return sum(r.get('ndcg_at_10', 0.0) for r in results) / len(results)

def calculate_ndcg_for_clustering_aided_variant(results: List[Dict[str, Any]]) -> float:
    return aggregate_ndcg_scores(results)

def wilcoxon_signed_rank_test(sample1: List[float], sample2: List[float]) -> Tuple[float, float]:
    if len(sample1) != len(sample2) or len(sample1) < 2:
        raise ValueError("Samples must be of equal length >= 2")
    stat, p_value = wilcoxon(sample1, sample2)
    return float(stat), float(p_value)

def bonferroni_correction(p_values: List[float], num_tests: int) -> List[float]:
    return [min(p * num_tests, 1.0) for p in p_values]

def validate_proxy_accuracy(proxy_scores: List[float], ground_truth: List[bool]) -> Dict[str, float]:
    if len(proxy_scores) != len(ground_truth):
        raise ValueError("Proxy scores and ground truth must be of equal length")
    correct = sum(1 for p, g in zip(proxy_scores, ground_truth) if (p > 0.95) == g)
    accuracy = correct / len(ground_truth)
    return {
        'accuracy': accuracy,
        'total_samples': len(ground_truth),
        'correct_predictions': correct
    }

def calculate_dynamic_sample_size(total_flagged_count: int, max_limit: int = 1000) -> int:
    """
    Calculate the dynamic sample size for LLM consensus validation.
    
    Args:
        total_flagged_count: The count of flagged pairs from T013a.
        max_limit: The maximum limit for the sample size (default 1000).
        
    Returns:
        The calculated sample size, capped at max_limit.
    """
    if total_flagged_count <= 0:
        return 0
    
    # Dynamic calculation: take 10% of flagged pairs, or a fixed number based on magnitude
    # This is a heuristic; adjust based on specific research requirements
    if total_flagged_count < 100:
        sample_size = total_flagged_count  # Take all if very small
    elif total_flagged_count < 1000:
        sample_size = int(total_flagged_count * 0.2)  # 20% for medium
    else:
        sample_size = int(total_flagged_count * 0.1)  # 10% for large
    
    # Cap at maximum limit
    return min(sample_size, max_limit)

def validate_jaccard_cosine_correlation(jaccard_scores: List[float], cosine_scores: List[float]) -> float:
    if len(jaccard_scores) != len(cosine_scores) or len(jaccard_scores) < 2:
        return 0.0
    corr = np.corrcoef(jaccard_scores, cosine_scores)[0, 1]
    return float(corr) if not np.isnan(corr) else 0.0

def calculate_wasted_call_ratios(total_calls: int, wasted_calls: int) -> Dict[str, float]:
    if total_calls == 0:
        return {'wasted_ratio': 0.0, 'total_calls': 0, 'wasted_calls': 0}
    return {
        'wasted_ratio': wasted_calls / total_calls,
        'total_calls': total_calls,
        'wasted_calls': wasted_calls
    }

class StatisticalTestResult:
    def __init__(self, test_name: str, statistic: float, p_value: float, significant: bool):
        self.test_name = test_name
        self.statistic = statistic
        self.p_value = p_value
        self.significant = significant

class BonferroniResult:
    def __init__(self, test_name: str, original_p: float, corrected_p: float, significant: bool):
        self.test_name = test_name
        self.original_p = original_p
        self.corrected_p = corrected_p
        self.significant = significant

def main():
    # Example usage for testing
    logger.info("Running metrics module main")
    if __name__ == '__main__':
        pass
