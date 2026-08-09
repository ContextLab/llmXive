import os
import sys
import json
import logging
import argparse
from typing import List, Dict, Tuple, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import wilcoxon
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global model cache
_embedding_model = None

class StatisticalDegeneracyWarning(UserWarning):
    """Warning raised when statistical tests encounter zero variance or degenerate inputs."""
    pass

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: all-MiniLM-L6-v2")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

def calculate_cosine_similarity(text1: str, text2: str) -> float:
    """Calculate cosine similarity between two text strings."""
    model = get_embedding_model()
    embeddings = model.encode([text1, text2], convert_to_numpy=True)
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(sim)

def calculate_cosine_similarity_proxy(doc1_text: str, doc2_text: str) -> float:
    """Wrapper for calculate_cosine_similarity to match expected signature."""
    return calculate_cosine_similarity(doc1_text, doc2_text)

def is_wasted_call(cosine_sim: float, threshold: float = 0.95) -> bool:
    """Determine if a pair is considered 'wasted' based on cosine similarity threshold."""
    return cosine_sim > threshold

def calculate_ndcg_at_k(relevances: List[float], k: int) -> float:
    """Calculate NDCG@k for a list of relevance scores."""
    if not relevances or k <= 0:
        return 0.0
    
    dcg = 0.0
    idcg = 0.0
    
    # Calculate DCG
    for i, rel in enumerate(relevances[:k]):
        if rel > 0:
            dcg += rel / np.log2(i + 2)
    
    # Calculate IDCG
    sorted_relevances = sorted(relevances, reverse=True)
    for i, rel in enumerate(sorted_relevances[:k]):
        if rel > 0:
            idcg += rel / np.log2(i + 2)
    
    if idcg == 0:
        return 0.0
    return dcg / idcg

def calculate_ndcg_at_10(relevances: List[float]) -> float:
    """Calculate NDCG@10."""
    return calculate_ndcg_at_k(relevances, 10)

def load_beir_ground_truth(dataset_name: str, split: str = "test") -> Dict[str, Dict[str, int]]:
    """Load BEIR ground truth (qrels) for a dataset."""
    try:
        from beir import util
        from beir.datasets.data_loader import GenericDataLoader
        
        url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset_name}.zip"
        data_path = util.download_and_unzip(url, "beir_data")
        loader = GenericDataLoader(data_path)
        _, _, qrels = loader.load(split=split)
        return qrels
    except Exception as e:
        logger.error(f"Failed to load BEIR ground truth for {dataset_name}: {e}")
        raise

