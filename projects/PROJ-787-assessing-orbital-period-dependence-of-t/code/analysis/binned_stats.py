"""
Module for calculating binned statistics, specifically the weighted mean period.

This module implements the calculation of 'weighted mean period' using the inverse
variance of the gap location estimate for each bin, as required by FR-003 and T027.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import numpy as np

# Configure logger for this module
logger = logging.getLogger(__name__)

# Default paths relative to project root
DEFAULT_GAP_LOCATIONS_PATH = "data/processed/gap_locations.csv"
DEFAULT_OUTPUT_PATH = "data/processed/binned_stats.csv"


def load_gap_locations(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the gap locations dataframe containing bin definitions and gap estimates.

    Args:
        file_path: Path to the gap locations CSV. Defaults to DEFAULT_GAP_LOCATIONS_PATH.

    Returns:
        pd.DataFrame: The loaded dataframe.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(file_path) if file_path else Path(DEFAULT_GAP_LOCATIONS_PATH)
    
    if not path.exists():
        raise FileNotFoundError(f"Gap locations file not found at {path}. "
                                "Ensure T028 (or the preceding GMM step) has run.")

    logger.info(f"Loading gap locations from {path}")
    df = pd.read_csv(path)

    required_cols = ['bin_index', 'gap_location', 'gap_uncertainty']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Gap locations file missing required columns: {missing_cols}")

    return df


def calculate_weighted_mean_period(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the weighted mean period for each bin using inverse variance weighting.

    The weight is defined as 1 / (gap_uncertainty^2). The weighted mean period is
    calculated based on the period distribution of planets within that bin, 
    weighted by the precision of the gap location estimate for that bin.
    
    However, typically 'weighted mean period' in this context refers to the 
    representative period of the bin itself, weighted by the reliability (inverse variance)
    of the gap measurement to determine the bin's significance in subsequent regression.
    
    Implementation logic per T027:
    1. Calculate weight = 1 / (gap_uncertainty^2) for each bin.
    2. Calculate the mean period of planets in the bin (if raw planet data is available) 
       OR use the bin center as the period. 
       Since this script operates on gap_locations (aggregated), we will calculate the 
       weighted mean of the bin centers across the dataset if aggregating, 
       OR simply attach the weight and the effective period (bin center) to the row.
       
    Refinement based on T027 description: "outputting to data/processed/binned_stats.csv"
    We assume the input `gap_locations.csv` contains the bin center (e.g., 'bin_center_logP' 
    or we calculate it from 'period_min'/'period_max'). 
    
    If 'period_center' is not present, we derive it from log-spaced bin edges if available,
    or assume the 'gap_location' context implies we need the period associated with that gap.
    
    Assumption: The input dataframe has a 'period_center' or we compute it. 
    If not present, we check for 'bin_min' and 'bin_max' to compute geometric mean.
    If neither, we assume the bin is represented by the 'gap_location' row's context, 
    but we need a period value. 
    
    Let's look at standard binning outputs: usually 'bin_center' or 'logP_center'.
    If missing, we might need to load the binned_planets.csv to get the mean period per bin.
    
    Strategy:
    1. Check for 'period_center' or 'logP_center'.
    2. If missing, try to load 'data/processed/binned_planets.csv' to get the mean period per bin_index.
    3. Calculate weights: w = 1 / (gap_uncertainty^2).
    4. Compute weighted mean period for the bin (if multiple entries per bin? No, usually one per bin).
       Actually, the task says "weighted mean period ... for each bin". 
       This likely means: For each bin, we have a gap estimate. We want the period value 
       associated with that bin, weighted by the inverse variance of the gap.
       This is effectively the bin's representative period, but we must handle the weighting 
       if we are aggregating bins later, or simply output the weight and the period.
       
    Interpretation: The output should contain the bin's period (center) and the calculated weight.
    The "weighted mean period" might be a misnomer in the task description if it's just one value per bin,
    UNLESS it refers to the weighted average of periods of planets *within* the bin, 
    weighted by the gap uncertainty? No, gap uncertainty is a property of the bin's fit.
    
    Correct Interpretation for Regression (T032):
    We need (X, Y, sigma_Y) for regression. X = log(period), Y = gap_radius, sigma_Y = gap_uncertainty.
    The "weighted mean period" likely refers to the robust estimate of the period for that bin,
    perhaps calculated from the planets in that bin, and then we associate the gap uncertainty.
    
    Let's implement:
    1. Load gap_locations.
    2. If 'period_center' is missing, load binned_planets to compute mean period per bin.
    3. Calculate weight = 1 / (gap_uncertainty^2).
    4. Output: bin_index, period_center, gap_location, gap_uncertainty, weight.
    
    If the task implies calculating a single "weighted mean period" for the *entire* dataset,
    that would be a scalar. But it says "for each bin", so it's a column.
    
    Let's assume the input has 'bin_index' and 'gap_uncertainty'.
    We will compute the mean period of planets in that bin if we can, or use the bin center.
    To be safe and robust, we will try to load `binned_planets.csv` to get the actual mean period.
    """
    
    logger.info("Calculating weighted mean period and weights for each bin.")
    
    # Ensure we have a period value
    if 'period_center' not in df.columns:
        # Try to load binned_planets to get mean period per bin
        binned_path = Path("data/processed/binned_planets.csv")
        if binned_path.exists():
            logger.info("Loading binned_planets.csv to derive period centers.")
            binned_df = pd.read_csv(binned_path)
            if 'period_center' in binned_df.columns:
                # Aggregate if necessary (though it should be one row per bin)
                period_map = binned_df.set_index('bin_index')['period_center'].to_dict()
                df['period_center'] = df['bin_index'].map(period_map)
            elif 'mean_period' in binned_df.columns:
                period_map = binned_df.set_index('bin_index')['mean_period'].to_dict()
                df['period_center'] = df['bin_index'].map(period_map)
            else:
                # Fallback: geometric mean of bin edges if available
                if 'period_min' in binned_df.columns and 'period_max' in binned_df.columns:
                    binned_df['period_center'] = np.sqrt(binned_df['period_min'] * binned_df['period_max'])
                    period_map = binned_df.set_index('bin_index')['period_center'].to_dict()
                    df['period_center'] = df['bin_index'].map(period_map)
        
        # If still missing, we cannot proceed accurately.
        if 'period_center' not in df.columns:
            # Fallback: assume gap_location is not period, but we might have logP_min/max
            # If no period info, we raise an error or use a placeholder (bad practice).
            # Let's raise an error to fail loudly as per constraints.
            raise ValueError("Could not determine period_center for bins. "
                             "Ensure 'data/processed/binned_planets.csv' contains period information "
                             "or 'data/processed/gap_locations.csv' has period columns.")

    # Calculate inverse variance weights
    # Avoid division by zero
    df = df.copy()
    df['gap_uncertainty'] = df['gap_uncertainty'].replace(0, np.nan).fillna(1e-10)
    df['weight'] = 1.0 / (df['gap_uncertainty'] ** 2)
    
    # The "weighted mean period" for a bin is simply the period_center if we are treating the bin as a point.
    # However, if the task implies re-weighting the period based on the gap fit quality?
    # Usually in regression: X = log(period), weight = 1/var(Y).
    # The "weighted mean period" column in the output likely serves as the X value for regression.
    # We will output 'period_center' as the representative period.
    
    logger.info(f"Calculated weights. Min weight: {df['weight'].min():.2e}, Max weight: {df['weight'].max():.2e}")
    
    return df


def save_binned_stats(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Save the binned statistics dataframe to CSV.

    Args:
        df: The dataframe with calculated weights and periods.
        output_path: Path for the output file. Defaults to DEFAULT_OUTPUT_PATH.

    Returns:
        str: The path to the saved file.
    """
    path = Path(output_path) if output_path else Path(DEFAULT_OUTPUT_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving binned stats to {path}")
    df.to_csv(path, index=False)
    
    logger.info(f"Successfully saved {len(df)} rows to {path}")
    return str(path)


def main():
    """
    Main entry point for the T027 task.
    
    Flow:
    1. Load gap_locations.csv (from T024/T028).
    2. Calculate weighted mean period (and weights).
    3. Save to binned_stats.csv.
    """
    # Setup logging
    log_file = Path("data/processed/logs/binned_stats.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    try:
        # Load data
        gap_df = load_gap_locations()
        
        # Process
        stats_df = calculate_weighted_mean_period(gap_df)
        
        # Save
        output_file = save_binned_stats(stats_df)
        
        logger.info("T027 completed successfully.")
        print(f"Output written to: {output_file}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()