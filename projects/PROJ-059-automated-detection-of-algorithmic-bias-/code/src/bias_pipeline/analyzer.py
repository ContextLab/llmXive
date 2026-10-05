import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats

from .error_handler import safe_execute, ExecutionError, handle_pipeline_error
from .utils import setup_logging

# Initialize logger
logger = setup_logging(__name__)


@handle_pipeline_error(task_name="compute_spearman_correlation")
def compute_spearman_correlation(
    textual_bias_scores: List[float],
    fairness_slopes: List[float]
) -> Dict[str, float]:
    """
    Compute Spearman's rank correlation coefficient between Textual Bias Scores
    and Fairness Degradation Slopes.

    Args:
        textual_bias_scores: List of aggregated bias scores per repository.
        fairness_slopes: List of fairness degradation slopes (d(Fairness)/d(Skew)).

    Returns:
        Dict containing 'correlation_coefficient' and 'p_value'.

    Raises:
        ExecutionError: If lists are empty, mismatched length, or contain NaN/Inf.
    """
    if len(textual_bias_scores) == 0 or len(fairness_slopes) == 0:
        raise ExecutionError("Input lists cannot be empty for correlation analysis.")

    if len(textual_bias_scores) != len(fairness_slopes):
        raise ExecutionError(
            f"Length mismatch: {len(textual_bias_scores)} bias scores vs "
            f"{len(fairness_slopes)} fairness slopes."
        )

    # Convert to numpy arrays for validation
    scores_arr = np.array(textual_bias_scores)
    slopes_arr = np.array(fairness_slopes)

    if np.any(np.isnan(scores_arr)) or np.any(np.isnan(slopes_arr)):
        raise ExecutionError("Input data contains NaN values.")
    if np.any(np.isinf(scores_arr)) or np.any(np.isinf(slopes_arr)):
        raise ExecutionError("Input data contains infinite values.")

    if len(scores_arr) < 3:
        logger.warning("Insufficient data points (< 3) for reliable Spearman correlation.")

    try:
        correlation, p_value = stats.spearmanr(scores_arr, slopes_arr)
        logger.info(
            f"Spearman correlation computed: rho={correlation:.4f}, p={p_value:.4e}"
        )
        return {
            "correlation_coefficient": float(correlation),
            "p_value": float(p_value)
        }
    except Exception as e:
        raise ExecutionError(f"Failed to compute Spearman correlation: {e}") from e


@handle_pipeline_error(task_name="apply_bonferroni_correction")
def apply_bonferroni_correction(
    p_value: float,
    num_tests: int
) -> Dict[str, float]:
    """
    Apply Bonferroni correction to a p-value for multiple comparisons.

    Args:
        p_value: The raw p-value to correct.
        num_tests: The number of hypothesis tests performed (m).

    Returns:
        Dict containing 'corrected_p_value' and 'is_significant' (bool).

    Raises:
        ExecutionError: If p_value is out of bounds or num_tests <= 0.
    """
    if not (0.0 <= p_value <= 1.0):
        raise ExecutionError(f"Invalid p-value: {p_value}. Must be in [0, 1].")

    if num_tests <= 0:
        raise ExecutionError(f"Number of tests must be positive, got {num_tests}.")

    try:
        corrected_p = min(p_value * num_tests, 1.0)
        # Standard alpha threshold
        alpha = 0.05
        is_sig = corrected_p < alpha

        logger.info(
            f"Bonferroni correction applied: raw_p={p_value:.4e}, "
            f"m={num_tests}, corrected_p={corrected_p:.4e}, significant={is_sig}"
        )
        return {
            "corrected_p_value": float(corrected_p),
            "is_significant": bool(is_sig),
            "alpha": alpha,
            "num_tests": num_tests
        }
    except Exception as e:
        raise ExecutionError(f"Failed to apply Bonferroni correction: {e}") from e


