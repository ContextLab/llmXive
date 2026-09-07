"""
Egger's Regression Test for Publication Bias.

This module implements Egger's linear regression test to detect
funnel plot asymmetry, which is an indicator of publication bias
in meta-analysis.
"""

import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats


def get_project_root() -> Path:
    """Get the project root directory (parent of the 'code' directory)."""
    return Path(__file__).resolve().parent.parent.parent


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: Path) -> None:
    """Save a dictionary to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def load_study_count_from_json(file_path: Path) -> int:
    """Load the study count (N) from study_count.json."""
    data = load_json(file_path)
    # Handle both 'N' and 'n' keys depending on the source file
    if 'N' in data:
        return int(data['N'])
    elif 'n' in data:
        return int(data['n'])
    else:
        # Default to 0 if key is missing
        return 0


def load_effect_sizes_and_se(meta_results_path: Path) -> Tuple[List[float], List[float]]:
    """
    Extract effect sizes (r) and standard errors (SE) from meta_analysis results.

    The meta_analysis.py script typically outputs a list of studies with 'effect_size'
    (or 'r') and 'se' (or 'standard_error').

    Returns:
        Tuple of (list of effect sizes, list of standard errors)
    """
    data = load_json(meta_results_path)

    # Try to find the list of individual study results
    studies = []
    if 'studies' in data:
        studies = data['studies']
    elif 'results' in data:
        studies = data['results']
    elif isinstance(data, list):
        studies = data

    if not studies:
        return [], []

    effect_sizes = []
    standard_errors = []

    for study in studies:
        # Extract effect size (r)
        r = study.get('effect_size') or study.get('r') or study.get('correlation')
        # Extract standard error (SE)
        se = study.get('se') or study.get('standard_error')

        if r is not None and se is not None:
            try:
                effect_sizes.append(float(r))
                standard_errors.append(float(se))
            except (ValueError, TypeError):
                continue

    return effect_sizes, standard_errors


def run_eggerr_regression(effect_sizes: List[float], standard_errors: List[float]) -> Dict[str, Any]:
    """
    Perform Egger's regression test.

    Egger's test regresses the standardized effect size (Z = r / SE)
    against precision (1 / SE). The intercept significantly different
    from zero indicates asymmetry (potential publication bias).

    Args:
        effect_sizes: List of correlation coefficients (r)
        standard_errors: List of standard errors for each r

    Returns:
        Dictionary with test results: t-statistic, p-value, intercept, slope, n_studies
    """
    n = len(effect_sizes)
    if n < 3:
        # Need at least 3 studies for regression
        return {
            "status": "skipped",
            "reason": "Insufficient studies for regression (n < 3)",
            "n_studies": n
        }

    # Calculate precision (1/SE) and standardized effect size (r/SE)
    # Add small epsilon to avoid division by zero if SE is 0
    epsilon = 1e-10
    precision = [1.0 / (se + epsilon) for se in standard_errors]
    standardized_effect = [r / (se + epsilon) for r, se in zip(effect_sizes, standard_errors)]

    # Convert to numpy arrays
    X = np.array(precision)
    Y = np.array(standardized_effect)

    # Perform linear regression: Y = intercept + slope * X
    # Using scipy.stats.linregress
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        slope, intercept, r_value, p_value, std_err = stats.linregress(X, Y)

    # The test statistic is the t-statistic for the intercept
    # t = intercept / std_err_intercept
    # However, linregress returns std_err of the slope, not intercept.
    # We need to calculate the standard error of the intercept manually.
    # Or simply use the t-statistic from the regression output if available.
    # scipy.stats.linregress returns t-statistic for the slope, not intercept.
    # We need to compute the t-statistic for the intercept.

    # Calculate residuals and standard error of the estimate
    y_pred = intercept + slope * X
    residuals = Y - y_pred
    s_err = np.sqrt(np.sum(residuals**2) / (n - 2))

    # Standard error of the intercept
    # SE_intercept = s_err * sqrt(sum(x^2) / (n * sum((x - mean(x))^2)))
    # Or equivalently: s_err * sqrt(1/n + mean(x)^2 / sum((x - mean(x))^2))
    x_mean = np.mean(X)
    ss_x = np.sum((X - x_mean)**2)

    if ss_x == 0:
        return {
            "status": "skipped",
            "reason": "Zero variance in precision (all SEs identical)",
            "n_studies": n
        }

    se_intercept = s_err * np.sqrt(np.sum(X**2) / (n * ss_x))

    # T-statistic for the intercept
    t_stat = intercept / se_intercept if se_intercept != 0 else 0.0

    # Two-tailed p-value for the intercept
    # Degrees of freedom = n - 2
    df = n - 2
    p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df))

    return {
        "status": "completed",
        "n_studies": n,
        "intercept": float(intercept),
        "slope": float(slope),
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "degrees_of_freedom": df,
        "interpretation": "Significant intercept (p < 0.05) suggests funnel plot asymmetry." if p_val < 0.05 else "No significant asymmetry detected."
    }


def run_bias_assessment() -> Dict[str, Any]:
    """
    Main function to run the bias assessment (Egger's test).

    Logic:
    1. Read gate_result.json. If status == 'narrative_required', skip.
    2. Read meta_results.json.
    3. Check N < 10. If so, skip.
    4. Run Egger's regression.
    5. Write results to data/derived/egger_test.json.

    Returns:
        Dictionary with the final result status.
    """
    project_root = get_project_root()
    gate_path = project_root / "data" / "derived" / "gate_result.json"
    meta_path = project_root / "data" / "derived" / "meta_results.json"
    output_path = project_root / "data" / "derived" / "egger_test.json"
    study_count_path = project_root / "data" / "processed" / "study_count.json"

    # Step 1: Check Gate
    try:
        gate_data = load_json(gate_path)
        status = gate_data.get("status", "")
        if status == "narrative_required":
            result = {
                "skipped": True,
                "reason": "Narrative mode active",
                "status": "skipped"
            }
            save_json(result, output_path)
            return result
    except FileNotFoundError:
        # If gate file is missing, we might assume quantitative is not safe,
        # but per task spec, we should handle missing gate gracefully or fail.
        # Let's assume if gate is missing, we cannot proceed with quantitative.
        result = {
            "skipped": True,
            "reason": "Gate result file not found (narrative mode assumed)",
            "status": "skipped"
        }
        save_json(result, output_path)
        return result

    # Step 2: Check Study Count (N < 10)
    try:
        n_studies = load_study_count_from_json(study_count_path)
        if n_studies < 10:
            result = {
                "skipped": True,
                "reason": "N < 10",
                "n_studies": n_studies,
                "status": "skipped"
            }
            save_json(result, output_path)
            return result
    except FileNotFoundError:
        result = {
            "skipped": True,
            "reason": "Study count file not found",
            "status": "skipped"
        }
        save_json(result, output_path)
        return result

    # Step 3: Run Egger's Regression
    try:
        effect_sizes, standard_errors = load_effect_sizes_and_se(meta_path)
        if not effect_sizes or len(effect_sizes) < 3:
            result = {
                "skipped": True,
                "reason": "Insufficient valid effect sizes for regression",
                "n_studies": len(effect_sizes),
                "status": "skipped"
            }
            save_json(result, output_path)
            return result

        test_result = run_eggerr_regression(effect_sizes, standard_errors)
        test_result["skipped"] = False
        save_json(test_result, output_path)
        return test_result

    except FileNotFoundError:
        result = {
            "skipped": True,
            "reason": "Meta results file not found",
            "status": "skipped"
        }
        save_json(result, output_path)
        return result
    except Exception as e:
        result = {
            "skipped": True,
            "reason": f"Error during regression: {str(e)}",
            "status": "error"
        }
        save_json(result, output_path)
        return result


def save_results(result: Dict[str, Any], output_path: Path) -> None:
    """Save the results to the output JSON file."""
    save_json(result, output_path)


def main():
    """Entry point for the bias analysis script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info("Starting Egger's Regression Test for Publication Bias...")

    try:
        result = run_bias_assessment()
        logger.info(f"Egger's test completed. Status: {result.get('status', 'unknown')}")
        if result.get('skipped'):
            logger.warning(f"Skipped: {result.get('reason')}")
        else:
            logger.info(f"P-value: {result.get('p_value', 'N/A'):.4f}")
            logger.info(f"Intercept: {result.get('intercept', 'N/A'):.4f}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()