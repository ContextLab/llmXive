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
import os
import json
import logging

MODEL = None

def get_embedding_model() -> SentenceTransformer:
    global MODEL
    if MODEL is None:
        # CPU-light model as per task description
        MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    return MODEL

def calculate_cosine_similarity_proxy(emb1: np.ndarray, emb2: np.ndarray) -> float:
    return float(cosine_similarity([emb1], [emb2])[0][0])

def is_wasted_call(similarity: float, threshold: float = 0.95) -> bool:
    return similarity > threshold

def calculate_ndcg_at_k(scores: List[float], k: int) -> float:
    """Calculate NDCG@k."""
    if not scores:
        return 0.0
    
    def dcg(s, k):
        dcg_val = 0.0
        for i in range(min(k, len(s))):
            # Assuming scores are relevance labels (integers) or can be treated as such
            # If scores are floats, we use them directly
            rel = s[i]
            dcg_val += (2 ** rel - 1) / np.log2(i + 2)
        return dcg_val
    
    idcg = dcg(sorted(scores, reverse=True), k)
    dcg_val = dcg(scores, k)
    
    return dcg_val / idcg if idcg > 0 else 0.0

def calculate_ndcg_at_10(scores: List[float]) -> float:
    return calculate_ndcg_at_k(scores, 10)

def load_beir_ground_truth(dataset_name: str) -> Dict[str, Dict[str, int]]:
    # Placeholder for BEIR ground truth loading
    # In a real implementation, this would load from BEIR
    return {}

def load_results_from_json(filepath: str) -> Dict:
    import json
    with open(filepath, 'r') as f:
        return json.load(f)

def aggregate_ndcg_scores(results: List[Dict]) -> float:
    if not results:
        return 0.0
    return sum(r.get("ndcg_at_10", 0) for r in results) / len(results)

def calculate_wasted_call_ratios(comparisons: List[Dict]) -> float:
    if not comparisons:
        return 0.0
    wasted = sum(1 for c in comparisons if c.get("is_wasted", False))
    return wasted / len(comparisons)

def wilcoxon_signed_rank_test(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """Perform Wilcoxon signed-rank test."""
    if len(group1) != len(group2) or len(group1) == 0:
        return 0.0, 1.0
    try:
        stat, p_val = wilcoxon(group1, group2)
        return stat, p_val
    except Exception:
        return 0.0, 1.0

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    n = len(p_values)
    if n == 0:
        return []
    return [min(p * n, 1.0) for p in p_values]

def calculate_dynamic_sample_size(total_count: int, min_size: int = 10, percentage: float = 0.05) -> int:
    return max(min_size, int(total_count * percentage))

def validate_proxy_accuracy(proxy_labels: List[bool], true_labels: List[bool]) -> Dict:
    tp = sum(1 for p, t in zip(proxy_labels, true_labels) if p and t)
    fp = sum(1 for p, t in zip(proxy_labels, true_labels) if p and not t)
    fn = sum(1 for p, t in zip(proxy_labels, true_labels) if not p and t)
    tn = sum(1 for p, t in zip(proxy_labels, true_labels) if not p and not t)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    return {
        "precision": precision,
        "recall": recall,
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn}
    }

def validate_jaccard_cosine_correlation(jaccard_scores: List[float], cosine_scores: List[float]) -> float:
    if not jaccard_scores or not cosine_scores or len(jaccard_scores) != len(cosine_scores):
        return 0.0
    return float(np.corrcoef(jaccard_scores, cosine_scores)[0, 1])

def aggregate_flagged_pairs_from_log(log_path: str, output_path: str, threshold: float = 0.95) -> Dict:
    """
    T013 Implementation: Aggregate flagged pairs from comparison log.
    Reads data/processed/comparison_log.json, counts pairs with cosine_sim > threshold,
    and writes results to data/results/flagged_pairs_count.json.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Reading comparison log from {log_path}")
    
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Comparison log not found: {log_path}. T014 must run first.")
    
    wasted_count = 0
    total_pairs = 0
    
    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                total_pairs += 1
                cosine_sim = entry.get("cosine_sim", 0.0)
                if cosine_sim > threshold:
                    wasted_count += 1
            except json.JSONDecodeError:
                logger.warning(f"Skipping malformed JSON line in log: {line}")
    
    wasted_ratio = wasted_count / total_pairs if total_pairs > 0 else 0.0
    
    result = {
        "wasted_count": wasted_count,
        "total_pairs": total_pairs,
        "wasted_ratio": wasted_ratio
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Flagged pairs aggregation complete. Total: {total_pairs}, Wasted: {wasted_count}, Ratio: {wasted_ratio:.4f}")
    logger.info(f"Results written to {output_path}")
    
    return result

def calculate_sample_size_for_consensus(
    input_path: str,
    output_path: str,
    min_size: int = 10,
    percentage: float = 0.05
) -> Dict:
    """
    T013b Implementation: Calculate sample size for LLM consensus validation.
    
    Reads data/results/flagged_pairs_count.json to get the total flagged count.
    Calculates sample_size = max(min_size, int(total_count * percentage)).
    Handles edge case: if flagged_count is 0, sets sample_size to 0 and skip_validation to true.
    Writes result to data/results/sample_config.json.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Calculating sample size from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Flagged pairs count not found: {input_path}. T013 must run first.")
    
    with open(input_path, 'r') as f:
        flagged_data = json.load(f)
    
    flagged_count = flagged_data.get("wasted_count", 0)
    
    # Handle edge case: if flagged_count is 0
    if flagged_count == 0:
        result = {
            "sample_size": 0,
            "minimum_threshold": min_size,
            "percentage": percentage,
            "skip_validation": True
        }
    else:
        # Calculate sample size: max of min_size or 5% of total
        calculated_size = int(flagged_count * percentage)
        sample_size = max(min_size, calculated_size)
        
        result = {
            "sample_size": sample_size,
            "minimum_threshold": min_size,
            "percentage": percentage,
            "skip_validation": False
        }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Sample size calculation complete. Flagged count: {flagged_count}, Sample size: {result['sample_size']}, Skip: {result['skip_validation']}")
    logger.info(f"Results written to {output_path}")
    
    return result

def main():
    """Entry point for T013b execution."""
    logging.basicConfig(level=logging.INFO)
    input_path = "data/results/flagged_pairs_count.json"
    output_path = "data/results/sample_config.json"
    calculate_sample_size_for_consensus(input_path, output_path)

if __name__ == "__main__":
    main()
