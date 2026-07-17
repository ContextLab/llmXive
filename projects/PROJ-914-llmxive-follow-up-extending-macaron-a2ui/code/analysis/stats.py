"""
Statistical analysis utilities for the A2UI Latency Study.

Implements Benjamini-Hochberg FDR correction for multiple comparison tests
on alignment scores (FR-006, SC-004).
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

# Add parent directory to path for imports if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_processed_data_path, get_figures_path, ensure_dirs
from utils.logging import get_experiment_logger

logger = get_experiment_logger(__name__)


def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.

    This procedure controls the False Discovery Rate (expected proportion of
    false positives among rejected hypotheses).

    Args:
        p_values: List of raw p-values from hypothesis tests.
        alpha: Significance level (default 0.05).

    Returns:
        Tuple of:
            - List of booleans indicating which hypotheses are rejected (True = significant)
            - List of adjusted p-values (q-values)
    """
    if not p_values:
        return [], []

    n = len(p_values)
    indices = np.arange(1, n + 1)
    sorted_p_values = np.sort(p_values)

    # Calculate critical values: (i/n) * alpha
    critical_values = (indices / n) * alpha

    # Find the largest k such that p_(k) <= (k/n) * alpha
    # We iterate from largest to smallest to find the first (largest) that satisfies the condition
    rejected = np.zeros(n, dtype=bool)
    adjusted_p_values = np.ones(n)

    # Calculate adjusted p-values (q-values)
    # q_i = min( (n/j) * p_j for j >= i )  (monotonically increasing from largest p)
    # We compute this by iterating backwards
    min_q = 1.0
    for i in range(n - 1, -1, -1):
        q = min(1.0, (n / (i + 1)) * sorted_p_values[i])
        min_q = min(min_q, q)
        adjusted_p_values[i] = min_q

    # Determine rejections: p_i <= adjusted_threshold
    # Actually, standard BH: reject if p_(i) <= (i/n)*alpha
    # But we need to map back to original indices.
    # A simpler way: compare adjusted p-values to alpha
    sorted_rejected = adjusted_p_values <= alpha

    # Map back to original order
    # We need to sort indices to match sorted_p_values
    sort_indices = np.argsort(p_values)
    original_order_rejected = np.zeros(n, dtype=bool)
    original_order_adjusted = np.zeros(n)

    for sorted_idx, orig_idx in enumerate(sort_indices):
        original_order_rejected[orig_idx] = sorted_rejected[sorted_idx]
        original_order_adjusted[orig_idx] = adjusted_p_values[sorted_idx]

    return original_order_rejected.tolist(), original_order_adjusted.tolist()


