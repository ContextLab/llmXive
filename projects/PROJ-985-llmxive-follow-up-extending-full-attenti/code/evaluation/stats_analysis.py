"""
Statistical Analysis Module for llmXive Pipeline.

Implements paired t-tests and Wilcoxon signed-rank tests to compare
Static Heuristic vs. Learned Sparse (RTPurbo) performance on a
per-document basis.
"""
import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INTERMEDIATE_DIR = DATA_DIR / "intermediate"
RESULTS_DIR = DATA_DIR / "results"

# Ensure output directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {file_path}: {e}")
        return None


def extract_document_scores_learned(learned_dir: Path) -> Dict[str, Dict[str, float]]:
    """
    Extract per-document scores from the learned baseline seed results.
    
    Input: Directory containing seed_{seed}_per_doc.json files.
    Output: Dict mapping document_id -> {metric_name: value}.
    
    Since T026a runs multiple seeds, we aggregate the scores per document
    by taking the mean across seeds for the primary metric (e.g., perplexity).
    This creates a single "Learned" score per document for the paired test.
    """
    doc_scores: Dict[str, Dict[str, List[float]]] = {}
    
    seed_files = list(learned_dir.glob("seed_*_per_doc.json"))
    if not seed_files:
        logger.warning(f"No seed files found in {learned_dir}")
        return {}
    
    logger.info(f"Found {len(seed_files)} seed files in {learned_dir}")
    
    for seed_file in seed_files:
        data = load_json(seed_file)
        if not data:
            continue
        
        # Assuming data is a list of {document_id, metric_name, value}
        for entry in data:
            doc_id = entry.get("document_id")
            metric_name = entry.get("metric_name", "perplexity")
            value = entry.get("value")
            
            if doc_id is None or value is None:
                continue
            
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"perplexity": [], "exact_match": []}
            
            if metric_name in doc_scores[doc_id]:
                doc_scores[doc_id][metric_name].append(value)
    
    # Aggregate: Compute mean across seeds for each document
    aggregated: Dict[str, Dict[str, float]] = {}
    for doc_id, metrics in doc_scores.items():
        aggregated[doc_id] = {}
        for metric, values in metrics.items():
            if values:
                aggregated[doc_id][metric] = float(np.mean(values))
            else:
                aggregated[doc_id][metric] = float('nan')
    
    return aggregated


def extract_document_scores_static(static_file: Path) -> Dict[str, Dict[str, float]]:
    """
    Extract per-document scores from the static heuristic results.
    
    Input: data/intermediate/static_per_document.json
    Output: Dict mapping document_id -> {metric_name: value}
    """
    data = load_json(static_file)
    if not data:
        logger.error(f"Failed to load static results from {static_file}")
        return {}
    
    # Assuming data is a list of {document_id, metric_name, value}
    doc_scores: Dict[str, Dict[str, float]] = {}
    for entry in data:
        doc_id = entry.get("document_id")
        metric_name = entry.get("metric_name", "perplexity")
        value = entry.get("value")
        
        if doc_id is None or value is None:
            continue
        
        if doc_id not in doc_scores:
            doc_scores[doc_id] = {}
        
        doc_scores[doc_id][metric_name] = float(value)
    
    return doc_scores


def perform_statistical_test(
    learned_scores: Dict[str, Dict[str, float]],
    static_scores: Dict[str, Dict[str, float]],
    metric: str = "perplexity"
) -> Dict[str, Any]:
    """
    Perform paired statistical tests (t-test and Wilcoxon) on document-level scores.
    
    Args:
        learned_scores: Dict[doc_id, {metric: value}] from Learned Baseline (aggregated).
        static_scores: Dict[doc_id, {metric: value}] from Static Heuristic.
        metric: The metric to compare (e.g., 'perplexity', 'exact_match').
    
    Returns:
        Dictionary containing test statistics and p-values.
    """
    # Identify common documents
    common_docs = set(learned_scores.keys()) & set(static_scores.keys())
    if not common_docs:
        logger.error("No common documents found between Learned and Static results.")
        return {"error": "No common documents", "n_pairs": 0}
    
    logger.info(f"Performing statistical test on {len(common_docs)} paired documents for metric: {metric}")
    
    learned_vals = []
    static_vals = []
    
    for doc_id in sorted(common_docs):
        l_val = learned_scores[doc_id].get(metric)
        s_val = static_scores[doc_id].get(metric)
        
        # Exclude pairs where either score is missing or NaN
        if l_val is None or s_val is None or np.isnan(l_val) or np.isnan(s_val):
            continue
        
        learned_vals.append(l_val)
        static_vals.append(s_val)
    
    n_pairs = len(learned_vals)
    if n_pairs < 2:
        logger.warning(f"Insufficient pairs ({n_pairs}) for statistical testing.")
        return {"error": "Insufficient pairs", "n_pairs": n_pairs}
    
    learned_arr = np.array(learned_vals)
    static_arr = np.array(static_vals)
    
    # Paired T-Test
    try:
        t_stat, t_pvalue = stats.ttest_rel(learned_arr, static_arr)
    except Exception as e:
        logger.error(f"T-test failed: {e}")
        t_stat, t_pvalue = None, None
    
    # Wilcoxon Signed-Rank Test
    try:
        w_stat, w_pvalue = stats.wilcoxon(learned_arr, static_arr)
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        w_stat, w_pvalue = None, None
    
    # Calculate effect size (Cohen's d for paired samples)
    diff = learned_arr - static_arr
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    cohens_d = mean_diff / std_diff if std_diff != 0 else 0.0
    
    return {
        "metric": metric,
        "n_pairs": n_pairs,
        "t_statistic": float(t_stat) if t_stat is not None else None,
        "t_pvalue": float(t_pvalue) if t_pvalue is not None else None,
        "wilcoxon_statistic": float(w_stat) if w_stat is not None else None,
        "wilcoxon_pvalue": float(w_pvalue) if w_pvalue is not None else None,
        "mean_difference": float(mean_diff),
        "std_difference": float(std_diff),
        "cohens_d": float(cohens_d),
        "learned_mean": float(np.mean(learned_arr)),
        "static_mean": float(np.mean(static_arr))
    }