def load_results_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Load results from a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def aggregate_ndcg_scores(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Aggregate NDCG scores from a list of results."""
    if not results:
        return {"mean": 0.0, "std": 0.0}
    
    scores = [r.get("ndcg@10", 0.0) for r in results if "ndcg@10" in r]
    if not scores:
        return {"mean": 0.0, "std": 0.0}
    
    return {
        "mean": float(np.mean(scores)),
        "std": float(np.std(scores))
    }

def calculate_wasted_call_ratios(comparison_logs: List[Dict[str, Any]], threshold: float = 0.95) -> Dict[str, float]:
    """Calculate wasted call ratios from comparison logs."""
    if not comparison_logs:
        return {"ratio": 0.0, "count": 0, "total": 0}
    
    wasted_count = sum(1 for log in comparison_logs if log.get("cosine_sim", 0) > threshold)
    total_count = len(comparison_logs)
    
    return {
        "ratio": wasted_count / total_count if total_count > 0 else 0.0,
        "count": wasted_count,
        "total": total_count
    }

def wilcoxon_signed_rank_test(group1: List[float], group2: List[float]) -> Dict[str, float]:
    """Perform Wilcoxon signed-rank test on two groups."""
    if len(group1) != len(group2):
        raise ValueError("Groups must have the same length for paired test")
    
    if len(group1) == 0:
        raise ValueError("Groups cannot be empty")
    
    # Check for zero variance
    if len(set(group1)) == 1 and len(set(group2)) == 1:
        logger.warning("StatisticalDegeneracyWarning: Zero variance detected in both groups.")
        return {"statistic": 0.0, "pvalue": 1.0, "warning": "zero_variance"}
    
    try:
        stat, pval = wilcoxon(group1, group2)
        return {"statistic": float(stat), "pvalue": float(pval)}
    except Exception as e:
        logger.warning(f"Wilcoxon test failed: {e}. Returning degenerate result.")
        return {"statistic": 0.0, "pvalue": 1.0, "warning": str(e)}

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """Apply Bonferroni correction to a list of p-values."""
    n = len(p_values)
    if n == 0:
        return {"corrected_p_values": [], "alpha": alpha, "n_tests": 0}
    
    corrected_p_values = [min(p * n, 1.0) for p in p_values]
    significant = [p < alpha for p in corrected_p_values]
    
    return {
        "corrected_p_values": corrected_p_values,
        "alpha": alpha,
        "n_tests": n,
        "significant": significant
    }

def calculate_dynamic_sample_size(flagged_count: int, min_threshold: int = 10, percentage: float = 0.05) -> int:
    """
    Calculate sample size for LLM consensus validation.
    Sample size = max(min_threshold, percentage * flagged_count).
    If flagged_count is 0, return 0.
    """
    if flagged_count <= 0:
        return 0
    return max(min_threshold, int(percentage * flagged_count))

def validate_proxy_accuracy(proxy_labels: List[bool], ground_truth_labels: List[bool]) -> Dict[str, Any]:
    """Validate proxy accuracy against ground truth."""
    if len(proxy_labels) != len(ground_truth_labels):
        raise ValueError("Proxy and ground truth lists must have the same length")
    
    tp = sum(1 for p, g in zip(proxy_labels, ground_truth_labels) if p and g)
    tn = sum(1 for p, g in zip(proxy_labels, ground_truth_labels) if not p and not g)
    fp = sum(1 for p, g in zip(proxy_labels, ground_truth_labels) if p and not g)
    fn = sum(1 for p, g in zip(proxy_labels, ground_truth_labels) if not p and g)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    return {
        "precision": precision,
        "recall": recall,
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn}
    }

def validate_jaccard_cosine_correlation(jaccard_scores: List[float], cosine_scores: List[float]) -> Dict[str, float]:
    """Validate correlation between Jaccard and cosine similarity scores."""
    if len(jaccard_scores) != len(cosine_scores) or len(jaccard_scores) == 0:
        return {"correlation": 0.0, "pvalue": 1.0}
    
    corr, pval = np.corrcoef(jaccard_scores, cosine_scores)
    return {"correlation": float(corr[0][1]), "pvalue": float(pval[0][1])}

def calculate_cosine_similarity_proxy_from_logs(logs: List[Dict[str, Any]], threshold: float = 0.95) -> List[Dict[str, Any]]:
    """Extract proxy labels from comparison logs."""
    return [
        {
            "pair_id": log.get("pair_id"),
            "proxy_label": log.get("cosine_sim", 0) > threshold,
            "cosine_sim": log.get("cosine_sim", 0)
        }
        for log in logs
    ]

def calculate_sample_config(flagged_count: int, min_threshold: int = 10, percentage: float = 0.05) -> Dict[str, Any]:
    """
    Calculate and return the sample configuration for LLM consensus validation.
    
    Args:
        flagged_count: Total number of flagged pairs (cosine_sim > 0.95)
        min_threshold: Minimum sample size (default 10)
        percentage: Percentage of flagged count to sample (default 0.05)
        
    Returns:
        Dictionary with sample_size, minimum_threshold, percentage, and skip_validation flag.
    """
    sample_size = calculate_dynamic_sample_size(flagged_count, min_threshold, percentage)
    skip_validation = (sample_size == 0)
    
    return {
        "sample_size": sample_size,
        "minimum_threshold": min_threshold,
        "percentage": percentage,
        "skip_validation": skip_validation
    }

def run_sample_size_calculation(flagged_count_file: str, output_file: str):
    """
    Execute sample size calculation for LLM consensus validation.
    Reads flagged count from flagged_count_file and writes config to output_file.
    """
    logger.info(f"Starting sample size calculation. Input: {flagged_count_file}, Output: {output_file}")
    
    if not os.path.exists(flagged_count_file):
        logger.error(f"Flagged count file not found: {flagged_count_file}")
        raise FileNotFoundError(f"Flagged count file not found: {flagged_count_file}")
    
    with open(flagged_count_file, 'r') as f:
        flagged_data = json.load(f)
    
    flagged_count = flagged_data.get("wasted_count", 0)
    logger.info(f"Total flagged count: {flagged_count}")
    
    sample_config = calculate_sample_config(flagged_count)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    logger.info(f"Sample config written to {output_file}: {sample_config}")
    return sample_config

def main():
    parser = argparse.ArgumentParser(description="Metrics and validation utilities")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Sample size calculation command
    sample_parser = subparsers.add_parser("calc_sample_size", help="Calculate sample size for consensus validation")
    sample_parser.add_argument("--input", required=True, help="Path to flagged_pairs_count.json")
    sample_parser.add_argument("--output", required=True, help="Path to write sample_config.json")
    
    args = parser.parse_args()
    
    if args.command == "calc_sample_size":
        run_sample_size_calculation(args.input, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
