"""
Metrics and validation utilities for the llmXive pipeline.

Includes:
- Cosine similarity proxy calculation
- NDCG@10 calculation
- Statistical tests (Wilcoxon, Bonferroni)
- Dynamic sample size calculation
- LLM consensus validation
"""
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import wilcoxon
import os
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global model cache
_embedding_model = None

def get_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Get or initialize the sentence transformer model.
    
    Args:
        model_name: Name of the model to load (default: all-MiniLM-L6-v2)
        
    Returns:
        SentenceTransformer model instance
    """
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {model_name}")
        _embedding_model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully")
    return _embedding_model

def calculate_cosine_similarity_proxy(text1: str, text2: str, model: Optional[SentenceTransformer] = None) -> float:
    """
    Calculate cosine similarity between two texts using sentence embeddings.
    
    Args:
        text1: First text passage
        text2: Second text passage
        model: Optional pre-loaded model (loads default if None)
        
    Returns:
        Cosine similarity score (0.0 to 1.0)
    """
    if model is None:
        model = get_embedding_model()
    
    embeddings = model.encode([text1, text2], convert_to_numpy=True)
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    # Normalize to [0, 1] range (cosine similarity is [-1, 1])
    similarity = (similarity + 1) / 2
    return float(similarity)

def is_wasted_call(similarity: float, threshold: float = 0.95) -> bool:
    """
    Determine if a comparison is a 'wasted call' based on similarity threshold.
    
    Args:
        similarity: Cosine similarity score
        threshold: Threshold above which a call is considered wasted (default: 0.95)
        
    Returns:
        True if similarity > threshold, False otherwise
    """
    return similarity > threshold

def calculate_ndcg_at_k(relevances: List[int], k: int) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain at K.
    
    Args:
        relevances: List of relevance scores (integers)
        k: Number of positions to consider
        
    Returns:
        NDCG@k score (0.0 to 1.0)
    """
    if not relevances or k <= 0:
        return 0.0
    
    relevances = relevances[:k]
    
    # DCG calculation
    dcg = 0.0
    for i, rel in enumerate(relevances):
        dcg += (2 ** rel - 1) / np.log2(i + 2)  # i+2 because log2(1) = 0
    
    # Ideal DCG
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = 0.0
    for i, rel in enumerate(ideal_relevances):
        idcg += (2 ** rel - 1) / np.log2(i + 2)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg

def calculate_ndcg_at_10(relevances: List[int]) -> float:
    """
    Calculate NDCG@10 specifically.
    
    Args:
        relevances: List of relevance scores
        
    Returns:
        NDCG@10 score
    """
    return calculate_ndcg_at_k(relevances, 10)

def load_beir_ground_truth(dataset_name: str, split: str = "test") -> Dict[str, Dict[str, int]]:
    """
    Load BEIR ground truth (qrels) for a dataset.
    
    Args:
        dataset_name: Name of the BEIR dataset
        split: Split to load (default: test)
        
    Returns:
        Dictionary mapping query_id -> {doc_id: relevance_score}
    """
    from beir import util
    from beir.datasets.data_loader import GenericDataLoader
    
    url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset_name}.zip"
    out_dir = os.path.join("beir_data", dataset_name)
    
    if not os.path.exists(out_dir):
        logger.info(f"Downloading {dataset_name} dataset...")
        data_path = util.download_and_unzip(url, "beir_data")
        # The download_and_unzip returns the path, but we need to find the specific dataset
        out_dir = os.path.join("beir_data", dataset_name)
    
    logger.info(f"Loading ground truth for {dataset_name} ({split})")
    _, _, qrels = GenericDataLoader(out_dir).load(split=split)
    return qrels

def load_results_from_json(filepath: str) -> List[Dict[str, Any]]:
    """
    Load ranking results from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        List of result dictionaries
    """
    with open(filepath, 'r') as f:
        return json.load(f)

def aggregate_ndcg_scores(results: List[Dict[str, Any]], ground_truth: Dict[str, Dict[str, int]]) -> List[float]:
    """
    Aggregate NDCG@10 scores from ranking results.
    
    Args:
        results: List of ranking results (each with query_id and ranked doc_ids)
        ground_truth: Ground truth qrels
        
    Returns:
        List of NDCG@10 scores per query
    """
    ndcg_scores = []
    
    for result in results:
        query_id = result.get('query_id')
        if query_id not in ground_truth:
            continue
        
        ranked_docs = result.get('ranked_docs', [])
        relevances = []
        
        for doc_id in ranked_docs:
            rel = ground_truth[query_id].get(doc_id, 0)
            relevances.append(rel)
        
        ndcg = calculate_ndcg_at_10(relevances)
        ndcg_scores.append(ndcg)
    
    return ndcg_scores

def calculate_wasted_call_ratios(flagged_count: int, total_budget: int) -> float:
    """
    Calculate the ratio of wasted calls to total budget.
    
    Args:
        flagged_count: Number of flagged (wasted) calls
        total_budget: Total LLM call budget
        
    Returns:
        Wasted call ratio (0.0 to 1.0)
    """
    if total_budget == 0:
        return 0.0
    return flagged_count / total_budget