@handle_pipeline_error(task_name="run_sensitivity_analysis")
def run_sensitivity_analysis(
    textual_bias_scores: List[float],
    fairness_slopes: List[float],
    alpha_range: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping alpha levels.

    Args:
        textual_bias_scores: List of bias scores.
        fairness_slopes: List of fairness slopes.
        alpha_range: List of alpha thresholds to test. Defaults to [0.01, 0.05, 0.1].

    Returns:
        Dict with 'raw_p_value', 'high_risk_count', and 'alpha_sweep_results'.
    """
    if alpha_range is None:
        alpha_range = [0.01, 0.05, 0.1]

    # Compute raw stats once
    corr_result = compute_spearman_correlation(textual_bias_scores, fairness_slopes)
    raw_p = corr_result["p_value"]

    # Apply Bonferroni for the single test (m=1) initially, or assume m=1 for sensitivity
    # per standard sensitivity analysis unless specified otherwise.
    # Here we treat the correlation as one test, so corrected_p == raw_p.
    # If the user intends multiple metrics, num_tests should be adjusted.
    num_tests = 1 
    bonf_result = apply_bonferroni_correction(raw_p, num_tests)
    raw_p_corrected = bonf_result["corrected_p_value"]

    sweep_results = []
    high_risk_count = 0

    for alpha in alpha_range:
        is_high_risk = raw_p_corrected < alpha
        if is_high_risk:
            high_risk_count += 1
        sweep_results.append({
            "alpha": alpha,
            "is_significant": is_high_risk,
            "p_value": raw_p_corrected
        })

    return {
        "raw_p_value": raw_p,
        "corrected_p_value": raw_p_corrected,
        "high_risk_count": high_risk_count,
        "alpha_sweep_results": sweep_results
    }


@handle_pipeline_error(task_name="flag_high_risk")
def flag_high_risk(
    corrected_p_value: float,
    threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Flag a result as 'High Risk' based on corrected p-value threshold.

    Args:
        corrected_p_value: The Bonferroni-corrected p-value.
        threshold: Significance threshold (default 0.05).

    Returns:
        Dict with 'is_high_risk' (bool) and 'risk_level' (str).
    """
    is_high_risk = corrected_p_value < threshold
    risk_level = "HIGH" if is_high_risk else "LOW"

    logger.info(
        f"Risk assessment: p={corrected_p_value:.4e}, threshold={threshold}, "
        f"risk_level={risk_level}"
    )

    return {
        "is_high_risk": bool(is_high_risk),
        "risk_level": risk_level,
        "threshold": threshold,
        "p_value": corrected_p_value
    }


@handle_pipeline_error(task_name="run_correlation_analysis")
def run_correlation_analysis(
    scores_path: str,
    slopes_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Main entry point to load scores and slopes, compute correlation,
    apply corrections, and generate the final report.

    Args:
        scores_path: Path to JSON/CSV containing textual bias scores.
        slopes_path: Path to JSON/CSV containing fairness degradation slopes.
        output_path: Path to write the final correlation results JSON.

    Returns:
        The analysis result dictionary.
    """
    # Load data (simplified for this task; assumes JSON format with lists)
    # In a full pipeline, this would handle CSV/Parquet etc.
    try:
        with open(scores_path, 'r') as f:
            scores_data = json.load(f)
            # Expecting a list of floats or a dict with a 'scores' key
            if isinstance(scores_data, dict) and 'scores' in scores_data:
                scores = scores_data['scores']
            else:
                scores = scores_data
        
        with open(slopes_path, 'r') as f:
            slopes_data = json.load(f)
            if isinstance(slopes_data, dict) and 'slopes' in slopes_data:
                slopes = slopes_data['slopes']
            else:
                slopes = slopes_data
    except FileNotFoundError as e:
        raise ExecutionError(f"Data file not found: {e.filename}") from e
    except json.JSONDecodeError as e:
        raise ExecutionError(f"Invalid JSON in data file: {e}") from e

    # 1. Compute Spearman
    corr_stats = compute_spearman_correlation(scores, slopes)

    # 2. Bonferroni (assuming 1 test for this specific correlation)
    # If multiple correlations were run, num_tests would be > 1
    num_tests = 1 
    bonf_stats = apply_bonferroni_correction(corr_stats["p_value"], num_tests)

    # 3. Sensitivity Analysis
    sensitivity = run_sensitivity_analysis(scores, slopes)

    # 4. Flag High Risk
    risk_flag = flag_high_risk(bonf_stats["corrected_p_value"])

    # Assemble Report
    report = {
        "correlation": corr_stats,
        "bonferroni_correction": bonf_stats,
        "sensitivity_analysis": sensitivity,
        "risk_assessment": risk_flag,
        "metadata": {
            "n_samples": len(scores),
            "analysis_type": "Spearman_Bonferroni"
        }
    }

    # Write Output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Correlation analysis report written to {output_path}")
    return report