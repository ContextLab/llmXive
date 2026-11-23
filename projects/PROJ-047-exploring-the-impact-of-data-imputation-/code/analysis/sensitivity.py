"""
Sensitivity Analysis Module.

This module provides functions to aggregate simulation results and verify
monotonic trends in bias and coverage rates across beta levels.
"""

import os
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from scipy import stats


def aggregate_sensitivity_data(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Aggregate the simulation_summary.csv into sensitivity_analysis_dataset.csv.

    Calculates the mean absolute bias and mean coverage rate per beta level
    and per imputation method/estimator combination.

    Args:
        input_path: Path to the input simulation_summary.csv file.
        output_path: Path where the output sensitivity_analysis_dataset.csv will be written.

    Returns:
        The aggregated DataFrame.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    # Filter out failed runs for aggregation, but ensure we handle NaNs correctly
    # The spec says: "preserve the row and status='failed' flag".
    # For aggregation of bias/coverage, failed runs (NaN) should not skew the mean.
    # We group by beta, method, estimator.
    
    # Ensure numeric columns are numeric
    df['bias'] = pd.to_numeric(df['bias'], errors='coerce')
    df['coverage_rate'] = pd.to_numeric(df['coverage_rate'], errors='coerce')
    df['beta'] = pd.to_numeric(df['beta'], errors='coerce')

    # Group by beta, method, estimator and calculate mean bias and mean coverage
    # We use dropna=True implicitly in mean() for the specific columns
    grouped = df.groupby(['beta', 'method', 'estimator'], dropna=False).agg(
        mean_bias=('bias', 'mean'),
        mean_coverage=('coverage_rate', 'mean'),
        n_runs=('bias', 'count') # Count total runs including failures if needed, or valid runs
    ).reset_index()

    # Reorder columns for clarity
    output_df = grouped[['beta', 'method', 'estimator', 'mean_bias', 'mean_coverage', 'n_runs']]

    # Sort by beta to ensure ordered output
    output_df = output_df.sort_values(by=['beta', 'method', 'estimator'])

    # Write to CSV
    output_df.to_csv(output_path, index=False)

    return output_df


def verify_monotonicity(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Verify monotonic trends for bias and coverage.

    Checks if mean absolute bias increases monotonically with beta (Spearman rho > 0.9, p < 0.05).
    Checks if mean coverage rate decreases monotonically with beta (negative slope, p < 0.05).

    Args:
        df: The aggregated DataFrame from aggregate_sensitivity_data.

    Returns:
        A dictionary containing the verification results.
    """
    results = {
        "monotonicity_confirmed": False,
        "spearman_rho": None,
        "p_value": None,
        "negative_slope_confirmed": False,
        "bias_trend": None,
        "coverage_trend": None
    }

    # Aggregate by beta only (average across methods/estimators) for the global trend check
    # Or check per method? The spec says "per beta level" in T030, and T031 checks "bias trend".
    # Usually, we check the overall trend across beta. Let's average across methods/estimators for the trend.
    beta_agg = df.groupby('beta').agg(
        mean_bias=('mean_bias', 'mean'),
        mean_coverage=('mean_coverage', 'mean')
    ).reset_index()
    
    beta_agg = beta_agg.sort_values('beta')

    if len(beta_agg) < 2:
        return results

    # Spearman correlation for Bias vs Beta
    # Expect positive correlation (bias increases as beta increases)
    rho_bias, p_bias = stats.spearmanr(beta_agg['beta'], beta_agg['mean_bias'])
    results['spearman_rho'] = float(rho_bias)
    results['p_value'] = float(p_bias)

    # Check conditions for bias monotonicity
    if rho_bias > 0.9 and p_bias < 0.05:
        results['monotonicity_confirmed'] = True
        results['bias_trend'] = "increasing"
    else:
        results['bias_trend'] = "not_increasing"

    # Check coverage trend (negative slope)
    # We can use Pearson or Spearman for slope direction, but let's use linear regression for "slope"
    # or just check correlation direction.
    rho_cov, p_cov = stats.spearmanr(beta_agg['beta'], beta_agg['mean_coverage'])
    results['coverage_trend'] = "decreasing" if rho_cov < 0 else "increasing"

    if rho_cov < 0 and p_cov < 0.05:
        results['negative_slope_confirmed'] = True
    else:
        results['negative_slope_confirmed'] = False

    return results


def save_monotonicity_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save the monotonicity verification results to a JSON file.

    Args:
        results: The dictionary of results from verify_monotonicity.
        output_path: Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)


def main():
    """
    Main entry point for the sensitivity analysis aggregation.
    """
    input_file = "data/results/simulation_summary.csv"
    output_csv = "data/results/sensitivity_analysis_dataset.csv"
    output_json = "data/results/sensitivity_analysis.json"

    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found. Please run the simulation first.")
        return 1

    try:
        print(f"Aggregating data from {input_file}...")
        df = aggregate_sensitivity_data(input_file, output_csv)
        print(f"Saved aggregated data to {output_csv}")

        print("Verifying monotonicity...")
        mono_results = verify_monotonicity(df)
        save_monotonicity_results(mono_results, output_json)
        print(f"Saved monotonicity results to {output_json}")

        print(f"Monotonicity confirmed: {mono_results['monotonicity_confirmed']}")
        print(f"Spearman Rho (Bias): {mono_results['spearman_rho']:.4f} (p={mono_results['p_value']:.4f})")
        print(f"Negative Slope (Coverage): {mono_results['negative_slope_confirmed']}")

        return 0

    except Exception as e:
        print(f"Error during sensitivity analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())