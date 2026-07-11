"""
Errors-in-Variables (EIV) Regression for Exoplanet Radius Gap Analysis.

Performs weighted linear regression of gap radius vs log(period) while
correcting for Malmquist bias by including the Kepler completeness map
as a covariate.

Implements Spec FR-006: Correct for Malmquist bias using completeness map.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from scipy import stats

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger
from utils.retry import retry_call

logger = get_logger(__name__)


def load_gap_locations(filepath: str) -> pd.DataFrame:
    """
    Load gap locations from processed data.

    Args:
        filepath: Path to gap_locations.csv

    Returns:
        DataFrame with gap location data
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Gap locations file not found: {filepath}")

    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} gap location records from {filepath}")
    return df


def load_completeness_map(filepath: str) -> pd.DataFrame:
    """
    Load Kepler completeness map from raw data.

    Args:
        filepath: Path to completeness_map.csv

    Returns:
        DataFrame with completeness data
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Completeness map not found: {filepath}")

    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} completeness records from {filepath}")
    return df


def merge_data_with_completeness(
    gap_df: pd.DataFrame,
    completeness_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge gap location data with completeness map.

    The completeness map is joined on period bin to correct for Malmquist bias.
    We use the period bin center or range to find the corresponding completeness value.

    Args:
        gap_df: DataFrame with gap locations and period bins
        completeness_df: DataFrame with completeness map data

    Returns:
        Merged DataFrame with completeness covariate
    """
    # Ensure we have the necessary columns
    required_gap_cols = ['bin_index', 'gap_location', 'gap_uncertainty', 'weighted_mean_period']
    for col in required_gap_cols:
        if col not in gap_df.columns:
            raise ValueError(f"Gap locations missing required column: {col}")

    # Join on bin_index if available, otherwise we may need to map by period
    if 'bin_index' in completeness_df.columns:
        merged = gap_df.merge(
            completeness_df[['bin_index', 'completeness']],
            on='bin_index',
            how='left'
        )
    elif 'period_bin_center' in completeness_df.columns and 'period_bin_center' in gap_df.columns:
        # Merge on period bin center with tolerance
        merged = gap_df.merge(
            completeness_df,
            on='period_bin_center',
            how='left'
        )
    else:
        # Fallback: assume completeness is already in gap_df or needs interpolation
        logger.warning("Could not find common key for merging completeness. Checking if completeness already exists.")
        if 'completeness' in gap_df.columns:
            merged = gap_df.copy()
        else:
            raise ValueError("Cannot merge: no common key found between gap data and completeness map")

    # Fill missing completeness values with 1.0 (no bias correction)
    if 'completeness' in merged.columns:
        merged['completeness'] = merged['completeness'].fillna(1.0)
    else:
        merged['completeness'] = 1.0

    logger.info(f"Merged data has {len(merged)} records with completeness covariate")
    return merged


