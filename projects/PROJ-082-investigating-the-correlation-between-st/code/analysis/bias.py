"""
Egger's Regression Test for Publication Bias.

This module implements Egger's linear regression test to detect
funnel plot asymmetry, a common indicator of publication bias in meta-analysis.
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
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
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
    """Load the study count 'N' from study_count.json."""
    data = load_json(file_path)
    return int(data.get('N', 0))


def load_effect_sizes_and_se(meta_results_path: Path) -> Tuple[List[float], List[float], int]:
    """
    Load effect sizes (r) and standard errors (SE) from meta_results.json.

    Returns:
        Tuple of (effect_sizes, standard_errors, N)
        If meta analysis was skipped, returns empty lists and N=0.
    """
    data = load_json(meta_results_path)

    if data.get('status') == 'skipped':
        return [], 0, 0

    # Extract effect sizes and sample sizes
    effect_sizes = []
    sample_sizes = []

    studies = data.get('studies', [])
    for study in studies:
        r = study.get('r')
        n = study.get('n')
        if r is not None and n is not None and n > 0:
            effect_sizes.append(float(r))
            sample_sizes.append(int(n))

    if not effect_sizes:
        return [], [], 0

    # Calculate standard error for Fisher's Z transformed r
    # SE_z = 1 / sqrt(N - 3)
    # However, Egger's test is often performed on the Z-transformed effect sizes
    # to stabilize variance.
    # We will compute Z and SE_z for the regression.
    z_scores = []
    se_z = []

    for r, n in zip(effect_sizes, sample_sizes):
        # Clamp r to (-0.999, 0.999) to avoid log(0) or division by zero
        r_clamped = max(-0.999, min(0.999, r))
        z = 0.5 * math.log((1 + r_clamped) / (1 - r_clamped))
        se = 1.0 / math.sqrt(n - 3)
        z_scores.append(z)
        se_z.append(se)

    return z_scores, se_z, len(effect_sizes)


def run_eggerr_regression(effect_sizes: List[float], standard_errors: List[float]) -> Dict[str, Any]:
    """
    Perform Egger's linear regression test.

    The regression model is:
        Z / SE = alpha + beta * (1 / SE) + epsilon

    Where:
        Z is the effect size (Fisher's Z)
        SE is the standard error of Z
        alpha is the intercept (measure of asymmetry)
        beta is the slope

    H0: alpha = 0 (no asymmetry)
    H1: alpha != 0 (asymmetry present)

    Args:
        effect_sizes: List of Fisher's Z transformed effect sizes.
        standard_errors: List of standard errors corresponding to effect sizes.

    Returns:
        Dictionary containing regression results.
    """
    if len(effect_sizes) < 3:
        # Need at least 3 points for a meaningful regression
        return {
            'skipped': True,
            'reason': 'Insufficient studies for regression (N < 3)'
        }

    X = np.array([1.0 / se for se in standard_errors])
    y = np.array(effect_sizes)

    # Weighted least squares is often preferred, but standard OLS is the classic Egger's
    # We will use OLS as per the original Egger et al. (1997) formulation.
    # y = intercept + slope * X

    try:
        # Fit linear regression: y = a + b*X
        # scipy.stats.linregress returns slope, intercept, r_value, p_value, std_err
        slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)

        # Calculate t-statistic for the intercept
        # t = intercept / std_err_intercept
        # The standard error of the intercept is not directly returned by linregress
        # We need to calculate it manually or use a more robust solver.
        # Using statsmodels is better, but to minimize dependencies we calculate manually.

        n = len(X)
        X_mean = np.mean(X)
        y_mean = np.mean(y)

        # Residual Sum of Squares (RSS)
        y_pred = intercept + slope * X
        rss = np.sum((y - y_pred) ** 2)

        # Standard Error of the Estimate (s)
        s = math.sqrt(rss / (n - 2))

        # Standard Error of the Intercept
        se_intercept = s * math.sqrt(1/n + (X_mean**2) / np.sum((X - X_mean)**2))

        if se_intercept == 0:
            t_stat_intercept = 0.0
        else:
            t_stat_intercept = intercept / se_intercept

        # Two-tailed p-value for the intercept
        df = n - 2
        p_value_intercept = 2 * (1 - stats.t.cdf(abs(t_stat_intercept), df))

        return {
            'intercept': float(intercept),
            'slope': float(slope),
            't_statistic': float(t_stat_intercept),
            'p_value': float(p_value_intercept),
            'r_squared': float(r_value ** 2),
            'n_studies': n,
            'degrees_of_freedom': df,
            'skipped': False
        }

    except Exception as e:
        return {
            'skipped': True,
            'reason': f'Regression failed: {str(e)}'
        }


def run_bias_assessment(meta_results_path: Path, study_count_path: Path) -> Dict[str, Any]:
    """
    Orchestrate the Egger's regression test.

    Args:
        meta_results_path: Path to meta_results.json
        study_count_path: Path to study_count.json

    Returns:
        Dictionary containing the full bias assessment results.
    """
    # Check study count
    try:
        N = load_study_count_from_json(study_count_path)
    except FileNotFoundError:
        return {
            'skipped': True,
            'reason': 'study_count.json not found'
        }

    if N < 10:
        return {
            'skipped': True,
            'reason': 'N < 10',
            'N': N
        }

    # Load effect sizes and SEs
    try:
        z_scores, se_z, effective_N = load_effect_sizes_and_se(meta_results_path)
    except FileNotFoundError:
        return {
            'skipped': True,
            'reason': 'meta_results.json not found'
        }

    if effective_N < 3:
        return {
            'skipped': True,
            'reason': f'Insufficient studies with valid data (N={effective_N})'
        }

    # Run regression
    results = run_eggerr_regression(z_scores, se_z)
    results['N'] = effective_N

    # Interpret results
    if not results.get('skipped', False):
        p_val = results['p_value']
        if p_val < 0.05:
            results['interpretation'] = 'Significant asymmetry detected (p < 0.05). Potential publication bias.'
        else:
            results['interpretation'] = 'No significant asymmetry detected (p >= 0.05). Evidence of publication bias is weak.'

    return results


def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save results to the specified JSON file."""
    save_json(results, output_path)


def main() -> int:
    """Main entry point for the script."""
    project_root = get_project_root()
    meta_results_path = project_root / 'data' / 'derived' / 'meta_results.json'
    study_count_path = project_root / 'data' / 'processed' / 'study_count.json'
    output_path = project_root / 'data' / 'derived' / 'egger_test.json'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        results = run_bias_assessment(meta_results_path, study_count_path)
        save_results(results, output_path)
        print(f"Egger's test results saved to {output_path}")
        return 0
    except Exception as e:
        print(f"Error running Egger's test: {e}", file=sys.stderr)
        # Even on error, save a status file if possible, or exit with error code
        error_result = {
            'skipped': True,
            'reason': f'Execution error: {str(e)}'
        }
        save_json(error_result, output_path)
        return 1


if __name__ == '__main__':
    sys.exit(main())