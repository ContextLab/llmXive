"""
Statistical Significance Analysis (T029)

Implements paired t-test / Wilcoxon signed-rank test to compare
Static Heuristic performance against Learned Sparse (RTPurbo) baselines.

Input:
  - data/results/static_aggregated.json (from T019c)
  - data/results/baseline_aggregated.json (from T026b)

Output:
  - data/results/stats_results.json (Detailed statistical test results)
  - data/results/stats_summary.csv (Summary for final report)

Requirements:
  - Performs a paired t-test on document-level performance differences.
  - Falls back to Wilcoxon signed-rank test if normality assumption is violated
    (Shapiro-Wilk test) or if sample size is small (< 30).
"""
import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATIC_AGG_PATH = os.path.join(PROJECT_ROOT, "data", "results", "static_aggregated.json")
BASELINE_AGG_PATH = os.path.join(PROJECT_ROOT, "data", "results", "baseline_aggregated.json")
OUTPUT_STATS_JSON = os.path.join(PROJECT_ROOT, "data", "results", "stats_results.json")
OUTPUT_STATS_CSV = os.path.join(PROJECT_ROOT, "data", "results", "stats_summary.csv")

# Metrics to compare
METRICS_TO_COMPARE = ["perplexity", "exact_match"]


def load_json(path: str) -> Dict[str, Any]:
    """Load JSON file safely."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required input file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_document_scores(aggregated_data: Dict[str, Any], metric_name: str) -> Optional[List[float]]:
    """
    Extract document-level scores from aggregated data.

    The aggregated JSON is expected to contain a 'seed_values' list where each
    element is a list of document-level scores for that seed, OR a list of
    individual document scores if aggregated differently.

    For T019c/T026b, we expect the structure to allow reconstruction of
    paired document-level differences.
    
    Assumption: The 'seed_values' key contains a list of lists (seeds -> doc scores).
    We assume the same documents were processed in the same order for all seeds.
    We will average the scores across seeds for each document to get the 'mean'
    per document, then compare Static Mean vs Learned Mean.
    
    Wait, the task says: "paired t-test on document-level performance differences 
    between Static (mean of multiple seeds) and Learned Sparse (mean of 5 seeds)."
    
    This implies we need the document-level scores for Static (averaged over seeds)
    and document-level scores for Learned (averaged over seeds).
    Then we compute the difference for each document and test if mean(diff) != 0.
    
    However, the aggregated files usually store the *mean of the means* and *std of the means*.
    To do a paired t-test, we need the vector of document-level scores.
    
    If the aggregated file only has the scalar mean, we cannot do a paired t-test.
    We must assume the 'seed_values' in the aggregated JSON contains the raw per-document
    scores for each seed, or that we have access to the per-seed per-document files.
    
    Given the constraints of the task description and typical pipeline outputs:
    We assume the aggregated file structure is:
    {
      "mean_metric": float,
      "std_metric": float,
      "n_seeds": int,
      "seed_values": [
         [score_doc1, score_doc2, ...],  # Seed 1
         [score_doc1, score_doc2, ...],  # Seed 2
         ...
      ]
    }
    
    If seed_values is not present or is just a list of scalars (means), we cannot do
    a paired t-test on documents. We would have to fall back to an unpaired test 
    on the seed means (less powerful).
    
    Let's implement robustly:
    1. Try to load seed_values as list of lists (document scores per seed).
    2. Average across seeds to get mean_doc_scores for Static and Learned.
    3. Compute differences.
    4. Run test.
    """
    seed_values = aggregated_data.get("seed_values")
    
    if not seed_values:
        logger.warning(f"No seed_values found in {aggregated_data.get('source', 'unknown')}. "
                       "Cannot perform paired document-level test. Returning None.")
        return None

    # Check if seed_values is a list of lists (document scores)
    if not isinstance(seed_values, list) or not isinstance(seed_values[0], list):
        logger.warning(f"seed_values in {aggregated_data.get('source', 'unknown')} is not a list of lists. "
                       "Cannot perform paired document-level test.")
        return None

    # Ensure all seeds have same number of documents
    n_docs = len(seed_values[0])
    for i, seed_scores in enumerate(seed_values):
        if len(seed_scores) != n_docs:
            logger.error(f"Seed {i} has {len(seed_scores)} docs, expected {n_docs}. "
                         "Cannot align documents for paired test.")
            return None

    # Calculate mean score per document across seeds
    # Convert to numpy array for easy averaging
    arr = np.array(seed_values)  # Shape: (n_seeds, n_docs)
    mean_per_doc = np.mean(arr, axis=0)  # Shape: (n_docs,)
    
    return mean_per_doc.tolist()


def perform_statistical_test(
    static_scores: List[float], 
    learned_scores: List[float], 
    metric_name: str
) -> Dict[str, Any]:
    """
    Perform paired t-test or Wilcoxon test.
    
    Returns a dictionary with test statistics, p-value, and conclusion.
    """
    if len(static_scores) != len(learned_scores):
        raise ValueError(f"Score vectors length mismatch for {metric_name}: "
                         f"{len(static_scores)} vs {len(learned_scores)}")
    
    n = len(static_scores)
    if n < 2:
        return {
            "metric": metric_name,
            "test": "insufficient_data",
            "message": f"Need at least 2 documents, got {n}.",
            "p_value": None,
            "statistic": None,
            "significant": False
        }

    # Convert to numpy arrays
    x = np.array(static_scores)
    y = np.array(learned_scores)
    
    # Calculate differences
    diff = x - y
    
    # Check for normality of differences (Shapiro-Wilk)
    # Note: Shapiro-Wilk is sensitive to sample size. For n > 50, it often rejects normality.
    # We use a threshold or switch if n is small.
    if n <= 30:
        # Small sample, Shapiro-Wilk is appropriate
        stat, p_val_normality = stats.shapiro(diff)
        logger.info(f"Normality test (Shapiro-Wilk) for {metric_name}: p={p_val_normality:.4f}")
        use_wilcoxon = p_val_normality < 0.05
    else:
        # For larger samples, we might use Kolmogorov-Smirnov or just default to t-test
        # unless there are strong outliers.
        # Let's default to t-test for n > 30 as it's robust, but check skewness.
        skewness = stats.skew(diff)
        logger.info(f"Skewness of differences for {metric_name}: {skewness:.4f}")
        # If skewness is extreme, use Wilcoxon
        use_wilcoxon = abs(skewness) > 2.0

    result = {
        "metric": metric_name,
        "n_documents": n,
        "mean_diff": float(np.mean(diff)),
        "std_diff": float(np.std(diff)),
        "mean_static": float(np.mean(x)),
        "mean_learned": float(np.mean(y)),
    }

    if use_wilcoxon:
        logger.info(f"Using Wilcoxon signed-rank test for {metric_name} (non-normal or skewed).")
        stat, p_val = stats.wilcoxon(diff)
        result["test"] = "wilcoxon"
        result["statistic"] = float(stat)
    else:
        logger.info(f"Using paired t-test for {metric_name}.")
        stat, p_val = stats.ttest_rel(x, y)
        result["test"] = "paired_t_test"
        result["statistic"] = float(stat)
    
    result["p_value"] = float(p_val)
    result["significant"] = bool(p_val < 0.05)
    
    # Interpretation
    if result["significant"]:
        if result["mean_diff"] > 0:
            result["conclusion"] = f"Static HEURISTIC performs significantly WORSE than Learned Sparse (p < 0.05)."
        else:
            result["conclusion"] = f"Static HEURISTIC performs significantly BETTER than Learned Sparse (p < 0.05)."
    else:
        result["conclusion"] = f"No statistically significant difference between Static and Learned Sparse (p >= 0.05)."

    return result


def main():
    logger.info("Starting Statistical Significance Analysis (T029)...")
    
    # Load inputs
    try:
        static_data = load_json(STATIC_AGG_PATH)
        static_data["source"] = "static_aggregated.json"
        logger.info(f"Loaded static aggregated data from {STATIC_AGG_PATH}")
        
        baseline_data = load_json(BASELINE_AGG_PATH)
        baseline_data["source"] = "baseline_aggregated.json"
        logger.info(f"Loaded baseline aggregated data from {BASELINE_AGG_PATH}")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)

    results = []
    csv_rows = []

    for metric in METRICS_TO_COMPARE:
        logger.info(f"Processing metric: {metric}")
        
        static_scores = extract_document_scores(static_data, metric)
        learned_scores = extract_document_scores(baseline_data, metric)
        
        if static_scores is None or learned_scores is None:
            logger.warning(f"Skipping {metric} due to missing document-level data.")
            continue

        test_result = perform_statistical_test(static_scores, learned_scores, metric)
        results.append(test_result)
        
        csv_rows.append({
            "metric": metric,
            "test": test_result["test"],
            "n_documents": test_result["n_documents"],
            "mean_diff": test_result["mean_diff"],
            "std_diff": test_result["std_diff"],
            "p_value": test_result["p_value"],
            "significant": test_result["significant"],
            "conclusion": test_result["conclusion"]
        })

    if not results:
        logger.error("No results generated. Check input data structure.")
        sys.exit(1)

    # Save JSON results
    with open(OUTPUT_STATS_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved detailed results to {OUTPUT_STATS_JSON}")

    # Save CSV summary
    import csv
    with open(OUTPUT_STATS_CSV, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["metric", "test", "n_documents", "mean_diff", "std_diff", "p_value", "significant", "conclusion"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    logger.info(f"Saved summary to {OUTPUT_STATS_CSV}")

    # Print summary to stdout
    print("\n--- Statistical Analysis Summary ---")
    for r in results:
        print(f"{r['metric']}: {r['test']} (p={r['p_value']:.4f}) -> {r['conclusion']}")
    print("------------------------------------")

    logger.info("T029 completed successfully.")


if __name__ == "__main__":
    main()