def pairwise_ttest_with_fdr(
    group1_scores: List[float],
    group2_scores: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform an independent two-sample t-test and apply FDR correction.

    Args:
        group1_scores: Scores for the first group (e.g., Hybrid model).
        group2_scores: Scores for the second group (e.g., Generative baseline).
        alpha: Significance level.

    Returns:
        Dictionary containing:
            - t_statistic: t-value
            - p_value: raw p-value
            - fdr_rejected: boolean indicating if significant after FDR
            - fdr_adjusted_p: adjusted p-value
    """
    if not group1_scores or not group2_scores:
        raise ValueError("Both groups must have at least one score.")

    t_stat, p_val = scipy_stats.ttest_ind(group1_scores, group2_scores, equal_var=False)

    # Since we are doing a single comparison here, FDR correction is trivial,
    # but we structure it to allow extension for multiple comparisons later.
    # For a single test, adjusted p = raw p.
    is_rejected, adjusted_p = benjamini_hochberg_fdr([p_val], alpha)

    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "fdr_rejected": is_rejected[0],
        "fdr_adjusted_p": float(adjusted_p[0])
    }


def analyze_alignment_scores_by_density(
    metrics_file: Optional[str] = None,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Analyze alignment scores across different density levels and perform
    statistical comparisons with FDR correction.

    Args:
        metrics_file: Path to the metrics JSON file. If None, uses default path.
        alpha: Significance level for FDR.

    Returns:
        Dictionary with analysis results including p-values and FDR decisions.
    """
    if metrics_file is None:
        data_path = get_processed_data_path()
        # Assuming the simulation runner saves a metrics file here
        # The exact filename might vary, but typically 'simulation_metrics.json'
        metrics_file = str(Path(data_path) / "simulation_metrics.json")

    if not os.path.exists(metrics_file):
        raise FileNotFoundError(f"Metrics file not found: {metrics_file}")

    with open(metrics_file, 'r') as f:
        data = json.load(f)

    # Extract alignment scores by density
    # Assuming data structure: { "results": [ { "density": ..., "alignment_score": ... }, ... ] }
    # Or aggregated: { "by_density": { "1": [...], "3": [...] } }
    # We handle the common case where we have a list of runs

    scores_by_density = {}
    density_levels = sorted(set([1, 3, 5, 10]))

    for entry in data.get("results", []):
        density = entry.get("density")
        score = entry.get("alignment_score")
        if density is not None and score is not None:
            if density not in scores_by_density:
                scores_by_density[density] = []
            scores_by_density[density].append(score)

    # Ensure all density levels are present (even if empty)
    for d in density_levels:
        if d not in scores_by_density:
            scores_by_density[d] = []

    # Perform pairwise comparisons between consecutive densities
    # (1 vs 3), (3 vs 5), (5 vs 10)
    comparisons = []
    p_values = []

    density_pairs = [(1, 3), (3, 5), (5, 10)]

    for d1, d2 in density_pairs:
        s1 = scores_by_density.get(d1, [])
        s2 = scores_by_density.get(d2, [])

        if len(s1) < 2 or len(s2) < 2:
            logger.warning(f"Insufficient data for comparison {d1} vs {d2}. Skipping.")
            comparisons.append({
                "group1": d1,
                "group2": d2,
                "n1": len(s1),
                "n2": len(s2),
                "skipped": True,
                "reason": "Insufficient samples"
            })
            continue

        result = pairwise_ttest_with_fdr(s1, s2, alpha)
        comparisons.append({
            "group1": d1,
            "group2": d2,
            "n1": len(s1),
            "n2": len(s2),
            "t_statistic": result["t_statistic"],
            "p_value": result["p_value"],
            "fdr_rejected": result["fdr_rejected"],
            "fdr_adjusted_p": result["fdr_adjusted_p"],
            "skipped": False
        })
        p_values.append(result["p_value"])

    # Apply FDR correction to all collected p-values at once
    # (This is the correct way: collect all p-values, then correct)
    if p_values:
        rejected_flags, adjusted_p_values = benjamini_hochberg_fdr(p_values, alpha)
        # Update the comparisons with the FDR results
        for i, comp in enumerate(comparisons):
            if not comp.get("skipped", False) and i < len(rejected_flags):
                comp["fdr_rejected"] = rejected_flags[i]
                comp["fdr_adjusted_p"] = adjusted_p_values[i]

    return {
        "total_comparisons": len(comparisons),
        "significant_comparisons": sum(1 for c in comparisons if not c.get("skipped") and c["fdr_rejected"]),
        "comparisons": comparisons,
        "alpha": alpha,
        "method": "Benjamini-Hochberg FDR"
    }


def save_fdr_analysis_report(results: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save the FDR analysis results to a JSON file.

    Args:
        results: Dictionary containing analysis results.
        output_path: Path to save the report. If None, uses default.

    Returns:
        Path to the saved report.
    """
    if output_path is None:
        fig_path = get_figures_path()
        output_path = str(Path(fig_path) / "fdr_analysis_report.json")

    ensure_dirs(output_path)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"FDR analysis report saved to: {output_path}")
    return output_path


def main():
    """
    CLI entry point for running FDR analysis on alignment scores.
    """
    parser = argparse.ArgumentParser(
        description="Perform Benjamini-Hochberg FDR correction on alignment scores."
    )
    parser.add_argument(
        "--metrics-file",
        type=str,
        default=None,
        help="Path to the simulation metrics JSON file."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for FDR correction (default: 0.05)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save the FDR analysis report."
    )

    args = parser.parse_args()

    logger.info("Starting FDR analysis for alignment scores...")

    try:
        results = analyze_alignment_scores_by_density(
            metrics_file=args.metrics_file,
            alpha=args.alpha
        )

        output_path = save_fdr_analysis_report(results, args.output)

        # Print summary
        print(f"\nFDR Analysis Summary:")
        print(f"  Method: {results['method']}")
        print(f"  Alpha: {results['alpha']}")
        print(f"  Total Comparisons: {results['total_comparisons']}")
        print(f"  Significant (FDR-corrected): {results['significant_comparisons']}")

        for comp in results['comparisons']:
            if comp.get('skipped'):
                print(f"  {comp['group1']} vs {comp['group2']}: SKIPPED ({comp.get('reason')})")
            else:
                sig_str = "SIGNIFICANT" if comp['fdr_rejected'] else "Not Significant"
                print(f"  {comp['group1']} vs {comp['group2']}: p={comp['p_value']:.4f}, "
                      f"adj_p={comp['fdr_adjusted_p']:.4f} [{sig_str}]")

        logger.info("FDR analysis completed successfully.")

    except Exception as e:
        logger.error(f"FDR analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()