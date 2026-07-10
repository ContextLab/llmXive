import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
from scipy import stats

# Import logging utility from the project's existing API
from code.utils.logging import setup_logger

logger = setup_logger(__name__)

def calculate_lagged_correlations(
    data: pd.DataFrame,
    target_col: str,
    reference_col: str = 'sunspot_number',
    min_lag_months: int = -12,
    max_lag_months: int = 12,
    method: str = 'pearson'
) -> pd.DataFrame:
    """
    Calculate lagged correlations between a target time series and a reference series.
    
    This function shifts the reference series by a range of months (lags) and computes
    the correlation coefficient (Pearson or Spearman) and p-value for each lag.
    
    Args:
        data: DataFrame containing the time series data with a 'date' column.
            Must be sorted by date.
        target_col: Column name of the target variable (e.g., 'He/p_ratio', 'proton_flux').
        reference_col: Column name of the reference variable (default: 'sunspot_number').
        min_lag_months: Minimum lag in months (negative means reference leads target).
        max_lag_months: Maximum lag in months (positive means reference lags target).
        method: Correlation method ('pearson' or 'spearman').
    
    Returns:
        DataFrame with columns: lag_months, correlation, p_value, n_samples.
        Rows with insufficient data (n < 2) will have NaN values.
    """
    if method not in ['pearson', 'spearman']:
        raise ValueError(f"Unsupported correlation method: {method}. Use 'pearson' or 'spearman'.")
    
    if target_col not in data.columns or reference_col not in data.columns:
        raise ValueError(f"Columns {target_col} or {reference_col} not found in data.")
    
    # Ensure data is sorted by date
    if 'date' not in data.columns:
        raise ValueError("DataFrame must contain a 'date' column.")
    
    data_sorted = data.sort_values('date').reset_index(drop=True)
    
    target_series = data_sorted[target_col]
    reference_series = data_sorted[reference_col]
    
    results = []
    
    for lag in range(min_lag_months, max_lag_months + 1):
        # Shift reference series: positive lag means reference is shifted forward (lags behind target)
        # Negative lag means reference is shifted backward (leads target)
        shifted_reference = reference_series.shift(lag)
        
        # Drop pairs where either value is NaN
        valid_mask = ~target_series.isna() & ~shifted_reference.isna()
        
        if valid_mask.sum() < 2:
            # Not enough data points for correlation
            corr_val = np.nan
            p_val = np.nan
            n_samples = int(valid_mask.sum())
        else:
            valid_target = target_series[valid_mask]
            valid_reference = shifted_reference[valid_mask]
            
            if method == 'pearson':
                corr_val, p_val = stats.pearsonr(valid_target, valid_reference)
            else:  # spearman
                corr_val, p_val = stats.spearmanr(valid_target, valid_reference)
            
            n_samples = int(valid_mask.sum())
        
        results.append({
            'lag_months': lag,
            'correlation': corr_val,
            'p_value': p_val,
            'n_samples': n_samples
        })
    
    return pd.DataFrame(results)

def calculate_rigidity_bin_correlations(
    data: pd.DataFrame,
    rigidity_col: str = 'rigidity',
    species_cols: List[str] = None,
    reference_col: str = 'sunspot_number',
    min_lag_months: int = -12,
    max_lag_months: int = 12,
    method: str = 'pearson'
) -> Dict[str, pd.DataFrame]:
    """
    Calculate lagged correlations for each rigidity bin and for each specified species column.
    
    Args:
        data: DataFrame with columns including 'date', rigidity_col, and species columns.
        rigidity_col: Column name for rigidity values.
        species_cols: List of column names to analyze (e.g., ['He/p', 'Fe/p', 'proton_flux']).
        reference_col: Column name for the reference series (default: 'sunspot_number').
        min_lag_months: Minimum lag in months.
        max_lag_months: Maximum lag in months.
        method: Correlation method ('pearson' or 'spearman').
    
    Returns:
        Dictionary mapping (rigidity_bin, species_col) to a DataFrame of correlation results.
    """
    if species_cols is None:
        species_cols = []
    
    unique_rigidities = data[rigidity_col].dropna().unique()
    results_dict = {}
    
    logger.info(f"Starting correlation analysis for {len(unique_rigidities)} rigidity bins "
               f"and {len(species_cols)} species columns.")
    
    for rigidity in sorted(unique_rigidities):
        bin_data = data[data[rigidity_col] == rigidity].copy()
        
        if len(bin_data) < 10:
            logger.warning(f"Skipping rigidity bin {rigidity}: only {len(bin_data)} data points.")
            continue
        
        for species in species_cols:
            if species not in bin_data.columns:
                logger.warning(f"Skipping species {species} for rigidity {rigidity}: column not found.")
                continue
            
            try:
                corr_df = calculate_lagged_correlations(
                    bin_data,
                    target_col=species,
                    reference_col=reference_col,
                    min_lag_months=min_lag_months,
                    max_lag_months=max_lag_months,
                    method=method
                )
                
                key = (float(rigidity), species)
                results_dict[key] = corr_df
                
            except Exception as e:
                logger.error(f"Error calculating correlations for rigidity {rigidity}, species {species}: {e}")
    
    logger.info(f"Correlation analysis complete. Generated {len(results_dict)} result sets.")
    return results_dict

def main():
    """
    Main entry point to demonstrate the correlation analysis.
    Loads the unified timeseries, calculates correlations per rigidity bin,
    and prints a summary.
    """
    # Paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_path = project_root / "data" / "processed" / "unified_timeseries.csv"
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}. Please run the data pipeline first.")
        sys.exit(1)
    
    # Load data
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # Identify species columns (He/p, Fe/p, and absolute fluxes if present)
    species_cols = [col for col in df.columns if col in ['He/p', 'Fe/p', 'proton_flux', 'helium_flux', 'heavy_flux']]
    
    if not species_cols:
        logger.error("No valid species columns found in the dataset.")
        sys.exit(1)
    
    logger.info(f"Analyzing species: {species_cols}")
    
    # Calculate correlations
    results = calculate_rigidity_bin_correlations(
        data=df,
        rigidity_col='rigidity',
        species_cols=species_cols,
        min_lag_months=-12,
        max_lag_months=12,
        method='pearson'  # Default method
    )
    
    # Print summary
    logger.info("Correlation Analysis Summary:")
    for (rig, species), corr_df in results.items():
        max_corr_row = corr_df.loc[corr_df['correlation'].abs().idxmax()]
        logger.info(f"Rigidity={rig:.2f} GV, Species={species}: "
                   f"Max |r| = {max_corr_row['correlation']:.3f} at lag {max_corr_row['lag_months']} months "
                   f"(p={max_corr_row['p_value']:.3e})")
    
    return results

if __name__ == "__main__":
    main()