"""
Significance testing module for validation set analysis.

This module implements the logic to re-compute Bonferroni correction
specifically for the validation set (2018-2020) as required by SC-003.
It uses the same procedure (global Neff logic applied to the subset)
to calculate alpha_adj for the test set.
"""
import os
import json
import pandas as pd
import numpy as np
from scipy import stats
from scipy import signal
from typing import Dict, List, Tuple, Optional
from code import logger
from code.config import TRAIN_START, TRAIN_END, TEST_START, TEST_END, ACE_VARS, NOAA_VARS
from code.analysis.neff import calculate_neff


def calculate_neff_for_subset(series: pd.Series) -> float:
    """
    Calculate effective sample size (Neff) for a given time series subset
    using the Pyper & Peterman method (detrend + lag-1 autocorrelation).

    Args:
        series: pandas Series containing the time series data

    Returns:
        Effective sample size (Neff) as a float
    """
    if len(series) < 2:
        logger.warning(f"Series too short for Neff calculation (len={len(series)}), returning original length")
        return float(len(series))

    # Remove linear trend as per Pyper & Peterman method
    detrended = signal.detrend(series.values)

    # Calculate lag-1 autocorrelation of residuals
    if len(detrended) < 2:
        return float(len(series))

    rho_1 = np.corrcoef(detrended[:-1], detrended[1:])[0, 1]

    # Handle edge cases where correlation is undefined or extreme
    if np.isnan(rho_1):
        logger.warning("Lag-1 autocorrelation is NaN, using raw sample size")
        return float(len(series))

    # Clamp rho_1 to prevent division by zero or negative Neff
    rho_1 = np.clip(rho_1, -0.999, 0.999)

    # Apply Pyper & Peterman formula: Neff = N * (1 - rho_1) / (1 + rho_1)
    n = len(series)
    neff = n * (1 - rho_1) / (1 + rho_1)

    logger.info(f"Neff calculated: N={n}, rho_1={rho_1:.4f}, Neff={neff:.2f}")
    return neff


def compute_bonferroni_threshold_for_subset(
    data: pd.DataFrame,
    params: List[str],
    indices: List[str],
    lags: List[int] = [0, 1, 2, 3, 6],
    alpha: float = 0.05
) -> Dict:
    """
    Compute Bonferroni correction threshold specifically for a validation subset.

    This function calculates the adjusted alpha (alpha_adj) for the test set
    using the same procedure as the global analysis but applied to the subset data.

    Args:
        data: DataFrame containing the validation subset data
        params: List of solar wind parameters (e.g., ['N_p', 'T_p', 'He2+_ratio'])
        indices: List of geomagnetic indices (e.g., ['Kp', 'Dst'])
        lags: List of time lags in hours to test
        alpha: Significance level (default 0.05)

    Returns:
        Dictionary containing:
            - alpha_adj: Adjusted alpha threshold
            - neff_values: Dict of Neff values for each variable
            - total_tests: Total number of hypothesis tests
            - lags: List of lags tested
    """
    # Calculate total number of tests (fixed global divisor as per SC-003)
    # 3 params × 2 indices × 5 lags = 30 tests
    total_tests = len(params) * len(indices) * len(lags)
    alpha_adj = alpha / total_tests

    logger.info(f"Computing Bonferroni threshold for subset: {total_tests} tests, alpha_adj={alpha_adj}")

    # Calculate Neff for each variable in the subset
    neff_values = {}

    # Combine all variables for Neff calculation
    all_vars = params + indices
    for var in all_vars:
        if var in data.columns:
            neff = calculate_neff_for_subset(data[var].dropna())
            neff_values[var] = neff
        else:
            logger.warning(f"Variable {var} not found in subset data, skipping Neff calculation")
            neff_values[var] = float(len(data))

    return {
        'alpha_adj': alpha_adj,
        'neff_values': neff_values,
        'total_tests': total_tests,
        'lags': lags,
        'alpha': alpha
    }


def compute_pvalue_with_neff(
    r: float,
    n: int,
    neff: float
) -> float:
    """
    Compute p-value for correlation coefficient using Neff adjustment.

    Args:
        r: Pearson correlation coefficient
        n: Original sample size
        neff: Effective sample size

    Returns:
        Two-tailed p-value adjusted for autocorrelation
    """
    if abs(r) >= 1.0:
        return 0.0 if r != 0 else 1.0

    # t-statistic calculation using Neff
    t_stat = r * np.sqrt((neff - 2) / (1 - r**2))
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=neff - 2))

    return p_value


