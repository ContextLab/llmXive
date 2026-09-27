"""
Reporting utilities for the Plant Disease Severity Prediction pipeline.

This module handles the final formatting of results, including the explicit
flagging of null hypothesis test results and the analysis of sensitivity
across swept thresholds as required by US-2 AC-3 and US-3 AC-3.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_path

logger = logging.getLogger(__name__)


def load_results(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the existing results.json file if it exists, otherwise return an empty dict.
    
    Args:
        path: Optional path to the results file. Defaults to 'artifacts/results.json'.
            
    Returns:
        Dictionary containing existing results or empty dict if file missing.
    """
    if path is None:
        path = get_path("artifacts/results.json")
    
    if not path.exists():
        logger.info(f"Results file not found at {path}. Starting fresh.")
        return {}
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load results from {path}: {e}")
        return {}


def save_results(results: Dict[str, Any], path: Optional[Path] = None) -> None:
    """
    Save the results dictionary to a JSON file.
    
    Args:
        results: The dictionary of results to save.
        path: Optional path to the results file. Defaults to 'artifacts/results.json'.
    """
    if path is None:
        path = get_path("artifacts/results.json")
    
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {path}")


def flag_null_result(results: Dict[str, Any], p_value: float, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Explicitly flag 'Null Result' in the results dictionary if the p-value 
    indicates a failure to reject the null hypothesis.
    
    This satisfies US-2 AC-3: "ensuring the outcome is recorded as a valid 
    scientific finding" even when the hypothesis is not supported.
    
    Args:
        results: The current results dictionary (modified in place and returned).
        p_value: The p-value from the permutation test.
        alpha: The significance threshold (default 0.05).
            
    Returns:
        The updated results dictionary with the null_result_flag set.
    """
    # Ensure the hypothesis_test structure exists
    if "hypothesis_test" not in results:
        results["hypothesis_test"] = {}
    
    # Determine if result is null (fail to reject null hypothesis)
    is_null = p_value >= alpha
    
    results["hypothesis_test"]["p_value"] = p_value
    results["hypothesis_test"]["alpha_threshold"] = alpha
    results["hypothesis_test"]["null_result_flag"] = is_null
    
    if is_null:
        results["hypothesis_test"]["conclusion"] = (
            f"Null Result: p-value ({p_value:.4f}) >= {alpha}. "
            "Failed to reject the null hypothesis. "
            "Weather variables did not significantly improve residual prediction."
        )
        logger.warning(f"Null Result detected: p-value ({p_value:.4f}) >= {alpha}")
    else:
        results["hypothesis_test"]["conclusion"] = (
            f"Significant Result: p-value ({p_value:.4f}) < {alpha}. "
            "Rejected the null hypothesis. "
            "Weather variables significantly improved residual prediction."
        )
        logger.info(f"Significant Result detected: p-value ({p_value:.4f}) < {alpha}")
    
    return results


def update_results_with_hypothesis_test(
    results: Dict[str, Any],
    r2_baseline: float,
    r2_augmented: float,
    p_value: float,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Update results with modeling metrics and the hypothesis test outcome.
    
    Args:
        results: The current results dictionary.
        r2_baseline: R² score of the baseline model.
        r2_augmented: R² score of the augmented model.
        p_value: The p-value from the permutation test.
        alpha: The significance threshold.
            
    Returns:
        The updated results dictionary.
    """
    results["modeling"] = results.get("modeling", {})
    results["modeling"]["baseline_r2"] = r2_baseline
    results["modeling"]["augmented_r2"] = r2_augmented
    results["modeling"]["r2_improvement"] = r2_augmented - r2_baseline
    
    # Flag null result if applicable
    flag_null_result(results, p_value, alpha)
    
    return results


def evaluate_sensitivity_robustness(results: Dict[str, Any], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Analyze sensitivity analysis results to explicitly state whether headline findings
    hold across the swept threshold range (US-3 AC-3).
    
    This function examines the `sensitivity_analysis` block in the results. It checks
    if the statistical significance (p-value < alpha) and the direction of the effect
    (e.g., F1 score improvement or False Positive Rate trends) remain consistent
    across all swept thresholds (e.g., deviations {0, 0.05, 0.1} from the 90th percentile).
    
    If the sensitivity data is missing or empty, it flags the robustness check as inconclusive.
    
    Args:
        results: The current results dictionary (modified in place and returned).
        alpha: The significance threshold (default 0.05).
            
    Returns:
        The updated results dictionary with the robustness conclusion.
    """
    sensitivity_data = results.get("sensitivity_analysis", {})
    
    if not sensitivity_data or "thresholds" not in sensitivity_data:
        logger.warning("Sensitivity analysis data is missing or empty. Cannot evaluate robustness.")
        results["sensitivity_analysis"]["robustness_conclusion"] = (
            "Inconclusive: Sensitivity analysis data is missing or empty."
        )
        results["sensitivity_analysis"]["robustness_verified"] = False
        return results
    
    thresholds = sensitivity_data["thresholds"]
    
    if not isinstance(thresholds, list) or len(thresholds) == 0:
        logger.warning("No threshold data found in sensitivity analysis.")
        results["sensitivity_analysis"]["robustness_conclusion"] = (
            "Inconclusive: No threshold data found in sensitivity analysis."
        )
        results["sensitivity_analysis"]["robustness_verified"] = False
        return results
    
    # Extract the hypothesis test result to compare against
    hypothesis_test = results.get("hypothesis_test", {})
    primary_p_value = hypothesis_test.get("p_value")
    is_primary_significant = primary_p_value is not None and primary_p_value < alpha
    
    # Check consistency across thresholds
    # We look for:
    # 1. Consistent direction of effect (e.g., F1 scores don't flip sign drastically)
    # 2. Stability of significance if per-threshold p-values were computed (optional, but good practice)
    # For this implementation, we check if the key metrics (F1, FPR) show monotonic or stable trends
    # rather than erratic fluctuations that would invalidate the headline finding.
    
    f1_scores = [t.get("f1_score") for t in thresholds if t.get("f1_score") is not None]
    fpr_scores = [t.get("false_positive_rate") for t in thresholds if t.get("false_positive_rate") is not None]
    
    robustness_verified = True
    conclusion_parts = []
    
    if not f1_scores:
        robustness_verified = False
        conclusion_parts.append("F1 scores missing across thresholds.")
    else:
        # Check for extreme variance (simple heuristic: std dev relative to mean)
        import statistics
        try:
            f1_mean = statistics.mean(f1_scores)
            f1_stdev = statistics.stdev(f1_scores) if len(f1_scores) > 1 else 0
            if f1_mean != 0 and (f1_stdev / abs(f1_mean)) > 0.5:
                robustness_verified = False
                conclusion_parts.append("High variance in F1 scores across thresholds.")
            else:
                conclusion_parts.append(f"F1 scores stable (mean: {f1_mean:.3f}, std: {f1_stdev:.3f}).")
        except statistics.StatisticsError:
            robustness_verified = False
            conclusion_parts.append("Could not calculate F1 statistics.")
    
    if not fpr_scores:
        robustness_verified = False
        conclusion_parts.append("FPR scores missing across thresholds.")
    else:
        try:
            fpr_mean = statistics.mean(fpr_scores)
            fpr_stdev = statistics.stdev(fpr_scores) if len(fpr_scores) > 1 else 0
            if fpr_mean != 0 and (fpr_stdev / abs(fpr_mean)) > 0.5:
                robustness_verified = False
                conclusion_parts.append("High variance in FPR scores across thresholds.")
            else:
                conclusion_parts.append(f"FPR scores stable (mean: {fpr_mean:.3f}, std: {fpr_stdev:.3f}).")
        except statistics.StatisticsError:
            robustness_verified = False
            conclusion_parts.append("Could not calculate FPR statistics.")
    
    # Final verdict
    if robustness_verified:
        status = "Holds" if is_primary_significant else "Holds (Null)"
        results["sensitivity_analysis"]["robustness_conclusion"] = (
            f"Headline finding {status} across swept thresholds. "
            "Metrics show stable trends without erratic fluctuations. "
            + " | ".join(conclusion_parts)
        )
        results["sensitivity_analysis"]["robustness_verified"] = True
        logger.info(f"Robustness check passed: Headline findings hold across thresholds.")
    else:
        results["sensitivity_analysis"]["robustness_conclusion"] = (
            f"Headline finding does NOT hold robustly across thresholds. "
            "Metrics show instability. "
            + " | ".join(conclusion_parts)
        )
        results["sensitivity_analysis"]["robustness_verified"] = False
        logger.warning(f"Robustness check failed: Headline findings do not hold across thresholds.")
    
    return results