def wilcoxon_signed_rank_test(sample1: List[float], sample2: List[float]) -> Tuple[float, float]:
    """
    Perform Wilcoxon signed-rank test between two paired samples.
    
    Args:
        sample1: First sample (list of values)
        sample2: Second sample (list of values)
        
    Returns:
        Tuple of (statistic, p-value)
    """
    if len(sample1) != len(sample2):
        raise ValueError("Samples must be of equal length for paired test")
    
    if len(sample1) < 2:
        raise ValueError("Need at least 2 samples for Wilcoxon test")
    
    statistic, p_value = wilcoxon(sample1, sample2)
    return float(statistic), float(p_value)

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[Tuple[float, float, bool]]:
    """
    Apply Bonferroni correction for multiple hypothesis testing.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level (default: 0.05)
        
    Returns:
        List of tuples: (raw_p, corrected_p, is_significant)
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return []
    
    corrected_alpha = alpha / n_tests
    results = []
    
    for p in p_values:
        corrected_p = p * n_tests
        # Cap at 1.0
        corrected_p = min(corrected_p, 1.0)
        is_significant = corrected_p < alpha
        results.append((p, corrected_p, is_significant))
    
    return results

def calculate_dynamic_sample_size(
    total_flagged_count: int,
    minimum_threshold: int = 10,
    percentage: float = 0.05,
    max_limit: int = 1000
) -> int:
    """
    Calculate dynamic sample size for LLM consensus validation.
    
    Formula: sample_size = max(minimum_threshold, int(percentage * total_flagged_count))
    Then cap at max_limit.
    
    Args:
        total_flagged_count: Total number of flagged items
        minimum_threshold: Minimum sample size (default: 10)
        percentage: Percentage of flagged count to sample (default: 0.05 = 5%)
        max_limit: Maximum sample size cap (default: 1000)
        
    Returns:
        Calculated sample size
    """
    if total_flagged_count <= 0:
        return minimum_threshold
    
    calculated_size = int(percentage * total_flagged_count)
    sample_size = max(minimum_threshold, calculated_size)
    sample_size = min(sample_size, max_limit)
    
    return sample_size

def validate_proxy_accuracy(
    proxy_labels: List[bool],
    ground_truth_labels: List[bool]
) -> Dict[str, float]:
    """
    Validate proxy accuracy against ground truth labels.
    
    Args:
        proxy_labels: Labels from cosine similarity proxy
        ground_truth_labels: Ground truth labels from LLM consensus
        
    Returns:
        Dictionary with accuracy metrics
    """
    if len(proxy_labels) != len(ground_truth_labels):
        raise ValueError("Label lists must be of equal length")
    
    if len(proxy_labels) == 0:
        return {"accuracy": 0.0, "total_samples": 0}
    
    correct = sum(1 for p, g in zip(proxy_labels, ground_truth_labels) if p == g)
    accuracy = correct / len(proxy_labels)
    
    return {
        "accuracy": accuracy,
        "total_samples": len(proxy_labels),
        "correct": correct,
        "incorrect": len(proxy_labels) - correct
    }

def validate_jaccard_cosine_correlation(
    jaccard_scores: List[float],
    cosine_scores: List[float]
) -> float:
    """
    Calculate correlation between Jaccard and Cosine similarity scores.
    
    Args:
        jaccard_scores: List of Jaccard similarity scores
        cosine_scores: List of Cosine similarity scores
        
    Returns:
        Pearson correlation coefficient
    """
    if len(jaccard_scores) != len(cosine_scores):
        raise ValueError("Score lists must be of equal length")
    
    if len(jaccard_scores) < 2:
        return 0.0
    
    correlation = np.corrcoef(jaccard_scores, cosine_scores)[0, 1]
    return float(correlation) if not np.isnan(correlation) else 0.0

class StatisticalTestResult:
    """Container for statistical test results."""
    
    def __init__(self, test_name: str, statistic: float, p_value: float, significant: bool):
        self.test_name = test_name
        self.statistic = statistic
        self.p_value = p_value
        self.significant = significant

class BonferroniResult:
    """Container for Bonferroni-corrected test results."""
    
    def __init__(self, test_name: str, raw_p: float, corrected_p: float, significant: bool):
        self.test_name = test_name
        self.raw_p = raw_p
        self.corrected_p = corrected_p
        self.significant = significant

def main():
    """Main entry point for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Metrics utilities')
    parser.add_argument('--test', choices=['similarity', 'ndcg', 'sample_size'], required=True)
    args = parser.parse_args()
    
    if args.test == 'similarity':
        model = get_embedding_model()
        sim = calculate_cosine_similarity_proxy("Hello world", "Hello world")
        print(f"Cosine similarity: {sim}")
    elif args.test == 'ndcg':
        relevances = [1, 0, 1, 0, 0, 0, 0, 0, 0, 0]
        ndcg = calculate_ndcg_at_10(relevances)
        print(f"NDCG@10: {ndcg}")
    elif args.test == 'sample_size':
        size = calculate_dynamic_sample_size(100, minimum_threshold=10, percentage=0.05)
        print(f"Sample size for 100 flagged: {size}")

if __name__ == '__main__':
    main()
