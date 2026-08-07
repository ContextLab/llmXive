import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import wilcoxon
import os
import json
import logging
import warnings

# Custom warning class for statistical degeneracy
class StatisticalDegeneracyWarning(UserWarning):
    pass

# Ensure the warning is shown
warnings.simplefilter("always", StatisticalDegeneracyWarning)

logger = logging.getLogger(__name__)

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        logger.info("Loading sentence-transformer model: all-MiniLM-L6-v2")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def calculate_cosine_similarity_proxy(doc1_text: str, doc2_text: str) -> float:
    model = get_embedding_model()
    embeddings = model.encode([doc1_text, doc2_text], convert_to_numpy=True)
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(sim)

def is_wasted_call(cosine_sim: float, threshold: float = 0.95) -> bool:
    return cosine_sim > threshold

def calculate_ndcg_at_k(relevances: List[int], k: int) -> float:
    if not relevances or k <= 0:
        return 0.0
    relevances = relevances[:k]
    dcg = 0.0
    idcg = 0.0
    for i, rel in enumerate(relevances):
        dcg += (2**rel - 1) / np.log2(i + 2)
        idcg += (2**rel - 1) / np.log2(i + 2)
    if idcg == 0:
        return 0.0
    return dcg / idcg

def calculate_ndcg_at_10(relevances: List[int]) -> float:
    return calculate_ndcg_at_k(relevances, 10)

def load_beir_ground_truth(dataset_name: str, split: str = "test") -> Dict[str, Dict[str, int]]:
    from beir import util
    from beir.datasets.data_loader import GenericDataLoader
    
    url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset_name}.zip"
    cache_dir = "beir_data"
    data_path = util.download_and_unzip(url, cache_dir)
    
    corpus, queries, qrels = GenericDataLoader(data_path).load(split=split)
    return qrels

def load_results_from_json(filepath: str) -> List[Dict[str, Any]]:
    with open(filepath, 'r') as f:
        return json.load(f)

def aggregate_ndcg_scores(results: List[Dict[str, Any]]) -> List[float]:
    scores = []
    for r in results:
        if 'ndcg_at_10' in r:
            scores.append(r['ndcg_at_10'])
    return scores

