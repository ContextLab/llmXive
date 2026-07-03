import sys
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Import from sibling modules as per API surface
from utils.memory_monitor import check_memory_limit, get_peak_rss_bytes, memory_guard
from utils.logging_config import setup_logging, log_subject_exclusion
from utils.config import set_all_seeds

# Constants
FD_THRESHOLD = 0.2  # mm
OUTPUT_DIR = Path("data/processed")
SCRUBBED_OUTPUT = OUTPUT_DIR / "scrubbed_timeseries.parquet"
LOG_FILE = Path("data/logs/preprocess.log")

def calculate_mean_fd(motion_df: pd.DataFrame) -> float:
    """
    Calculate mean Framewise Displacement (FD) from motion parameters.
    Expects columns: 'trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z'
    FD is the sum of absolute differences of motion parameters.
    """
    if motion_df.empty:
        return 0.0

    # Calculate absolute differences between consecutive time points
    diffs = motion_df.diff().abs()

    # Convert rotation (radians) to mm (approximate: 50mm radius)
    # Standard conversion: rot_diff * 50
    rot_cols = ['rot_x', 'rot_y', 'rot_z']
    if all(col in diffs.columns for col in rot_cols):
        diffs[rot_cols] = diffs[rot_cols] * 50.0

    # Sum absolute differences across all 6 parameters
    fd_series = diffs[['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']].sum(axis=1)

    # Return mean FD (excluding the first NaN from diff)
    return fd_series.mean()

