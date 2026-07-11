"""
T027: Calculate weighted mean period using inverse variance of gap location estimates.

This module computes the weighted mean orbital period for each period bin,
where the weights are derived from the inverse variance of the gap location
estimate (uncertainty) obtained from the bootstrap resampling in T024.

Output: data/processed/binned_stats.csv
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_gap_locations(file_path: str) -> pd.DataFrame:
    """
    Load the gap locations CSV produced by T024/T025.
    
    Expected columns include:
    - bin_index: The bin identifier
    - period_center: Center of the period bin (log scale)
    - gap_location: The estimated gap location (radius)
    - gap_uncertainty: The standard deviation/uncertainty from bootstrap
    - status: 'resolved' or 'unresolved'
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Gap locations file not found: {path}")
    
    df = pd.read_csv(path)
    required_cols = ['bin_index', 'gap_location', 'gap_uncertainty', 'status']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Gap locations file missing required columns: {missing}")
    
    return df

def calculate_weighted_mean_period(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the weighted mean period for each bin.
    
    Weight = 1 / (uncertainty^2)
    Weighted Mean Period = sum(weight * period_center) / sum(weight)
    
    For bins with 'unresolved' status or zero/NaN uncertainty, 
    the weighted mean defaults to the unweighted period center.
    """
    # Ensure we have a copy to avoid SettingWithCopyWarning
    result = df.copy()
    
    # Handle unresolved bins and NaN uncertainties
    # We only calculate weighted stats for resolved bins with valid uncertainty
    valid_mask = (result['status'] == 'resolved') & (~result['gap_uncertainty'].isna()) & (result['gap_uncertainty'] > 0)
    
    # Calculate weights (inverse variance)
    result['weight'] = np.zeros_like(result['gap_uncertainty'], dtype=float)
    result.loc[valid_mask, 'weight'] = 1.0 / (result.loc[valid_mask, 'gap_uncertainty'] ** 2)
    
    # Calculate weighted mean period
    # For resolved bins: weighted average
    # For unresolved/invalid: use the center as the mean (weight effectively 1 for display purposes, or just the center)
    result['weighted_mean_period'] = result['period_center'].copy()
    
    if valid_mask.any():
        # Group by bin_index to calculate weighted means if multiple entries per bin (though typically 1 per bin)
        # Here we assume 1 row per bin_index based on standard binning output
        # But if the input has multiple rows per bin, we aggregate:
        
        # Calculate weighted sum and total weight per bin
        valid_data = result[valid_mask].copy()
        valid_data['weighted_period_sum'] = valid_data['weight'] * valid_data['period_center']
        
        # Aggregate by bin_index
        agg = valid_data.groupby('bin_index').agg({
            'weighted_period_sum': 'sum',
            'weight': 'sum'
        }).reset_index()
        
        agg['weighted_mean_period'] = agg['weighted_period_sum'] / agg['weight']
        
        # Map back to the main dataframe
        result = result.merge(
            agg[['bin_index', 'weighted_mean_period']], 
            on='bin_index', 
            how='left', 
            suffixes=('', '_new')
        )
        
        # Update only the valid rows
        result.loc[valid_mask, 'weighted_mean_period'] = result.loc[valid_mask, 'weighted_mean_period_new']
        result = result.drop(columns=['weighted_mean_period_new'])
    
    # Ensure column types
    result['weight'] = result['weight'].astype(float)
    result['weighted_mean_period'] = result['weighted_mean_period'].astype(float)
    
    return result

def save_binned_stats(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the binned statistics to CSV.
    
    Output columns:
    - bin_index
    - period_center (original bin center)
    - weighted_mean_period (calculated)
    - gap_location
    - gap_uncertainty
    - status
    - weight (inverse variance weight)
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Select and order columns
    output_cols = [
        'bin_index', 
        'period_center', 
        'weighted_mean_period', 
        'gap_location', 
        'gap_uncertainty', 
        'status', 
        'weight'
    ]
    
    # Filter to only existing columns in case of schema drift
    existing_cols = [c for c in output_cols if c in df.columns]
    
    df[existing_cols].to_csv(path, index=False)
    logger.info(f"Saved binned statistics to {path} with {len(df)} rows")

def main():
    """
    Main entry point for T027.
    
    Input: data/processed/gap_locations.csv (from T024/T025)
    Output: data/processed/binned_stats.csv
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    input_path = project_root / "data" / "processed" / "gap_locations.csv"
    output_path = project_root / "data" / "processed" / "binned_stats.csv"
    
    logger.info(f"Starting T027: Calculating weighted mean periods")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        # Load data
        df = load_gap_locations(str(input_path))
        logger.info(f"Loaded {len(df)} gap location records")
        
        # Calculate weighted mean period
        result_df = calculate_weighted_mean_period(df)
        
        # Save output
        save_binned_stats(result_df, str(output_path))
        
        logger.info("T027 completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error("Ensure T024/T025 have been run to generate gap_locations.csv")
        return 1
    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())