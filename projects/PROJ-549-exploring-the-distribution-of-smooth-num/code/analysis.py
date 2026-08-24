"""
Statistical analysis module for smooth number density measurements.

This module implements power-law regression, goodness-of-fit tests, and
statistical analysis for the smooth number distribution project.

IMPORTANT DISCLAIMER:
This analysis measures statistical associations between interval length and
smooth number density. Correlation does not imply causation. The observed
trends are descriptive patterns within the sampled data and do not establish
causal mechanisms or universal laws. All interpretations should be framed
as associational findings subject to further theoretical investigation.
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit
from scipy.special import gamma

# Import Dickman function
from dickman import DickmanFunction, rho

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_density_data(file_path: str) -> pd.DataFrame:
    """
    Load density measurement data from CSV file.

    Args:
        file_path: Path to the CSV file.

    Returns:
        DataFrame with density measurements.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")

    logger.info(f"Loading data from {file_path}")
    df = pd.read_csv(file_path)

    # Ensure numeric columns
    numeric_cols = ['x', 'y', 'h', 'density', 'dickman_rho', 'deviation_ratio']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def power_law(x: np.ndarray, c: float, beta: float) -> np.ndarray:
    """
    Power-law function: f(x) = c * x^beta

    Args:
        x: Input values.
        c: Scaling coefficient.
        beta: Exponent.

    Returns:
        Predicted values.
    """
    return c * np.power(x, beta)


def fit_power_law_deviation(
    df: pd.DataFrame,
    x_col: str = 'h',
    y_col: str = 'deviation_ratio'
) -> Dict[str, Any]:
    """
    Fit a power-law model to deviation ratio data: R ∝ h^beta

    Args:
        df: DataFrame containing the data.
        x_col: Column name for independent variable (h).
        y_col: Column name for dependent variable (deviation_ratio).

    Returns:
        Dictionary with fit parameters and statistics.
    """
    # Filter out NaN values
    mask = df[[x_col, y_col]].notna().all(axis=1)
    df_clean = df[mask]

    if len(df_clean) < 2:
        logger.warning("Insufficient data for regression")
        return {
            'beta': None,
            'c': None,
            'r_squared': None,
            'p_value': None,
            'std_error': None,
            'n_points': len(df_clean)
        }

    x = df_clean[x_col].values
    y = df_clean[y_col].values

    # Log-transform for linear regression
    log_x = np.log10(x)
    log_y = np.log10(y)

    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)

    # Convert back to power-law parameters
    beta = slope
    c = 10 ** intercept

    return {
        'beta': beta,
        'c': c,
        'r_squared': r_value ** 2,
        'p_value': p_value,
        'std_error': std_err,
        'n_points': len(df_clean)
    }


def fit_power_law_raw_density(
    df: pd.DataFrame,
    x_col: str = 'h',
    y_col: str = 'density'
) -> Dict[str, Any]:
    """
    Fit a power-law model to raw density data: ρ = c * h^beta

    Args:
        df: DataFrame containing the data.
        x_col: Column name for independent variable (h).
        y_col: Column name for dependent variable (density).

    Returns:
        Dictionary with fit parameters and statistics.
    """
    # Filter out NaN and zero values (log requires positive)
    mask = (df[[x_col, y_col]].notna().all(axis=1)) & (df[y_col] > 0)
    df_clean = df[mask]

    if len(df_clean) < 2:
        logger.warning("Insufficient data for regression")
        return {
            'beta': None,
            'c': None,
            'r_squared': None,
            'p_value': None,
            'std_error': None,
            'n_points': len(df_clean)
        }

    x = df_clean[x_col].values
    y = df_clean[y_col].values

    # Log-transform for linear regression
    log_x = np.log10(x)
    log_y = np.log10(y)

    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_y)

    # Convert back to power-law parameters
    beta = slope
    c = 10 ** intercept

    return {
        'beta': beta,
        'c': c,
        'r_squared': r_value ** 2,
        'p_value': p_value,
        'std_error': std_err,
        'n_points': len(df_clean)
    }


