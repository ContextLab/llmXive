import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import wilcoxon
import os
import logging

# --- Configuration & Caching ---
_embedding_model: Optional[SentenceTransformer] = None
logger = logging.getLogger(__name__)

def get_embedding_model() -> SentenceTransformer:
    """Lazy load the embedding model to avoid overhead during imports."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading SentenceTransformer model: all-MiniLM-L6-v2")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

# --- Similarity & Proxy Logic ---

def calculate_cosine_similarity_proxy(texts: List[str]) -> np.ndarray:
    """
    Calculate cosine similarity between all pairs of texts using embeddings.
    
    Args:
        texts: List of text strings.
        
    Returns:
        2D numpy array of shape (len(texts), len(texts)) containing pairwise similarities.
    """
    if not texts:
        return np.array([])
    
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    # Normalize for cosine similarity (sklearn cosine_similarity handles this if inputs are normalized, 
    # but explicit normalization is safer for raw dot product logic if needed. 
    # sklearn's cosine_similarity computes dot(A, B.T) / (||A|| ||B||)
    return cosine_similarity(embeddings)

def is_wasted_call(similarity: float, threshold: float = 0.95) -> bool:
    """
    Determine if a pairwise comparison is considered 'wasted' based on similarity threshold.
    
    Args:
        similarity: Cosine similarity score between 0 and 1.
        threshold: Threshold above which a pair is considered near-duplicate (wasted).
        
    Returns:
        True if similarity > threshold, False otherwise.
    """
    return similarity > threshold

# --- NDCG Metrics ---

def calculate_ndcg_at_k(relevance_scores: List[int], k: int) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain at k.
    
    Args:
        relevance_scores: List of integer relevance scores (0 or 1 typically for BEIR).
        k: The cutoff rank.
        
    Returns:
        NDCG@k score.
    """
    if k <= 0 or not relevance_scores:
        return 0.0
    
    relevance_scores = relevance_scores[:k]
    if not relevance_scores:
        return 0.0
        
    dcg = 0.0
    idcg = 0.0
    
    # Calculate DCG
    for i, rel in enumerate(relevance_scores):
        dcg += (2 ** rel - 1) / np.log2(i + 2)  # i+2 because log2(1) is 0, rank starts at 1
        
    # Calculate IDCG (Ideal DCG)
    ideal_scores = sorted(relevance_scores, reverse=True)
    for i, rel in enumerate(ideal_scores):
        idcg += (2 ** rel - 1) / np.log2(i + 2)
        
    if idcg == 0:
        return 0.0
        
    return dcg / idcg

def calculate_ndcg_at_10(relevance_scores: List[int]) -> float:
    """Convenience wrapper for NDCG@10."""
    return calculate_ndcg_at_k(relevance_scores, 10)

# --- Data Loading Helpers ---

def load_beir_ground_truth(dataset_name: str, query_id: str) -> Dict[str, int]:
    """
    Load ground truth relevance judgments for a specific query from BEIR.
    Note: This is a placeholder for the actual BEIR loading logic which might vary by dataset.
    In a real implementation, this would interact with the BEIR library's Qrels structure.
    """
    # Placeholder: In a real scenario, this would fetch from a loaded Qrels object
    # For now, returning an empty dict to avoid crashes if called without BEIR setup
    logger.warning(f"Ground truth for {dataset_name}/{query_id} not implemented in this utility alone.")
    return {}

