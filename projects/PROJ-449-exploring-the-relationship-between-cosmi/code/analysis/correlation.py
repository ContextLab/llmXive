import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_lagged_correlations(
    time_series: pd.Series,
    target_series: pd.Series,
    max_lag_months: int = 12,
    method: str = 'pearson'
) -> Dict[int, Tuple[float, float]]:
    """
    Calculate correlation coefficients between two time series at various lags.

    Args:
        time_series: The primary time series (e.g., cosmic ray flux).
        target_series: The target time series (e.g., sunspot number).
        max_lag_months: Maximum lag in months to consider (both positive and negative).
        method: Correlation method ('pearson' or 'spearman').

    Returns:
        A dictionary mapping lag (in months) to (correlation coefficient, p-value).
    """
    results = {}
    align_func = pearsonr if method == 'pearson' else spearmanr

    # Ensure indices are datetime-like and sorted
    if not isinstance(time_series.index, pd.DatetimeIndex):
        time_series = time_series.copy()
        time_series.index = pd.to_datetime(time_series.index)
    if not isinstance(target_series.index, pd.DatetimeIndex):
        target_series = target_series.copy()
        target_series.index = pd.to_datetime(target_series.index)

    # Create a common index for alignment
    common_index = time_series.index.intersection(target_series.index)
    ts_aligned = time_series.reindex(common_index)
    target_aligned = target_series.reindex(common_index)

    # Drop NaNs from both
    mask = ts_aligned.notna() & target_aligned.notna()
    ts_clean = ts_aligned[mask]
    target_clean = target_aligned[mask]

    if len(ts_clean) < 2:
        logger.warning("Insufficient data points for correlation calculation.")
        return {lag: (np.nan, np.nan) for lag in range(-max_lag_months, max_lag_months + 1)}

    for lag in range(-max_lag_months, max_lag_months + 1):
        # Shift target series by lag months
        # Positive lag: target leads time_series (target is older)
        # Negative lag: target lags time_series (target is newer)
        if lag == 0:
            t1 = ts_clean
            t2 = target_clean
        else:
            # Shift target by lag months
            # Using date offset for month shifting
            shifted_index = target_clean.index + pd.DateOffset(months=lag)
            t1 = ts_clean.reindex(shifted_index)
            t2 = target_clean

        # Align again after shift
        valid_mask = t1.notna() & t2.notna()
        t1_valid = t1[valid_mask]
        t2_valid = t2[valid_mask]

        if len(t1_valid) < 2:
            results[lag] = (np.nan, np.nan)
            continue

        try:
            corr, p_val = align_func(t1_valid, t2_valid)
            results[lag] = (corr, p_val)
        except Exception as e:
            logger.warning(f"Correlation failed at lag {lag}: {e}")
            results[lag] = (np.nan, np.nan)

    return results

def calculate_rigidity_bin_correlations(
    unified_data: pd.DataFrame,
    sunspot_column: str = 'sunspot_number',
    species_columns: Dict[str, List[str]] = None,
    rigidity_column: str = 'rigidity_bin',
    max_lag_months: int = 12,
    method: str = 'pearson'
) -> Dict[str, Dict[int, Dict[str, Any]]]:
    """
    Calculate correlations for each rigidity bin and species (ratio or absolute flux).

    Args:
        unified_data: DataFrame containing date, rigidity_bin, flux/ratio columns, and sunspot_number.
        sunspot_column: Name of the sunspot number column.
        species_columns: Dictionary mapping species name (e.g., 'He/p', 'Fe/p', 'p_flux') to column names.
        rigidity_column: Name of the rigidity bin column.
        max_lag_months: Maximum lag in months.
        method: Correlation method.

    Returns:
        Nested dictionary: {species: {rigidity_bin: {lag: {'corr': val, 'pval': val}}}}
    """
    if species_columns is None:
        # Default to ratios and absolute fluxes if not provided
        species_columns = {
            'He/p': ['He/p'],
            'Fe/p': ['Fe/p'],
            'p_flux': ['proton_flux'],
            'He_flux': ['helium_flux'],
            'Fe_flux': ['iron_flux']
        }

    results = {}

    # Ensure date column is datetime
    if 'date' in unified_data.columns:
        unified_data = unified_data.copy()
        unified_data['date'] = pd.to_datetime(unified_data['date'])
        unified_data = unified_data.set_index('date')

    rigidity_bins = unified_data[rigidity_column].unique()

    for species, cols in species_columns.items():
        results[species] = {}
        for col in cols:
            if col not in unified_data.columns:
                logger.warning(f"Column {col} not found in data. Skipping.")
                continue

            for r_bin in rigidity_bins:
                bin_data = unified_data[unified_data[rigidity_column] == r_bin]
                if col not in bin_data.columns or sunspot_column not in bin_data.columns:
                    continue

                ts_series = bin_data[col]
                sun_series = bin_data[sunspot_column]

                lag_results = calculate_lagged_correlations(
                    ts_series, sun_series,
                    max_lag_months=max_lag_months,
                    method=method
                )

                # Store results for this rigidity bin and column
                if r_bin not in results[species]:
                    results[species][r_bin] = {}
                results[species][r_bin][col] = lag_results

    return results

def main():
    """
    Main entry point for correlation analysis.
    Loads unified timeseries, calculates correlations, and saves results.
    """
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / 'data' / 'processed'
    output_json = data_dir / 'correlation_results.json'
    output_csv = data_dir / 'correlation_summary.csv'

    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Load unified timeseries
    input_file = data_dir / 'unified_timeseries.csv'
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)

    # Ensure date column exists and is datetime
    if 'date' not in df.columns:
        logger.error("Input file must contain a 'date' column.")
        sys.exit(1)

    # Define species columns (ratios and absolute fluxes)
    species_columns = {
        'He/p_ratio': ['He/p'],
        'Fe/p_ratio': ['Fe/p'],
        'p_flux': ['proton_flux'],
        'He_flux': ['helium_flux'],
        'Fe_flux': ['iron_flux']
    }

    # Filter out rows with NaN in key columns for correlation
    # We'll handle NaNs inside the correlation function, but let's be cautious
    # about rigidity bins with too few data points

    logger.info("Calculating lagged correlations...")
    results = calculate_rigidity_bin_correlations(
        df,
        sunspot_column='sunspot_number',
        species_columns=species_columns,
        rigidity_column='rigidity_bin',
        max_lag_months=12,
        method='pearson'
    )

    # Save JSON results
    logger.info(f"Saving detailed results to {output_json}")
    import json
    # Convert numpy types to Python types for JSON serialization
    def convert_numpy(obj):
        if isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(i) for i in obj]
        return obj

    json_results = convert_numpy(results)
    with open(output_json, 'w') as f:
        json.dump(json_results, f, indent=2)

    # Create a summary CSV
    # Structure: species, rigidity_bin, column, lag, corr, pval
    summary_rows = []
    for species, rigidity_data in results.items():
        for r_bin, col_data in rigidity_data.items():
            for col, lag_data in col_data.items():
                for lag, (corr, pval) in lag_data.items():
                    summary_rows.append({
                        'species': species,
                        'rigidity_bin': r_bin,
                        'column': col,
                        'lag_months': lag,
                        'correlation': corr,
                        'p_value': pval
                    })

    summary_df = pd.DataFrame(summary_rows)
    logger.info(f"Saving summary to {output_csv}")
    summary_df.to_csv(output_csv, index=False)

    logger.info("Correlation analysis complete.")
    return results

if __name__ == '__main__':
    main()