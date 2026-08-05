import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy.stats import wilcoxon

# Configure logging
logger = logging.getLogger(__name__)

def stratify_samples(
    fine_results: List[Dict[str, Any]],
    coarse_results: List[Dict[str, Any]],
    detection_status_key: str = "detection_status",
    exclude_statuses: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter out samples based on detection status to ensure valid statistical comparison.
    
    Args:
        fine_results: List of fine-grained strategy results.
        coarse_results: List of coarse-grained strategy results.
        detection_status_key: Key name for detection status in result dicts.
        exclude_statuses: List of statuses to exclude (e.g., 'fallback', 'zero_detection').
    
    Returns:
        Tuple of (filtered_fine, filtered_coarse) lists containing only valid samples.
    """
    if exclude_statuses is None:
        exclude_statuses = ["fallback", "zero_detection"]

    # Align samples by ID (assuming both lists are ordered or keyed by sample_id)
    # We assume the lists are already aligned by index as per the pipeline design
    # If they are not, a join by sample_id would be required.
    
    valid_fine = []
    valid_coarse = []
    
    for i, (f_item, c_item) in enumerate(zip(fine_results, coarse_results)):
        status = f_item.get(detection_status_key, "unknown")
        if status not in exclude_statuses:
            valid_fine.append(f_item)
            valid_coarse.append(c_item)
        else:
            logger.debug(f"Stratifying out sample {i} with status: {status}")

    if len(valid_fine) != len(valid_coarse):
        logger.warning("Mismatch in stratified sample counts. Check alignment logic.")
        
    return valid_fine, valid_coarse

def run_wilcoxon_test(
    fine_scores: List[float],
    coarse_scores: List[float]
) -> Dict[str, Any]:
    """
    Perform paired Wilcoxon signed-rank test to compare Fine vs. Coarse accuracy.
    
    Args:
        fine_scores: List of accuracy scores for the Fine strategy.
        coarse_scores: List of accuracy scores for the Coarse strategy.
    
    Returns:
        Dictionary containing 'statistic', 'pvalue', and 'n_samples'.
    """
    if len(fine_scores) != len(coarse_scores):
        raise ValueError("Fine and coarse score lists must have the same length for paired test.")
    
    if len(fine_scores) < 2:
        raise ValueError("At least 2 paired samples are required for Wilcoxon test.")

    # Convert to numpy arrays for scipy
    x = np.array(fine_scores)
    y = np.array(coarse_scores)

    try:
        statistic, p_value = wilcoxon(x, y)
        return {
            "statistic": float(statistic),
            "pvalue": float(p_value),
            "n_samples": len(fine_scores)
        }
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        return {
            "statistic": None,
            "pvalue": None,
            "n_samples": len(fine_scores),
            "error": str(e)
        }

def calculate_effect_size(
    fine_scores: List[float],
    coarse_scores: List[float],
    statistic: Optional[float] = None
) -> Dict[str, float]:
    """
    Calculate effect size metrics for the Wilcoxon test.
    
    Uses r = Z / sqrt(N) where Z is approximated from the statistic or calculated directly.
    Also calculates Cohen's d for the difference distribution as a supplementary metric.
    
    Args:
        fine_scores: List of fine strategy scores.
        coarse_scores: List of coarse strategy scores.
        statistic: Optional pre-computed Wilcoxon statistic (W).
    
    Returns:
        Dictionary with 'r' (rank-biserial correlation approximation) and 'cohens_d'.
    """
    if len(fine_scores) != len(coarse_scores) or len(fine_scores) < 2:
        return {"r": 0.0, "cohens_d": 0.0}

    x = np.array(fine_scores)
    y = np.array(coarse_scores)
    diffs = x - y
    n = len(diffs)

    # Calculate Cohen's d for the difference
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    if std_diff == 0:
        cohens_d = 0.0
    else:
        cohens_d = mean_diff / std_diff

    # Approximate Z for r calculation if statistic is not provided
    # For large N, Z approx = statistic / sqrt(n*(n+1)*(2*n+1)/6)
    # However, scipy returns the sum of ranks of positive differences (W).
    # A more robust way for r is to use the Z-score from the test if available.
    # Since scipy.stats.wilcoxon doesn't return Z directly in older versions,
    # we approximate Z using the normal approximation of the W statistic.
    
    if statistic is None:
        # Recalculate W if not provided
        from scipy.stats import rankdata
        # Combine and rank absolute differences, handling ties
        abs_diffs = np.abs(diffs)
        ranks = rankdata(abs_diffs, method='average')
        # Sum of ranks for positive differences
        W = np.sum(ranks[diffs > 0])
        statistic = W

    # Mean and Std of W under null hypothesis
    mu_W = n * (n + 1) / 4
    sigma_W = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    
    if sigma_W == 0:
        z_score = 0.0
    else:
        # Continuity correction
        if W > mu_W:
            W_corr = W - 0.5
        elif W < mu_W:
            W_corr = W + 0.5
        else:
            W_corr = W
        z_score = (W_corr - mu_W) / sigma_W

    # Effect size r = Z / sqrt(N)
    r = z_score / np.sqrt(n)

    return {
        "r": float(r),
        "cohens_d": float(cohens_d)
    }

def check_significance(
    p_value: Optional[float],
    alpha: float = 0.05,
    effect_size_r: Optional[float] = None
) -> Dict[str, Any]:
    """
    Determine statistical significance and interpret effect size.
    
    Args:
        p_value: The p-value from the Wilcoxon test.
        alpha: Significance threshold (default 0.05).
        effect_size_r: Optional r value for interpretation.
    
    Returns:
        Dictionary with 'is_significant', 'interpretation', and 'effect_magnitude'.
    """
    result = {
        "is_significant": False,
        "interpretation": "Inconclusive (p-value missing)",
        "effect_magnitude": "Unknown"
    }

    if p_value is None:
        return result

    result["is_significant"] = p_value < alpha
    
    if result["is_significant"]:
        result["interpretation"] = f"Significant difference detected (p={p_value:.4f} < {alpha})"
    else:
        result["interpretation"] = f"No significant difference (p={p_value:.4f} >= {alpha})"

    if effect_size_r is not None:
        abs_r = abs(effect_size_r)
        if abs_r < 0.1:
            magnitude = "negligible"
        elif abs_r < 0.3:
            magnitude = "small"
        elif abs_r < 0.5:
            magnitude = "medium"
        else:
            magnitude = "large"
        result["effect_magnitude"] = magnitude
        result["effect_size_r"] = float(effect_size_r)

    return result

def generate_comparison_report(
    fine_scores: List[float],
    coarse_scores: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Generate a comprehensive statistical comparison report.
    
    Args:
        fine_scores: List of fine strategy accuracy scores.
        coarse_scores: List of coarse strategy accuracy scores.
        alpha: Significance threshold.
    
    Returns:
        Dictionary containing full analysis results.
    """
    report = {
        "n_samples": len(fine_scores),
        "mean_fine": float(np.mean(fine_scores)) if fine_scores else 0.0,
        "std_fine": float(np.std(fine_scores, ddof=1)) if len(fine_scores) > 1 else 0.0,
        "mean_coarse": float(np.mean(coarse_scores)) if coarse_scores else 0.0,
        "std_coarse": float(np.std(coarse_scores, ddof=1)) if len(coarse_scores) > 1 else 0.0,
        "wilcoxon": {},
        "effect_size": {},
        "significance": {}
    }

    if len(fine_scores) >= 2:
        wilcoxon_result = run_wilcoxon_test(fine_scores, coarse_scores)
        report["wilcoxon"] = wilcoxon_result

        # Calculate effect size
        effect = calculate_effect_size(
            fine_scores, 
            coarse_scores, 
            statistic=wilcoxon_result.get("statistic")
        )
        report["effect_size"] = effect

        # Check significance
        sig_result = check_significance(
            wilcoxon_result.get("pvalue"),
            alpha=alpha,
            effect_size_r=effect.get("r")
        )
        report["significance"] = sig_result
    else:
        report["wilcoxon"] = {"error": "Insufficient samples (< 2)"}
        report["effect_size"] = {"error": "Insufficient samples"}
        report["significance"] = {"error": "Insufficient samples"}

    return report

def main():
    """
    Main entry point for stats module to run a demo or validation.
    In a real pipeline, this would be called by the evaluation orchestrator.
    """
    logger.info("Stats module initialized. Ready for analysis.")
    # Example usage would be here if run as a script, but typically called via API

if __name__ == "__main__":
    main()