def evaluate_validation_set_significance(
    data: pd.DataFrame,
    params: List[str],
    indices: List[str],
    lags: List[int] = [0, 1, 2, 3, 6],
    correlation_results: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Evaluate significance of correlations specifically for the validation set.

    This function:
    1. Filters data to the validation period (2018-2020)
    2. Computes local Neff for each variable in the subset
    3. Calculates Bonferroni-adjusted alpha for the subset
    4. Computes p-values using Neff-adjusted degrees of freedom
    5. Flags significant pairs based on local Bonferroni threshold

    Args:
        data: Full dataset DataFrame with timestamp column
        params: List of solar wind parameters
        indices: List of geomagnetic indices
        lags: List of time lags in hours
        correlation_results: Optional pre-computed correlation results DataFrame

    Returns:
        DataFrame with validation set significance results
    """
    # Filter to validation period
    mask = (data['timestamp'].dt.year >= TEST_START) & (data['timestamp'].dt.year <= TEST_END)
    validation_data = data[mask].copy()

    if len(validation_data) == 0:
        logger.error("No data found in validation period (2018-2020)")
        return pd.DataFrame()

    logger.info(f"Validation set size: {len(validation_data)} rows")

    # Compute local Bonferroni threshold
    threshold_info = compute_bonferroni_threshold_for_subset(
        validation_data, params, indices, lags
    )

    logger.info(f"Local alpha_adj for validation set: {threshold_info['alpha_adj']}")

    results = []

    for param in params:
        for index in indices:
            for lag in lags:
                # Shift parameter by lag hours
                shifted_param = validation_data[param].shift(-lag)

                # Drop NaN values resulting from shift
                valid_mask = shifted_param.notna() & validation_data[index].notna()
                x = shifted_param[valid_mask]
                y = validation_data[index][valid_mask]

                if len(x) < 10:  # Minimum sample size for meaningful correlation
                    logger.warning(f"Insufficient data for {param}-{index} at lag {lag}h (n={len(x)})")
                    continue

                # Compute correlation
                r, p_raw = stats.pearsonr(x, y)

                # Get Neff for this pair (use average of both variables)
                neff_param = threshold_info['neff_values'].get(param, len(x))
                neff_index = threshold_info['neff_values'].get(index, len(x))
                neff_avg = (neff_param + neff_index) / 2

                # Compute Neff-adjusted p-value
                p_neff_adjusted = compute_pvalue_with_neff(r, len(x), neff_avg)

                # Apply Bonferroni correction
                p_bonferroni = min(p_neff_adjusted * threshold_info['total_tests'], 1.0)

                # Flag significance
                is_significant = p_bonferroni < threshold_info['alpha_adj']

                results.append({
                    'parameter': param,
                    'index': index,
                    'lag_hours': lag,
                    'pearson_r': r,
                    'p_raw': p_raw,
                    'p_neff_adjusted': p_neff_adjusted,
                    'p_bonferroni': p_bonferroni,
                    'neff': neff_avg,
                    'n_samples': len(x),
                    'is_significant': is_significant,
                    'validation_period': f"{TEST_START}-{TEST_END}"
                })

    result_df = pd.DataFrame(results)

    if not result_df.empty:
        logger.info(f"Validation significance analysis complete: {len(result_df)} tests performed")
        logger.info(f"Significant pairs in validation set: {result_df['is_significant'].sum()}")
    else:
        logger.warning("No results generated for validation set")

    return result_df


def save_validation_thresholds(
    threshold_info: Dict,
    output_path: str = "artifacts/thresholds/validation_threshold.json"
):
    """
    Save validation set threshold information to JSON file.

    Args:
        threshold_info: Dictionary containing threshold information
        output_path: Path to output JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Convert numpy types to Python native types for JSON serialization
    serializable_info = {
        'alpha_adj': float(threshold_info['alpha_adj']),
        'total_tests': int(threshold_info['total_tests']),
        'alpha': float(threshold_info['alpha']),
        'lags': [int(l) for l in threshold_info['lags']],
        'neff_values': {k: float(v) for k, v in threshold_info['neff_values'].items()},
        'validation_period': f"{TEST_START}-{TEST_END}"
    }

    with open(output_path, 'w') as f:
        json.dump(serializable_info, f, indent=2)

    logger.info(f"Validation thresholds saved to {output_path}")


def run_validation_significance_analysis(
    data_path: str = "data/processed/synced.csv",
    output_path: str = "data/processed/validation_significance.csv"
):
    """
    Main entry point for running validation set significance analysis.

    Args:
        data_path: Path to the synced dataset
        output_path: Path to save results
    """
    logger.info("Starting validation set significance analysis")

    # Load data
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        return None

    data = pd.read_csv(data_path)
    data['timestamp'] = pd.to_datetime(data['timestamp'])

    # Define parameters and indices
    params = ACE_VARS
    indices = NOAA_VARS
    lags = [0, 1, 2, 3, 6]

    # Run analysis
    results = evaluate_validation_set_significance(data, params, indices, lags)

    if results.empty:
        logger.error("Validation significance analysis produced no results")
        return None

    # Save results
    results.to_csv(output_path, index=False)
    logger.info(f"Validation significance results saved to {output_path}")

    # Save threshold information
    threshold_info = compute_bonferroni_threshold_for_subset(
        data[data['timestamp'].dt.year >= TEST_START], params, indices, lags
    )
    save_validation_thresholds(threshold_info)

    return results