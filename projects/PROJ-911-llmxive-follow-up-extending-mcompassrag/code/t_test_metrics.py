"""
Task T029: Implement paired t-test for precision metrics and calculate
the ratio of Graph Recall@10 to Neural Recall@10.

This script reads retrieval scores from T024 (retrieval_scores.csv) and
topological features from T016/T023 (retrieved_features.csv), matches them
by query/document, and performs:
1. Paired t-test on Recall@10 between Graph-based and Neural-based retrieval.
2. Calculation of the ratio: Graph Recall@10 / Neural Recall@10.
3. Logging of whether the ratio meets the ≥ 0.70 threshold.
4. Writing results to data/results/metrics.json.

Dependencies:
- data/results/retrieval_scores.csv (from T022/T024)
- data/results/retrieved_features.csv (from T023)
- code/config.py for paths
"""
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

from code.config import RESULTS_DIR, DATA_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def load_retrieval_scores() -> List[Dict[str, Any]]:
    """
    Load retrieval scores from data/results/retrieval_scores.csv.
    Expected columns: query_id, doc_id, method, recall_at_k (or similar).
    We assume the file contains rows for both 'graph' and 'neural' methods.
    """
    scores_path = RESULTS_DIR / "retrieval_scores.csv"
    if not scores_path.exists():
        raise FileNotFoundError(f"Retrieval scores file not found: {scores_path}")

    scores = []
    with open(scores_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure numeric conversion
            try:
                row['recall'] = float(row.get('recall_at_10', row.get('recall', 0.0)))
            except (ValueError, TypeError):
                row['recall'] = 0.0
            scores.append(row)

    logger.info(f"Loaded {len(scores)} retrieval score rows from {scores_path}")
    return scores

def load_retrieved_features() -> List[Dict[str, Any]]:
    """
    Load topological features for retrieved documents from data/results/retrieved_features.csv.
    This file should contain features for documents that were retrieved by the TF-IDF ranking.
    We use this to ensure we are comparing the same set of documents for both methods if needed,
    but primarily we rely on retrieval_scores.csv for the Recall values.
    """
    features_path = RESULTS_DIR / "retrieved_features.csv"
    if not features_path.exists():
        logger.warning(f"Retrieved features file not found: {features_path}. Proceeding without it.")
        return []

    features = []
    with open(features_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            features.append(row)

    logger.info(f"Loaded {len(features)} feature rows from {features_path}")
    return features

def aggregate_recall_by_method_and_query(scores: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Aggregate Recall@10 scores by query_id and method.
    Returns: {query_id: {method: recall_value}}
    """
    aggregated = {}
    for row in scores:
        qid = row.get('query_id')
        method = row.get('method', 'unknown')
        recall = row.get('recall', 0.0)

        if qid is None:
            continue

        if qid not in aggregated:
            aggregated[qid] = {}

        # If multiple rows for same query/method, we might need to decide how to aggregate.
        # For this task, we assume one row per query/method or take the last one.
        # A more robust approach would be to average, but let's assume single entry per query/method.
        aggregated[qid][method] = recall

    return aggregated

def perform_paired_t_test(aggregated_data: Dict[str, Dict[str, float]]) -> Tuple[float, float, Dict[str, float]]:
    """
    Perform a paired t-test between Graph and Neural Recall@10 scores.
    Returns: (t_statistic, p_value, summary_stats)
    """
    graph_scores = []
    neural_scores = []
    query_ids = []

    for qid, methods in aggregated_data.items():
        if 'graph' in methods and 'neural' in methods:
            graph_scores.append(methods['graph'])
            neural_scores.append(methods['neural'])
            query_ids.append(qid)

    if len(graph_scores) < 2:
        logger.error("Not enough paired data points (need at least 2) to perform t-test.")
        return 0.0, 1.0, {"graph_mean": 0.0, "neural_mean": 0.0, "pairs": 0}

    graph_array = np.array(graph_scores)
    neural_array = np.array(neural_scores)

    # Paired t-test
    t_stat, p_val = stats.ttest_rel(graph_array, neural_array)

    summary = {
        "graph_mean": float(np.mean(graph_array)),
        "neural_mean": float(np.mean(neural_array)),
        "pairs": len(graph_scores),
        "graph_std": float(np.std(graph_array)),
        "neural_std": float(np.std(neural_array))
    }

    return float(t_stat), float(p_val), summary

def calculate_ratio(aggregated_data: Dict[str, Dict[str, float]]) -> Tuple[float, bool]:
    """
    Calculate the ratio of Graph Recall@10 to Neural Recall@10.
    Returns: (average_ratio, meets_threshold)
    Threshold: ≥ 0.70
    """
    ratios = []
    for qid, methods in aggregated_data.items():
        if 'graph' in methods and 'neural' in methods:
            graph_recall = methods['graph']
            neural_recall = methods['neural']
            if neural_recall > 0:
                ratio = graph_recall / neural_recall
                ratios.append(ratio)
            elif graph_recall == 0:
                # If both are zero, ratio is undefined, but we can treat it as 1.0 or skip.
                # Let's skip to avoid division by zero or misleading 0/0.
                continue
            else:
                # Neural is 0 but Graph is not -> infinite ratio, skip or handle as special case
                continue

    if not ratios:
        logger.warning("No valid ratios could be calculated (no pairs with non-zero neural recall).")
        return 0.0, False

    avg_ratio = float(np.mean(ratios))
    meets_threshold = avg_ratio >= 0.70

    return avg_ratio, meets_threshold

def run_pipeline() -> Dict[str, Any]:
    """
    Main pipeline for T029: Load data, run t-test, calculate ratio, save metrics.
    """
    logger.info("Starting T029 pipeline: Paired t-test and ratio calculation.")

    # Load data
    try:
        scores = load_retrieval_scores()
        # We don't strictly need retrieved_features for this specific task,
        # but loading it ensures we have the data context if needed later.
        _ = load_retrieved_features()
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        return {"error": str(e)}

    # Aggregate
    aggregated = aggregate_recall_by_method_and_query(scores)

    if not aggregated:
        logger.error("No valid query-method pairs found in retrieval scores.")
        return {"error": "No valid data found"}

    # Paired t-test
    t_stat, p_val, summary_stats = perform_paired_t_test(aggregated)
    logger.info(f"T-test: t={t_stat:.4f}, p={p_val:.4f}")

    # Ratio calculation
    avg_ratio, meets_threshold = calculate_ratio(aggregated)
    logger.info(f"Average Graph/Neural Recall@10 ratio: {avg_ratio:.4f} (Threshold ≥ 0.70: {'PASS' if meets_threshold else 'FAIL'})")

    # Prepare results
    results = {
        "task_id": "T029",
        "description": "Paired t-test for precision metrics and Graph/Neural Recall@10 ratio",
        "t_test": {
            "t_statistic": t_stat,
            "p_value": p_val,
            "summary": summary_stats
        },
        "ratio": {
            "average_graph_neural_ratio": avg_ratio,
            "threshold": 0.70,
            "meets_threshold": meets_threshold
        },
        "status": "completed"
    }

    # Save to metrics.json
    metrics_path = RESULTS_DIR / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Metrics saved to {metrics_path}")

    return results

def main():
    """Entry point for the script."""
    results = run_pipeline()
    if "error" in results:
        logger.error(f"Pipeline failed: {results['error']}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