def load_results_from_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Load ranking results from a JSON file.
    Expected format: List of dicts with 'query_id', 'doc_id', 'score', 'rank'.
    """
    import json
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Results file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def aggregate_ndcg_scores(dataset_results: List[Dict[str, Any]]) -> float:
    """
    Aggregate NDCG@10 scores across multiple queries in a dataset.
    Assumes dataset_results is a list of per-query NDCG scores or objects containing them.
    """
    if not dataset_results:
        return 0.0
    # Assuming the input is a list of floats or objects with an 'ndcg' attribute
    scores = []
    for item in dataset_results:
        if isinstance(item, dict) and 'ndcg' in item:
            scores.append(item['ndcg'])
        elif isinstance(item, (int, float)):
            scores.append(float(item))
    
    if not scores:
        return 0.0
    return float(np.mean(scores))

# --- Statistical Testing ---

class StatisticalTestResult:
    def __init__(self, statistic: float, pvalue: float, method: str):
        self.statistic = statistic
        self.pvalue = pvalue
        self.method = method

class BonferroniResult:
    def __init__(self, corrected_pvalue: float, original_pvalue: float, alpha: float, significant: bool):
        self.corrected_pvalue = corrected_pvalue
        self.original_pvalue = original_pvalue
        self.alpha = alpha
        self.significant = significant

def wilcoxon_signed_rank_test(sample_a: List[float], sample_b: List[float]) -> StatisticalTestResult:
    """
    Perform Wilcoxon signed-rank test between two paired samples.
    
    Args:
        sample_a: List of values (e.g., NDCG scores for baseline).
        sample_b: List of values (e.g., NDCG scores for clustering-aided).
        
    Returns:
        StatisticalTestResult object.
    """
    if len(sample_a) != len(sample_b):
        raise ValueError("Samples must be of equal length for paired test.")
    if len(sample_a) < 2:
        raise ValueError("Need at least 2 samples for Wilcoxon test.")
        
    stat, pval = wilcoxon(sample_a, sample_b)
    return StatisticalTestResult(float(stat), float(pval), "Wilcoxon Signed-Rank")

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[BonferroniResult]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level.
        
    Returns:
        List of BonferroniResult objects.
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return []
        
    results = []
    for p in p_values:
        corrected_p = p * n_tests
        if corrected_p > 1.0:
            corrected_p = 1.0
        significant = corrected_p < alpha
        results.append(BonferroniResult(corrected_p, p, alpha, significant))
    return results

# --- Validation & Proxy Logic ---

def validate_proxy_accuracy(flagged_pairs: List[Tuple[str, str]], 
                            true_labels: List[bool], 
                            similarity_scores: List[float]) -> Dict[str, Any]:
    """
    Validate the accuracy of the cosine similarity proxy against ground truth labels.
    
    Args:
        flagged_pairs: List of (text_a, text_b) that were flagged.
        true_labels: List of booleans indicating if they were truly duplicates (ground truth).
        similarity_scores: List of similarity scores used for flagging.
        
    Returns:
        Dictionary with precision, recall, and accuracy metrics.
    """
    if not flagged_pairs:
        return {"precision": 0.0, "recall": 0.0, "accuracy": 0.0}
        
    # Threshold for flagging
    threshold = 0.95
    predicted_labels = [s > threshold for s in similarity_scores]
    
    tp = sum(1 for p, t in zip(predicted_labels, true_labels) if p and t)
    fp = sum(1 for p, t in zip(predicted_labels, true_labels) if p and not t)
    fn = sum(1 for p, t in zip(predicted_labels, true_labels) if not p and t)
    tn = sum(1 for p, t in zip(predicted_labels, true_labels) if not p and not t)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    accuracy = (tp + tn) / len(true_labels)
    
    return {
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn
    }

def calculate_dynamic_sample_size(total_flagged: int, upper_bound: int = 100) -> int:
    """
    Calculate dynamic sample size for LLM consensus validation.
    Formula: min(total_flagged, upper_bound)
    """
    if total_flagged <= 0:
        return 0
    return min(total_flagged, upper_bound)

def validate_jaccard_cosine_correlation(jaccard_scores: List[float], 
                                        cosine_scores: List[float]) -> float:
    """
    Calculate Pearson correlation between Jaccard and Cosine similarity scores.
    """
    if len(jaccard_scores) != len(cosine_scores) or len(jaccard_scores) < 2:
        return 0.0
    
    j_arr = np.array(jaccard_scores)
    c_arr = np.array(cosine_scores)
    
    # Pearson correlation
    corr_matrix = np.corrcoef(j_arr, c_arr)
    return float(corr_matrix[0, 1]) if not np.isnan(corr_matrix[0, 1]) else 0.0

def calculate_ndcg_for_clustering_aided_variant(relevance_scores: List[int], 
                                                cluster_filter_applied: bool) -> float:
    """
    Calculate NDCG@10 for the clustering-aided variant.
    This is a logical wrapper; the actual calculation is identical to standard NDCG,
    but this function serves as a marker in the pipeline for where the clustering logic was applied.
    """
    if not cluster_filter_applied:
        logger.warning("Cluster filter not applied, but NDCG calculated for clustering variant.")
    return calculate_ndcg_at_10(relevance_scores)

def main():
    """Entry point for direct execution (e.g., for quick tests)."""
    print("Metrics module loaded successfully.")
    print("Available functions: calculate_cosine_similarity_proxy, is_wasted_call, calculate_ndcg_at_10, ...")

if __name__ == "__main__":
    main()
