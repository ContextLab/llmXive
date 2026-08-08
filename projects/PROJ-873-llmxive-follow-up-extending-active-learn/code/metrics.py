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

class StatisticalDegeneracyWarning(UserWarning):
    """Raised when statistical tests encounter zero variance."""
    pass

def get_embedding_model():
    """Get the embedding model."""
    return SentenceTransformer('all-MiniLM-L6-v2')

def calculate_cosine_similarity_proxy(embeddings: List[np.ndarray]) -> List[List[float]]:
    """Calculate cosine similarity proxy for embeddings."""
    return cosine_similarity(embeddings).tolist()

def is_wasted_call(cosine_sim: float, threshold: float = 0.95) -> bool:
    """Determine if a call is wasted based on cosine similarity."""
    return cosine_sim > threshold

def calculate_ndcg_at_k(scores: List[float], k: int) -> float:
    """Calculate NDCG@k."""
    dcg = 0.0
    idcg = 0.0
    for i, score in enumerate(scores[:k]):
        dcg += score / np.log2(i + 2)
        idcg += 1.0 / np.log2(i + 2)
    return dcg / idcg if idcg > 0 else 0.0

def calculate_ndcg_at_10(scores: List[float]) -> float:
    """Calculate NDCG@10."""
    return calculate_ndcg_at_k(scores, 10)

def load_beir_ground_truth(dataset: str) -> Dict[str, Dict[str, int]]:
    """Load BEIR ground truth qrels."""
    from beir.datasets.data_loader import GenericDataLoader
    from beir import util
    from config import get_config

    config = get_config()
    out_dir = os.path.join(config.data_dir, "beir_data")
    url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset}.zip"
    data_path = util.download_and_unzip(url, out_dir)
    _, _, qrels = GenericDataLoader(data_path).load(split="test")
    return qrels

def load_results_from_json(path: str) -> List[Dict[str, Any]]:
    """Load results from JSON file."""
    with open(path, "r") as f:
        return json.load(f)

def aggregate_ndcg_scores(results: List[Dict[str, Any]]) -> List[float]:
    """Aggregate NDCG scores from results."""
    return [r.get("ndcg_at_10", 0.0) for r in results]

def calculate_wasted_call_ratios(logs: List[Dict[str, Any]], threshold: float = 0.95) -> Dict[str, float]:
    """Calculate wasted call ratios."""
    wasted_count = sum(1 for log in logs if log.get("cosine_sim", 0) > threshold)
    total_count = len(logs)
    return {
        "wasted_count": wasted_count,
        "total_count": total_count,
        "wasted_ratio": wasted_count / total_count if total_count > 0 else 0.0
    }

def wilcoxon_signed_rank_test(group1: List[float], group2: List[float]) -> Dict[str, Any]:
    """Perform Wilcoxon signed-rank test with zero-variance handling."""
    if len(group1) != len(group2):
        raise ValueError("Groups must have the same length.")

    # Check for zero variance
    if np.std(group1) == 0 or np.std(group2) == 0:
        logger.warning(StatisticalDegeneracyWarning("Zero variance detected in one or both groups."))
        return {
            "statistic": 0.0,
            "pvalue": 1.0,
            "degeneracy_warning": True
        }

    statistic, pvalue = wilcoxon(group1, group2)
    return {
        "statistic": float(statistic),
        "pvalue": float(pvalue),
        "degeneracy_warning": False
    }

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """Apply Bonferroni correction to p-values."""
    n = len(p_values)
    corrected_p_values = [p * n for p in p_values]
    return [
        {"pvalue": p, "corrected_pvalue": min(cp, 1.0), "significant": min(cp, 1.0) < alpha}
        for p, cp in zip(p_values, corrected_p_values)
    ]

def calculate_dynamic_sample_size(flagged_count: int, minimum_threshold: int = 10, percentage: float = 0.05) -> int:
    """Calculate dynamic sample size based on flagged count."""
    return max(minimum_threshold, int(flagged_count * percentage))

def validate_proxy_accuracy(proxy_labels: List[bool], ground_truth: List[bool]) -> Dict[str, int]:
    """Validate proxy accuracy against ground truth."""
    tp = sum(1 for p, g in zip(proxy_labels, ground_truth) if p and g)
    tn = sum(1 for p, g in zip(proxy_labels, ground_truth) if not p and not g)
    fp = sum(1 for p, g in zip(proxy_labels, ground_truth) if p and not g)
    fn = sum(1 for p, g in zip(proxy_labels, ground_truth) if not p and g)
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn}

def validate_jaccard_cosine_correlation(jaccard_scores: List[float], cosine_scores: List[float]) -> float:
    """Validate correlation between Jaccard and cosine similarity."""
    correlation = np.corrcoef(jaccard_scores, cosine_scores)[0, 1]
    return correlation

def main():
    pass

if __name__ == "__main__":
    main()