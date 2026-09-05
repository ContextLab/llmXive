"""
Module for calculating binned statistics, specifically the weighted mean period.

This module implements Task T027: Calculate 'weighted mean period' using 
inverse variance of the gap location estimate for each bin.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GAP_LOCATIONS_PATH = PROJECT_ROOT / "data" / "processed" / "gap_locations.csv"
BINNED_STATS_PATH = PROJECT_ROOT / "data" / "processed" / "binned_stats.csv"


def load_gap_locations(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the gap locations dataset produced by the GMM analysis.
    
    Args:
        path: Optional path to the gap locations CSV. Defaults to 
              data/processed/gap_locations.csv.
    
    Returns:
        DataFrame containing bin statistics and gap location estimates.
    
    Raises:
        FileNotFoundError: If the gap locations file does not exist.
        ValueError: If required columns are missing.
    """
    if path is None:
        path = GAP_LOCATIONS_PATH
    
    if not path.exists():
        raise FileNotFoundError(
            f"Gap locations file not found at {path}. "
            "Ensure T028 (or the preceding GMM/binning steps) has been run successfully."
        )
    
    df = pd.read_csv(path)
    
    required_columns = ['bin_index', 'gap_location', 'gap_uncertainty', 'period_center']
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(
            f"Gap locations file is missing required columns: {missing}. "
            "Expected columns: {required_columns}"
        )
    
    logger.info(f"Loaded {len(df)} gap location records from {path}")
    return df


def calculate_weighted_mean_period(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the weighted mean period for each bin using inverse variance weighting.
    
    The weight for each bin is calculated as w = 1 / (sigma^2), where sigma is the
    gap location uncertainty. The weighted mean period is then:
        P_weighted = sum(w_i * P_i) / sum(w_i)
    
    This metric provides a more robust estimate of the characteristic period for
    a bin when gap location uncertainties vary significantly.
    
    Args:
        df: DataFrame containing 'bin_index', 'gap_location', 'gap_uncertainty', 
            and 'period_center' columns.
    
    Returns:
        DataFrame with an additional 'weighted_mean_period' column.
    
    Raises:
        ValueError: If uncertainty values are non-positive or zero.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df.copy()
    
    # Calculate weights: inverse variance
    # Add a small epsilon to avoid division by zero if uncertainty is 0
    epsilon = 1e-10
    uncertainties = df['gap_uncertainty'].values
    
    if np.any(uncertainties <= 0):
        # Handle zero or negative uncertainties by replacing with epsilon
        logger.warning(
            "Detected zero or negative uncertainties. Replacing with small epsilon."
        )
        uncertainties = np.where(
            uncertainties <= 0, 
            epsilon, 
            uncertainties
        )
    
    weights = 1.0 / (uncertainties ** 2)
    
    # Calculate weighted mean period
    # Using the period_center as the period value for each bin
    periods = df['period_center'].values
    weighted_sum = np.sum(weights * periods)
    weight_total = np.sum(weights)
    
    if weight_total == 0:
        raise ValueError(
            "Total weight is zero. Cannot calculate weighted mean period. "
            "Check that gap_uncertainty values are finite and positive."
        )
    
    weighted_mean_period = weighted_sum / weight_total
    
    # Add to DataFrame
    result_df = df.copy()
    result_df['weighted_mean_period'] = weighted_mean_period
    
    # Log summary
    logger.info(
        f"Calculated weighted mean period: {weighted_mean_period:.4f} days "
        f"(using {len(df)} bins)"
    )
    
    return result_df


def save_binned_stats(df: pd.DataFrame, path: Optional[Path] = None) -> Path:
    """
    Save the binned statistics DataFrame to a CSV file.
    
    Args:
        df: DataFrame containing binned statistics including weighted_mean_period.
        path: Optional output path. Defaults to data/processed/binned_stats.csv.
    
    Returns:
        Path to the saved file.
    
    Raises:
        IOError: If the file cannot be written.
    """
    if path is None:
        path = BINNED_STATS_PATH
    
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        df.to_csv(path, index=False)
        logger.info(f"Saved binned statistics to {path} ({len(df)} rows)")
        return path
    except Exception as e:
        logger.error(f"Failed to save binned statistics to {path}: {e}")
        raise IOError(f"Could not write file {path}: {e}")


def main() -> int:
    """
    Main entry point for the binned statistics calculation.
    
    This function orchestrates the loading of gap locations, calculation of
    weighted mean periods, and saving of the results.
    
    Returns:
        0 on success, 1 on failure.
    """
    logger.info("Starting binned statistics calculation (Task T027)")
    
    try:
        # Load gap locations
        gap_df = load_gap_locations()
        
        # Calculate weighted mean period
        stats_df = calculate_weighted_mean_period(gap_df)
        
        # Save results
        output_path = save_binned_stats(stats_df)
        
        logger.info("Binned statistics calculation completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during binned statistics calculation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())