def run_plan_primary_analysis(
    data_path: str,
    output_path: str,
    y_values: List[int]
) -> Dict[str, Any]:
    """
    Run Plan-primary analysis: Power-law regression on deviation ratio.

    This is the MAIN scientific output per the Plan, fitting R ∝ h^beta
    for each y-group using the Plan-defined grid.

    Args:
        data_path: Path to Plan grid data CSV.
        output_path: Path to save results.
        y_values: List of y values to analyze.

    Returns:
        Dictionary with all fit results.
    """
    logger.info(f"Running Plan-primary analysis on {data_path}")

    try:
        df = load_density_data(data_path)
    except FileNotFoundError as e:
        logger.error(f"Cannot load data: {e}")
        return {}

    results = {}

    for y_val in y_values:
        y_data = df[df['y'] == y_val]

        if y_data.empty:
            logger.warning(f"No data for y={y_val}")
            continue

        fit_result = fit_power_law_deviation(y_data)
        fit_result['y'] = y_val
        results[f'y_{y_val}'] = fit_result

        logger.info(f"y={y_val}: beta={fit_result['beta']:.4f}, "
                   f"R²={fit_result['r_squared']:.4f}, "
                   f"n={fit_result['n_points']}")

    # Save results
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Plan-primary results saved to {output_path}")

    return results


def run_spec_mandatory_analysis(
    data_path: str,
    output_path: str,
    y_values: List[int]
) -> Dict[str, Any]:
    """
    Run Spec-mandatory analysis: Power-law regression on raw density.

    This satisfies FR-004 and SC-001, fitting ρ = c * h^beta for each y-group
    using the Spec-defined grid.

    Args:
        data_path: Path to Spec grid data CSV.
        output_path: Path to save results.
        y_values: List of y values to analyze.

    Returns:
        Dictionary with all fit results.
    """
    logger.info(f"Running Spec-mandatory analysis on {data_path}")

    try:
        df = load_density_data(data_path)
    except FileNotFoundError as e:
        logger.error(f"Cannot load data: {e}")
        return {}

    results = {}

    for y_val in y_values:
        y_data = df[df['y'] == y_val]

        if y_data.empty:
            logger.warning(f"No data for y={y_val}")
            continue

        fit_result = fit_power_law_raw_density(y_data)
        fit_result['y'] = y_val
        results[f'y_{y_val}'] = fit_result

        logger.info(f"y={y_val}: beta={fit_result['beta']:.4f}, "
                   f"R²={fit_result['r_squared']:.4f}, "
                   f"n={fit_result['n_points']}")

    # Save results
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Spec-mandatory results saved to {output_path}")

    return results