def calculate_wasted_call_ratios(comparison_log_path: str, threshold: float = 0.95) -> Dict[str, Any]:
    if not os.path.exists(comparison_log_path):
        logger.warning(f"Comparison log not found at {comparison_log_path}")
        return {"wasted_count": 0, "total_pairs": 0, "wasted_ratio": 0.0}
    
    wasted_count = 0
    total_pairs = 0
    
    with open(comparison_log_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            total_pairs += 1
            if entry.get('cosine_sim', 0.0) > threshold:
                wasted_count += 1
    
    ratio = wasted_count / total_pairs if total_pairs > 0 else 0.0
    return {
        "wasted_count": wasted_count,
        "total_pairs": total_pairs,
        "wasted_ratio": ratio
    }

def wilcoxon_signed_rank_test(sample1: List[float], sample2: List[float]) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test with robust handling of zero variance.
    
    If variance is zero (perfect scores or identical samples), logs a 
    StatisticalDegeneracyWarning and returns a p-value indicating no significant difference.
    """
    if len(sample1) != len(sample2):
        raise ValueError("Sample sizes must be equal for paired test")
    
    if len(sample1) == 0:
        logger.warning("Empty sample provided for Wilcoxon test")
        return {"statistic": 0.0, "pvalue": 1.0, "degenerate": True, "reason": "empty_sample"}

    sample1 = np.array(sample1)
    sample2 = np.array(sample2)
    
    # Check for zero variance in differences
    diffs = sample1 - sample2
    unique_diffs = np.unique(diffs)
    
    if len(unique_diffs) == 1 and unique_diffs[0] == 0:
        # Perfect tie / zero variance case
        logger.warning(
            "StatisticalDegeneracyWarning: Zero variance detected in Wilcoxon test (all differences are zero). "
            "Reporting p-value as 1.0 (no significant difference)."
        )
        warnings.warn(
            "StatisticalDegeneracyWarning: Zero variance detected in Wilcoxon test. "
            "Result is degenerate; p-value set to 1.0.",
            StatisticalDegeneracyWarning
        )
        return {
            "statistic": 0.0,
            "pvalue": 1.0,
            "degenerate": True,
            "reason": "zero_variance"
        }
    
    # Standard Wilcoxon test
    try:
        stat, pval = wilcoxon(sample1, sample2)
        return {
            "statistic": float(stat),
            "pvalue": float(pval),
            "degenerate": False,
            "reason": "normal"
        }
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        return {
            "statistic": 0.0,
            "pvalue": 1.0,
            "degenerate": True,
            "reason": f"exception: {str(e)}"
        }

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction for multiple hypothesis testing.
    
    Args:
        p_values: List of raw p-values from statistical tests.
        alpha: Significance level (default 0.05).
    
    Returns:
        Dict with corrected p-values, adjusted alpha, and significance flags.
    """
    n = len(p_values)
    if n == 0:
        return {"corrected_pvalues": [], "adjusted_alpha": alpha, "significant": []}
    
    adjusted_alpha = alpha / n
    corrected_pvalues = [min(p * n, 1.0) for p in p_values]
    significant = [p < adjusted_alpha for p in corrected_pvalues]
    
    return {
        "corrected_pvalues": corrected_pvalues,
        "adjusted_alpha": adjusted_alpha,
        "significant": significant
    }

def calculate_dynamic_sample_size(total_count: int, min_threshold: int = 10, percentage: float = 0.05) -> int:
    """
    Calculate sample size as max(min_threshold, percentage * total_count).
    
    Args:
        total_count: Total population size.
        min_threshold: Minimum sample size required.
        percentage: Percentage of population to sample.
    
    Returns:
        Calculated sample size.
    """
    calculated = int(total_count * percentage)
    return max(min_threshold, calculated)

def validate_proxy_accuracy(proxy_scores: List[float], consensus_labels: List[bool]) -> Dict[str, float]:
    """
    Validate the accuracy of the cosine similarity proxy against LLM consensus.
    
    Args:
        proxy_scores: List of cosine similarity scores.
        consensus_labels: List of boolean consensus labels (True = wasted).
    
    Returns:
        Dict with accuracy metrics.
    """
    if len(proxy_scores) != len(consensus_labels):
        raise ValueError("Proxy scores and consensus labels must have same length")
    
    threshold = 0.95
    predictions = [s > threshold for s in proxy_scores]
    
    correct = sum(1 for p, l in zip(predictions, consensus_labels) if p == l)
    accuracy = correct / len(consensus_labels) if consensus_labels else 0.0
    
    return {
        "accuracy": accuracy,
        "total_samples": len(consensus_labels),
        "correct_predictions": correct
    }

def validate_jaccard_cosine_correlation(jaccard_scores: List[float], cosine_scores: List[float]) -> float:
    """
    Calculate Pearson correlation between Jaccard and Cosine similarity scores.
    
    Args:
        jaccard_scores: List of Jaccard similarity scores.
        cosine_scores: List of Cosine similarity scores.
    
    Returns:
        Correlation coefficient.
    """
    if len(jaccard_scores) != len(cosine_scores):
        raise ValueError("Jaccard and cosine scores must have same length")
    
    if len(jaccard_scores) < 2:
        return 0.0
    
    jaccard_arr = np.array(jaccard_scores)
    cosine_arr = np.array(cosine_scores)
    
    # Handle constant arrays
    if np.std(jaccard_arr) == 0 or np.std(cosine_arr) == 0:
        logger.warning("Zero variance in Jaccard or Cosine scores; correlation undefined.")
        return 0.0
    
    corr = np.corrcoef(jaccard_arr, cosine_arr)[0, 1]
    return float(corr) if not np.isnan(corr) else 0.0

def main():
    """Main entry point for metrics module testing."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage of Wilcoxon with zero variance handling
    sample_a = [0.98, 0.99, 1.0, 0.97]
    sample_b = [0.98, 0.99, 1.0, 0.97]  # Identical -> zero variance
    
    result = wilcoxon_signed_rank_test(sample_a, sample_b)
    logger.info(f"Wilcoxon Result: {result}")
    
    # Example with normal data
    sample_c = [0.98, 0.99, 1.0, 0.97]
    sample_d = [0.85, 0.88, 0.90, 0.82]
    
    result2 = wilcoxon_signed_rank_test(sample_c, sample_d)
    logger.info(f"Wilcoxon Result (normal): {result2}")

if __name__ == "__main__":
    main()