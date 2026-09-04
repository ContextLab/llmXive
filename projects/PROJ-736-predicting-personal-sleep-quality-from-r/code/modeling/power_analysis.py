"""Power analysis for the sleep quality prediction study.

Performs a pilot power analysis to validate the 100-subject subset for
the permutation test, using a theoretical F-test for linear regression.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

import numpy as np
from scipy.stats import f

# Import local config
try:
    from config import get_hyperparameter, get_paths
except ImportError:
    # Fallback for direct execution or different import context
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import get_hyperparameter, get_paths


def calculate_power_f_test(
    n_samples: int,
    n_predictors: int,
    r_squared: float,
    alpha: float = 0.05
) -> float:
    """Calculate statistical power for a linear regression F-test.

    Args:
        n_samples: Number of observations (subjects).
        n_predictors: Number of predictors (features) in the model.
        r_squared: Expected effect size (R-squared value).
        alpha: Significance level (alpha).

    Returns:
        Statistical power (probability of rejecting null when false).
    """
    # Degrees of freedom
    df1 = n_predictors  # Numerator df (model)
    df2 = n_samples - n_predictors - 1  # Denominator df (error)

    if df2 <= 0:
        raise ValueError(
            f"Sample size too small for given predictors. "
            f"Need n_samples > n_predictors + 1. Got {n_samples} vs {n_predictors + 1}."
        )

    # Non-centrality parameter (lambda) for the F-distribution
    # lambda = (R^2 / (1 - R^2)) * n
    if r_squared >= 1.0:
        r_squared = 0.9999
    if r_squared <= 0.0:
        r_squared = 0.0001

    non_central_param = (r_squared / (1 - r_squared)) * n_samples

    # Critical F value
    f_crit = f.ppf(1 - alpha, df1, df2)

    # Power is the probability that the non-central F statistic exceeds the critical value
    # We use the survival function (sf) of the non-central F distribution
    # Note: scipy.stats.ncf.sf(x, dfn, dfd, nc)
    # However, scipy.stats.ncf is not always available or stable in all environments.
    # A robust approximation or using the cumulative distribution function (cdf) is preferred.
    # Power = 1 - CDF(f_crit; df1, df2, ncp)
    try:
        from scipy.stats import ncf
        power = 1.0 - ncf.cdf(f_crit, df1, df2, non_central_param)
    except ImportError:
        # Fallback: If ncf is missing, we cannot compute exact power without numpy/scipy extensions.
        # In a strict environment, this should fail loudly rather than returning a dummy.
        raise RuntimeError(
            "scipy.stats.ncf is required for power analysis but is not available. "
            "Please ensure scipy is installed with all optional dependencies."
        )

    return max(0.0, min(1.0, power))


def run_power_analysis(
    n_samples: int = 100,
    n_predictors: int = 50,
    expected_r_squared: float = 0.05,
    alpha: float = 0.05,
    power_threshold: float = 0.8
) -> Dict[str, Any]:
    """Run the power analysis calculation.

    Args:
        n_samples: Number of subjects in the subset.
        n_predictors: Number of features (after dimensionality reduction).
        expected_r_squared: Expected effect size.
        alpha: Significance level.
        power_threshold: Minimum required power.

    Returns:
        Dictionary with analysis results.
    """
    try:
        power = calculate_power_f_test(
            n_samples=n_samples,
            n_predictors=n_predictors,
            r_squared=expected_r_squared,
            alpha=alpha
        )
    except ValueError as e:
        return {
            "status": "failed",
            "error": str(e),
            "n_samples": n_samples,
            "n_predictors": n_predictors,
            "expected_r_squared": expected_r_squared
        }

    is_valid = power >= power_threshold

    return {
        "status": "success" if is_valid else "insufficient_power",
        "parameters": {
            "n_samples": n_samples,
            "n_predictors": n_predictors,
            "expected_r_squared": expected_r_squared,
            "alpha": alpha,
            "power_threshold": power_threshold
        },
        "results": {
            "calculated_power": float(power),
            "is_valid": is_valid,
            "meets_threshold": is_valid
        },
        "conclusion": (
            f"Power analysis for N={n_samples} subjects: "
            f"Calculated power is {power:.4f} (threshold: {power_threshold}). "
            f"{'Valid' if is_valid else 'Invalid'} for the proposed study design."
        )
    }


def save_power_analysis(results: Dict[str, Any], output_path: str) -> None:
    """Save power analysis results to a JSON file.

    Args:
        results: Dictionary containing analysis results.
        output_path: Path to save the JSON file.
    """
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)


def main() -> int:
    """Main entry point for the power analysis script."""
    # Get configuration
    paths = get_paths()
    results_dir = paths.get("results_dir", "data/results")
    output_file = os.path.join(results_dir, "power_analysis.json")

    # Load hyperparameters from config
    try:
        expected_r2 = get_hyperparameter("EXPECTED_R2_EFFECT_SIZE", 0.05)
        alpha_level = get_hyperparameter("ALPHA_LEVEL", 0.05)
        power_threshold = get_hyperparameter("POWER_THRESHOLD", 0.8)
    except Exception:
        # Fallback to defaults if config loading fails
        expected_r2 = 0.05
        alpha_level = 0.05
        power_threshold = 0.8

    # Define the subset size (from T021/T037a requirements)
    n_samples = 100

    # Estimate n_predictors:
    # In the actual pipeline, PCA reduces dimensions.
    # We assume a conservative estimate based on typical fMRI connectivity
    # (e.g., 200 regions -> ~20k edges -> PCA reduces to ~50-100 components).
    # Using 50 as a conservative estimate for the effective degrees of freedom.
    n_predictors = 50

    print(f"Running Power Analysis:")
    print(f"  N (Subjects): {n_samples}")
    print(f"  Predictors (PCA components): {n_predictors}")
    print(f"  Expected R²: {expected_r2}")
    print(f"  Alpha: {alpha_level}")
    print(f"  Power Threshold: {power_threshold}")

    results = run_power_analysis(
        n_samples=n_samples,
        n_predictors=n_predictors,
        expected_r_squared=expected_r2,
        alpha=alpha_level,
        power_threshold=power_threshold
    )

    print(f"\nResult: {results['conclusion']}")

    save_power_analysis(results, output_file)
    print(f"Saved results to: {output_file}")

    return 0 if results.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