def run_chi_square_goodness_of_fit(
    data_path: str,
    output_path: str,
    y_values: List[int],
    n_bins: int = 10
) -> Dict[str, Any]:
    """
    Perform Chi-Square Goodness-of-Fit test comparing observed vs Dickman expectations.

    This satisfies the mandatory FR-005 requirement. We bin the interval data,
    calculate expected counts using Dickman(u) * h for each bin, and compute p-values.

    IMPORTANT: This test assesses whether the observed distribution is consistent
    with the Dickman function prediction. It does not imply causation.

    Args:
        data_path: Path to data CSV.
        output_path: Path to save results.
        y_values: List of y values to analyze.
        n_bins: Number of bins for Chi-Square test.

    Returns:
        Dictionary with Chi-Square test results.
    """
    logger.info(f"Running Chi-Square Goodness-of-Fit on {data_path}")

    try:
        df = load_density_data(data_path)
    except FileNotFoundError as e:
        logger.error(f"Cannot load data: {e}")
        return {}

    results = {}

    for y_val in y_values:
        y_data = df[df['y'] == y_val].copy()

        if y_data.empty:
            logger.warning(f"No data for y={y_val}")
            continue

        # Sort by h and bin
        y_data = y_data.sort_values('h')
        n_samples = len(y_data)

        if n_samples < n_bins:
            logger.warning(f"Insufficient samples ({n_samples}) for {n_bins} bins")
            results[f'y_{y_val}'] = {
                'chi_square': None,
                'p_value': None,
                'degrees_of_freedom': None,
                'n_samples': n_samples,
                'n_bins': n_bins,
                'status': 'insufficient_samples'
            }
            continue

        # Create bins based on h
        y_data['bin'] = pd.qcut(y_data['h'], q=n_bins, labels=False, duplicates='drop')

        # Calculate observed and expected counts per bin
        observed_counts = []
        expected_counts = []

        for bin_idx in range(n_bins):
            bin_data = y_data[y_data['bin'] == bin_idx]

            if len(bin_data) == 0:
                observed_counts.append(0)
                expected_counts.append(0)
                continue

            # Observed: count of smooth numbers
            obs = bin_data['density'].sum() * len(bin_data)  # Approximate total count
            observed_counts.append(obs)

            # Expected: based on Dickman function
            # Average u for this bin
            avg_u = bin_data['x'].mean() / bin_data['y'].mean()
            avg_h = bin_data['h'].mean()

            # Expected density using Dickman
            dickman_val = rho(avg_u) if avg_u > 0 else 0
            exp = dickman_val * avg_h
            expected_counts.append(exp)

        observed_counts = np.array(observed_counts)
        expected_counts = np.array(expected_counts)

        # Filter out zero expected values (Chi-Square requirement)
        mask = expected_counts > 0
        if not np.any(mask):
            logger.warning(f"No valid bins for y={y_val}")
            results[f'y_{y_val}'] = {
                'chi_square': None,
                'p_value': None,
                'degrees_of_freedom': None,
                'n_samples': n_samples,
                'n_bins': n_bins,
                'status': 'no_valid_bins'
            }
            continue

        obs_valid = observed_counts[mask]
        exp_valid = expected_counts[mask]

        # Perform Chi-Square test
        # Note: scipy.stats.chisquare expects observed and expected frequencies
        chi2_stat, p_val = stats.chisquare(obs_valid, exp_valid)
        dof = len(obs_valid) - 1

        results[f'y_{y_val}'] = {
            'chi_square': chi2_stat,
            'p_value': p_val,
            'degrees_of_freedom': dof,
            'n_samples': n_samples,
            'n_bins': n_bins,
            'status': 'success'
        }

        logger.info(f"y={y_val}: χ²={chi2_stat:.4f}, p={p_val:.4f}, dof={dof}")

    # Save results
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Load existing results if file exists
        existing_results = {}
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r') as f:
                    existing_results = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing_results = {}

        # Merge new results
        existing_results['chi_square_tests'] = results

        with open(output_path, 'w') as f:
            json.dump(existing_results, f, indent=2)
        logger.info(f"Chi-Square results saved to {output_path}")

    return results


def main() -> None:
    """Main entry point for analysis."""
    parser = argparse.ArgumentParser(
        description='Statistical analysis for smooth number density measurements.'
    )
    parser.add_argument(
        '--plan-data',
        type=str,
        default='data/density_measurements_plan.csv',
        help='Path to Plan grid data CSV'
    )
    parser.add_argument(
        '--spec-data',
        type=str,
        default='data/density_measurements_spec.csv',
        help='Path to Spec grid data CSV'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='Output directory for results'
    )
    parser.add_argument(
        '--y-values',
        type=int,
        nargs='+',
        default=[100, 1000, 10000],
        help='Y values to analyze'
    )
    parser.add_argument(
        '--plan-output',
        type=str,
        default='plan_primary_fits.json',
        help='Output filename for Plan-primary results'
    )
    parser.add_argument(
        '--spec-output',
        type=str,
        default='spec_mandatory_fits.json',
        help='Output filename for Spec-mandatory results'
    )
    parser.add_argument(
        '--chi-square-output',
        type=str,
        default='model_fits.json',
        help='Output filename for Chi-Square results'
    )

    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Run Plan-primary analysis
    plan_output = os.path.join(args.output_dir, args.plan_output)
    plan_results = run_plan_primary_analysis(
        args.plan_data,
        plan_output,
        args.y_values
    )

    # Run Spec-mandatory analysis
    spec_output = os.path.join(args.output_dir, args.spec_output)
    spec_results = run_spec_mandatory_analysis(
        args.spec_data,
        spec_output,
        args.y_values
    )

    # Run Chi-Square Goodness-of-Fit (FR-005)
    chi_output = os.path.join(args.output_dir, args.chi_square_output)
    chi_results = run_chi_square_goodness_of_fit(
        args.spec_data,
        chi_output,
        args.y_values
    )

    # Combine all results into model_fits.json
    combined = {
        'plan_primary': plan_results,
        'spec_mandatory': spec_results,
        'chi_square_tests': chi_results
    }

    with open(chi_output, 'w') as f:
        json.dump(combined, f, indent=2)
    logger.info(f"All results saved to {chi_output}")

    logger.info("Analysis complete")


if __name__ == '__main__':
    main()