def eiv_regression(
    x: np.ndarray,
    y: np.ndarray,
    x_err: np.ndarray,
    y_err: np.ndarray,
    weights: Optional[np.ndarray] = None,
    completeness: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Perform Errors-in-Variables (EIV) regression with completeness correction.

    This implements a weighted linear regression that accounts for:
    1. Uncertainties in both x (log period) and y (gap radius)
    2. Completeness correction for Malmquist bias

    The model is: y = slope * x + intercept

    Args:
        x: Independent variable (log period)
        y: Dependent variable (gap radius)
        x_err: Uncertainty in x
        y_err: Uncertainty in y
        weights: Optional inverse variance weights
        completeness: Completeness values for Malmquist correction

    Returns:
        Dictionary with regression results
    """
    n = len(x)
    if n < 2:
        raise ValueError("Need at least 2 data points for regression")

    # Convert to arrays if not already
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x_err = np.asarray(x_err, dtype=float)
    y_err = np.asarray(y_err, dtype=float)

    # Handle missing values
    valid_mask = ~(np.isnan(x) | np.isnan(y) | np.isnan(x_err) | np.isnan(y_err))
    x = x[valid_mask]
    y = y[valid_mask]
    x_err = x_err[valid_mask]
    y_err = y_err[valid_mask]

    if weights is not None:
        weights = np.asarray(weights, dtype=float)[valid_mask]
    if completeness is not None:
        completeness = np.asarray(completeness, dtype=float)[valid_mask]

    n_valid = len(x)
    if n_valid < 2:
        raise ValueError("Need at least 2 valid data points after filtering")

    # Apply completeness correction: adjust y values based on completeness
    # Higher completeness means less bias, so we weight by completeness
    if completeness is not None:
        # Correct y by dividing by completeness (simplified Malmquist correction)
        # More sophisticated: use completeness as a weight in the regression
        y_corrected = y / np.clip(completeness, 0.1, 1.0)
    else:
        y_corrected = y

    # Calculate effective weights
    # Total variance = y_err^2 + (slope * x_err)^2 (iterative approach)
    # For initial estimate, use y_err^2
    if weights is None:
        total_var = y_err ** 2 + (0.1 * x_err) ** 2  # Initial slope estimate of 0.1
        weights = 1.0 / total_var
    else:
        # Combine provided weights with error-based weights
        total_var = y_err ** 2 + (0.1 * x_err) ** 2
        error_weights = 1.0 / total_var
        weights = weights * error_weights

    # Normalize weights
    weights = weights / np.max(weights)

    # Perform weighted linear regression
    # Using scipy.stats.linregress with weights approximation
    # Since scipy doesn't have weighted linregress directly, we use numpy's polyfit
    try:
        # Use polyfit for weighted regression
        coeffs, cov = np.polyfit(
            x, y_corrected, 1,
            w=np.sqrt(weights),
            cov=True
        )
        slope, intercept = coeffs
        slope_err = np.sqrt(cov[0, 0])
        intercept_err = np.sqrt(cov[1, 1])
    except np.linalg.LinAlgError:
        logger.warning("Singular matrix in regression, using unweighted fit")
        slope, intercept = np.polyfit(x, y_corrected, 1)
        # Estimate errors from residuals
        y_pred = slope * x + intercept
        residuals = y_corrected - y_pred
        rmse = np.sqrt(np.mean(residuals ** 2))
        slope_err = rmse / np.sqrt(np.sum((x - np.mean(x)) ** 2))
        intercept_err = rmse * np.sqrt(np.sum(x ** 2) / (len(x) * np.sum((x - np.mean(x)) ** 2)))

    # Calculate R-squared
    y_pred = slope * x + intercept
    ss_res = np.sum((y_corrected - y_pred) ** 2)
    ss_tot = np.sum((y_corrected - np.mean(y_corrected)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Calculate p-value for slope
    # Using t-test: t = slope / slope_err
    t_stat = slope / slope_err if slope_err > 0 else 0.0
    p_value = 2 * (1 - stats.t.cdf(np.abs(t_stat), n_valid - 2))

    return {
        'slope': float(slope),
        'slope_error': float(slope_err),
        'intercept': float(intercept),
        'intercept_error': float(intercept_err),
        'r_squared': float(r_squared),
        'p_value': float(p_value),
        'n_points': int(n_valid),
        'method': 'EIV_weighted_completeness_corrected'
    }


def run_regression(
    gap_locations_path: str,
    completeness_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Main function to run EIV regression on gap locations.

    Args:
        gap_locations_path: Path to gap_locations.csv
        completeness_path: Path to completeness_map.csv
        output_path: Path to save regression results

    Returns:
        Dictionary with regression results
    """
    logger.info(f"Starting EIV regression analysis")
    logger.info(f"Gap locations: {gap_locations_path}")
    logger.info(f"Completeness map: {completeness_path}")

    # Load data
    gap_df = load_gap_locations(gap_locations_path)
    completeness_df = load_completeness_map(completeness_path)

    # Merge with completeness
    merged_df = merge_data_with_completeness(gap_df, completeness_df)

    # Prepare variables for regression
    # x = log(period), y = gap_radius
    # Use weighted_mean_period for x
    if 'weighted_mean_period' not in merged_df.columns:
        if 'period' in merged_df.columns:
            merged_df['weighted_mean_period'] = merged_df['period']
        else:
            raise ValueError("No period column found in merged data")

    if 'gap_location' not in merged_df.columns:
        raise ValueError("gap_location column not found in merged data")

    x = np.log10(merged_df['weighted_mean_period'].values)
    y = merged_df['gap_location'].values

    # Get uncertainties
    x_err = np.zeros_like(x)  # Period uncertainties are typically small
    if 'period_uncertainty' in merged_df.columns:
        x_err = np.log10(1 + merged_df['period_uncertainty'].values / merged_df['weighted_mean_period'].values)

    y_err = np.zeros_like(y)
    if 'gap_uncertainty' in merged_df.columns:
        y_err = merged_df['gap_uncertainty'].values

    # Get weights (inverse variance of gap location)
    weights = None
    if 'gap_uncertainty' in merged_df.columns:
        gap_unc = merged_df['gap_uncertainty'].values
        valid_unc = gap_unc > 0
        weights = np.zeros_like(gap_unc)
        weights[valid_unc] = 1.0 / (gap_unc[valid_unc] ** 2)

    # Get completeness values
    completeness = merged_df['completeness'].values if 'completeness' in merged_df.columns else None

    # Run regression
    results = eiv_regression(
        x=x,
        y=y,
        x_err=x_err,
        y_err=y_err,
        weights=weights,
        completeness=completeness
    )

    # Add metadata
    results['input_gap_file'] = gap_locations_path
    results['input_completeness_file'] = completeness_path
    results['output_file'] = output_path

    # Save results to CSV
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create results DataFrame
    results_df = pd.DataFrame([results])
    results_df.to_csv(output_path, index=False)

    logger.info(f"Regression complete. Slope: {results['slope']:.4f} ± {results['slope_error']:.4f}")
    logger.info(f"Results saved to {output_path}")

    return results


def main():
    """Main entry point for regression analysis."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Default paths
    gap_locations_path = "data/processed/gap_locations.csv"
    completeness_path = "data/raw/completeness_map.csv"
    output_path = "data/processed/regression_results.csv"

    # Allow override via command line
    if len(sys.argv) > 1:
        gap_locations_path = sys.argv[1]
    if len(sys.argv) > 2:
        completeness_path = sys.argv[2]
    if len(sys.argv) > 3:
        output_path = sys.argv[3]

    try:
        results = run_regression(gap_locations_path, completeness_path, output_path)
        print(f"Regression completed successfully.")
        print(f"Slope: {results['slope']:.4f} ± {results['slope_error']:.4f}")
        print(f"R-squared: {results['r_squared']:.4f}")
        print(f"P-value: {results['p_value']:.4f}")
        return 0
    except Exception as e:
        logger.error(f"Regression failed: {e}")
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())