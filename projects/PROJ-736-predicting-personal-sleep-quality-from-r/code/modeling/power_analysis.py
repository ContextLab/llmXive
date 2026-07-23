"""Power analysis for the 100-subject stratified subset.

Validates that a sample size of N=100 is sufficient to detect the expected
effect size (R²=0.05) with alpha=0.05 and power > 0.8 using a theoretical
F-test for linear regression.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

import numpy as np
from scipy import stats

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_paths, get_hyperparameter

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
        r_squared: Expected R-squared effect size.
        alpha: Significance level (Type I error rate).

    Returns:
        Calculated statistical power (1 - beta).
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
    # Formula: lambda = (R² / (1 - R²)) * (n - k - 1)
    # where k is number of predictors
    non_central_param = (r_squared / (1 - r_squared)) * df2

    # Critical F value
    f_crit = stats.f.ppf(1 - alpha, df1, df2)

    # Power is the probability that the F-statistic exceeds the critical value
    # under the alternative hypothesis (non-central F distribution)
    power = 1 - stats.ncf.cdf(f_crit, df1, df2, non_central_param)

    return float(power)

def run_power_analysis() -> Dict[str, Any]:
    """Perform power analysis and return results dictionary.

    Returns:
        Dictionary containing power analysis results and validation status.
    """
    paths = get_paths()
    results_dir = paths["results"]
    os.makedirs(results_dir, exist_ok=True)

    # Load configuration
    expected_r2 = get_hyperparameter("EXPECTED_R2_EFFECT_SIZE")
    alpha_level = get_hyperparameter("ALPHA_LEVEL")
    power_threshold = get_hyperparameter("POWER_THRESHOLD")
    subset_size = get_hyperparameter("PERMUTATION_SUBSET_SIZE")

    # Estimate number of predictors (features)
    # We use a conservative estimate based on the Schaefer atlas (400 regions -> ~80k edges)
    # However, PCA will reduce this. We assume PCA retains enough to explain variance
    # but we use a representative number for power calculation.
    # For power analysis of the final model, we consider the effective degrees of freedom.
    # A safe conservative estimate for a high-dimensional model after PCA is often
    # much lower than the raw feature count. We'll use a placeholder that represents
    # the effective model complexity after dimensionality reduction.
    # Given the context of "100 subjects", we assume the model complexity (k)
    # is significantly lower than n to avoid overfitting, but we need a value.
    # Let's assume a moderate number of principal components, e.g., 20-30.
    # We'll use 20 as a conservative estimate for the effective number of predictors.
    n_predictors = 20

    # Calculate power
    power = calculate_power_f_test(
        n_samples=subset_size,
        n_predictors=n_predictors,
        r_squared=expected_r2,
        alpha=alpha_level
    )

    # Determine validation status
    is_valid = power > power_threshold

    results = {
        "analysis_type": "power_analysis",
        "parameters": {
            "sample_size": subset_size,
            "n_predictors": n_predictors,
            "expected_r_squared": expected_r2,
            "alpha_level": alpha_level,
            "power_threshold": power_threshold
        },
        "results": {
            "calculated_power": power,
            "is_valid": is_valid,
            "meets_threshold": power > power_threshold
        },
        "validation": {
            "status": "passed" if is_valid else "failed",
            "message": (
                f"Power analysis {'passed' if is_valid else 'failed'}. "
                f"Calculated power: {power:.4f} (threshold: {power_threshold}). "
                f"Effect size: R²={expected_r2}, N={subset_size}, k={n_predictors}."
            )
        }
    }

    return results

def save_power_analysis(results: Dict[str, Any], output_path: str) -> None:
    """Save power analysis results to JSON file.

    Args:
        results: Dictionary containing analysis results.
        output_path: Path to output JSON file.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

def main() -> int:
    """Main entry point for power analysis script.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        print("Starting power analysis...")
        results = run_power_analysis()

        paths = get_paths()
        output_file = str(Path(paths["results"]) / "power_analysis.json")

        save_power_analysis(results, output_file)

        print(f"Power analysis complete. Results saved to: {output_file}")
        print(f"Status: {results['validation']['status']}")
        print(f"Calculated Power: {results['results']['calculated_power']:.4f}")

        return 0

    except Exception as e:
        print(f"Power analysis failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