def main():
    parser = argparse.ArgumentParser(description="Perform statistical significance tests on baseline results.")
    parser.add_argument(
        "--learned-dir",
        type=str,
        default=str(INTERMEDIATE_DIR / "baseline_seeds"),
        help="Directory containing seed_*_per_doc.json files (T026a output)."
    )
    parser.add_argument(
        "--static-file",
        type=str,
        default=str(INTERMEDIATE_DIR / "static_per_document.json"),
        help="Path to static_per_document.json (T027 output)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(RESULTS_DIR / "statistical_report.txt"),
        help="Output file path for the statistical report."
    )
    parser.add_argument(
        "--json-output",
        type=str,
        default=str(RESULTS_DIR / "statistical_report.json"),
        help="Output file path for JSON results."
    )
    
    args = parser.parse_args()
    
    learned_dir = Path(args.learned_dir)
    static_file = Path(args.static_file)
    
    if not learned_dir.exists():
        logger.error(f"Learned baseline directory not found: {learned_dir}")
        sys.exit(1)
    if not static_file.exists():
        logger.error(f"Static results file not found: {static_file}")
        sys.exit(1)
    
    # Extract scores
    learned_scores = extract_document_scores_learned(learned_dir)
    static_scores = extract_document_scores_static(static_file)
    
    if not learned_scores or not static_scores:
        logger.error("Failed to extract scores from input files.")
        sys.exit(1)
    
    # Perform tests for Perplexity and Exact Match
    metrics_to_test = ["perplexity", "exact_match"]
    results = {}
    
    for metric in metrics_to_test:
        logger.info(f"Testing metric: {metric}")
        test_result = perform_statistical_test(learned_scores, static_scores, metric)
        results[metric] = test_result
    
    # Generate Text Report
    report_lines = [
        "=" * 60,
        "Statistical Significance Analysis Report",
        "=" * 60,
        f"Input Learned Dir: {learned_dir}",
        f"Input Static File: {static_file}",
        "-" * 60,
        ""
    ]
    
    for metric, res in results.items():
        report_lines.append(f"METRIC: {metric.upper()}")
        if "error" in res:
            report_lines.append(f"  Error: {res['error']}")
            report_lines.append(f"  N Pairs: {res.get('n_pairs', 0)}")
        else:
            report_lines.append(f"  Sample Size (N): {res['n_pairs']}")
            report_lines.append(f"  Learned Mean: {res['learned_mean']:.4f}")
            report_lines.append(f"  Static Mean: {res['static_mean']:.4f}")
            report_lines.append(f"  Mean Difference (Learned - Static): {res['mean_difference']:.4f}")
            report_lines.append(f"  Cohen's d: {res['cohens_d']:.4f}")
            report_lines.append("")
            report_lines.append("  Paired T-Test:")
            if res['t_pvalue'] is not None:
                report_lines.append(f"    t-statistic: {res['t_statistic']:.4f}")
                report_lines.append(f"    p-value: {res['t_pvalue']:.6f}")
                sig = "YES" if res['t_pvalue'] < 0.05 else "NO"
                report_lines.append(f"    Significant (p < 0.05): {sig}")
            else:
                report_lines.append("    Failed to compute.")
            report_lines.append("")
            report_lines.append("  Wilcoxon Signed-Rank Test:")
            if res['wilcoxon_pvalue'] is not None:
                report_lines.append(f"    W-statistic: {res['wilcoxon_statistic']:.4f}")
                report_lines.append(f"    p-value: {res['wilcoxon_pvalue']:.6f}")
                sig = "YES" if res['wilcoxon_pvalue'] < 0.05 else "NO"
                report_lines.append(f"    Significant (p < 0.05): {sig}")
            else:
                report_lines.append("    Failed to compute.")
        report_lines.append("")
        report_lines.append("-" * 60)
    
    report_text = "\n".join(report_lines)
    
    # Write Text Report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    logger.info(f"Text report saved to: {output_path}")
    
    # Write JSON Report
    json_output_path = Path(args.json_output)
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"JSON report saved to: {json_output_path}")
    
    # Print summary to stdout
    print(report_text)


if __name__ == "__main__":
    main()