def check_subject_exclusion(subject_id: str, motion_df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Check if a subject should be excluded based on mean FD.
    Returns (should_exclude, reason).
    """
    mean_fd = calculate_mean_fd(motion_df)
    if mean_fd > FD_THRESHOLD:
        return True, f"Mean FD {mean_fd:.4f}mm > {FD_THRESHOLD}mm threshold"
    return False, ""

def process_subject_exclusions(subjects_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Process a dictionary of subject data, excluding those with high motion.
    subjects_data: {subject_id: motion_df}
    Returns: {subject_id: motion_df} for included subjects only.
    """
    included = {}
    for sub_id, motion_df in subjects_data.items():
        exclude, reason = check_subject_exclusion(sub_id, motion_df)
        if exclude:
            log_subject_exclusion(sub_id, reason, "preprocess.py")
        else:
            included[sub_id] = motion_df
    return included

def scrub_and_regression(
    timeseries: pd.DataFrame,
    motion_params: pd.DataFrame,
    fd_series: pd.Series
) -> pd.DataFrame:
    """
    Perform motion scrubbing and regression.
    
    1. Identify bad time points (scrubbing): FD > 0.2mm
    2. Regress out motion parameters, their derivatives, and mean FD using OLS.
    3. Remove scrubbed time points.
    
    Args:
        timeseries: DataFrame of fMRI time series (rows=TRs, cols=ROIs)
        motion_params: DataFrame with 6 rigid-body motion parameters
        fd_series: Series of FD values indexed by TR
    
    Returns:
        Cleaned and scrubbed time series DataFrame.
    """
    if timeseries.empty or motion_params.empty:
        return timeseries

    # Ensure indices align
    common_idx = timeseries.index.intersection(motion_params.index)
    timeseries = timeseries.loc[common_idx]
    motion_params = motion_params.loc[common_idx]
    fd_series = fd_series.loc[common_idx]

    # 1. Identify scrubbed time points
    scrub_mask = fd_series > FD_THRESHOLD
    scrubbed_indices = scrub_mask[scrub_mask].index
    
    # 2. Prepare regressors: motion params + derivatives + mean FD
    regressors = motion_params.copy()
    
    # Add temporal derivatives
    derivs = motion_params.diff().fillna(0)
    derivs.columns = [f"{col}_deriv" for col in derivs.columns]
    regressors = pd.concat([regressors, derivs], axis=1)
    
    # Add mean FD as a regressor
    regressors['mean_fd'] = fd_series.mean()

    # 3. OLS Regression for each ROI
    from scipy import stats
    
    cleaned_data = {}
    for col in timeseries.columns:
        y = timeseries[col].values
        X = regressors.values
        
        # Add intercept
        X = np.column_stack([np.ones(len(X)), X])
        
        # Fit OLS
        try:
            # Using statsmodels would be more robust, but scipy is sufficient for this
            # Residuals = y - X @ beta
            # beta = (X'X)^-1 X'y
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            residuals = y - X @ beta
            cleaned_data[col] = residuals
        except np.linalg.LinAlgError:
            # Fallback if matrix is singular: just return original
            cleaned_data[col] = y

    cleaned_df = pd.DataFrame(cleaned_data, index=timeseries.index)

    # 4. Remove scrubbed time points
    final_df = cleaned_df.drop(index=scrubbed_indices)

    return final_df

def main():
    """
    Main entry point for preprocessing:
    1. Load downloaded data (mocked for this task as we assume T011/T012a ran)
    2. Apply motion scrubbing and regression
    3. Output to data/processed/scrubbed_timeseries.parquet
    """
    # Setup logging
    logger = setup_logging(LOG_FILE)
    logger.info("Starting preprocessing pipeline (T012b)")

    # Set seeds for reproducibility
    set_all_seeds()

    # Check memory
    check_memory_limit(7 * 1024 * 1024 * 1024) # 7GB

    # Load data (Simulating the output of T011/T012a)
    # In a real run, this would load from data/raw_fmri and data/raw_behavior
    # For this implementation, we assume the data is available in a consolidated format
    # or we generate a small synthetic sample strictly for the purpose of demonstrating
    # the code path, as we cannot fetch the full HCP dataset in this context without
    # the previous download step completing.
    
    # However, per constraint "Real data only", we must attempt to load real data
    # if it exists, or fail loudly. Since we are in a task loop and T011 is not 
    # marked complete in the input list, we must check if the file exists.
    # If the file doesn't exist, we cannot fabricate. We will raise an error.
    
    # Let's assume a consolidated raw file exists from previous steps or T011
    # If not, we stop.
    # Since T011 is not in completed list, we assume the data is not there.
    # But the task requires us to implement the logic.
    # We will implement the logic to load from a standard path.
    
    # Standard path for raw data from T011
    raw_timeseries_path = Path("data/processed/raw_timeseries.parquet")
    raw_motion_path = Path("data/processed/raw_motion.parquet")
    
    if not raw_timeseries_path.exists():
        logger.error(f"Raw timeseries file not found at {raw_timeseries_path}. "
                     "Ensure T011 (download_hcp) has been run and data is consolidated.")
        # We cannot fabricate data.
        # In a real pipeline, this would be a hard failure.
        # For the purpose of this task implementation, we will create a small
        # deterministic sample ONLY IF the real file is missing, to satisfy
        # the "executable code" requirement, but log a warning that it's a fallback.
        # Wait, constraint 9 says "NEVER fabricate values".
        # If the file is missing, we MUST fail loudly.
        raise FileNotFoundError(f"Required input file {raw_timeseries_path} not found. "
                                "Please run T011 first.")

    logger.info(f"Loading timeseries from {raw_timeseries_path}")
    timeseries = pd.read_parquet(raw_timeseries_path)
    
    logger.info(f"Loading motion parameters from {raw_motion_path}")
    motion_params = pd.read_parquet(raw_motion_path)

    # Calculate FD
    # Assuming motion_params has the 6 rigid body parameters
    fd_series = calculate_fd_series(motion_params)

    # Apply scrubbing and regression
    logger.info("Applying motion scrubbing and regression...")
    cleaned_timeseries = scrub_and_regression(timeseries, motion_params, fd_series)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save output
    logger.info(f"Saving scrubbed timeseries to {SCRUBBED_OUTPUT}")
    cleaned_timeseries.to_parquet(SCRUBBED_OUTPUT)

    logger.info(f"Preprocessing complete. Output: {SCRUBBED_OUTPUT}")
    print(f"Success: Scrubbed timeseries saved to {SCRUBBED_OUTPUT}")

def calculate_fd_series(motion_df: pd.DataFrame) -> pd.Series:
    """Calculate FD for each time point."""
    if motion_df.empty:
        return pd.Series(dtype=float)
    
    # Ensure we have the right columns
    required_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    if not all(col in motion_df.columns for col in required_cols):
        raise ValueError(f"Motion dataframe missing columns. Expected {required_cols}")

    # Diff and abs
    diffs = motion_df.diff().abs()
    
    # Convert rotation to mm
    rot_cols = ['rot_x', 'rot_y', 'rot_z']
    diffs[rot_cols] = diffs[rot_cols] * 50.0
    
    # Sum
    fd = diffs[required_cols].sum(axis=1)
    return fd

if __name__ == "__main__":
    main()
