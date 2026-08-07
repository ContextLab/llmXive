import numpy as np
import pandas as pd
from typing import Tuple, Optional
from pathlib import Path
import logging
import json

from config import get_logger, setup_logging

# Setup logging for this module
logger = get_logger(__name__)

# Constants
DYNE_TO_NEWTON = 1e-5
MICROMETER_TO_METER = 1e-6

def dynes_to_newtons(force_dynes: np.ndarray) -> np.ndarray:
    """
    Convert force values from dynes to Newtons.
    
    Args:
        force_dynes: Array of force values in dynes.
        
    Returns:
        Array of force values in Newtons.
    """
    if not isinstance(force_dynes, np.ndarray):
        force_dynes = np.array(force_dynes)
    return force_dynes * DYNE_TO_NEWTON

def micrometers_to_meters(distance_microns: np.ndarray) -> np.ndarray:
    """
    Convert distance values from micrometers to meters.
    
    Args:
        distance_microns: Array of distance values in micrometers.
        
    Returns:
        Array of distance values in meters.
    """
    if not isinstance(distance_microns, np.ndarray):
        distance_microns = np.array(distance_microns)
    return distance_microns * MICROMETER_TO_METER

def convert_to_si(dataset_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert all force and separation columns in the dataset to SI units.
    
    Assumes the DataFrame has columns 'force' (in dynes) and 'separation' (in micrometers).
    If columns have different names, they should be standardized before calling this function.
    
    Args:
        dataset_df: DataFrame containing raw data with dynes and micrometers.
        
    Returns:
        DataFrame with 'force_N' and 'separation_m' columns in SI units.
        Original columns are preserved for reference if needed, but new SI columns are added.
    """
    df = dataset_df.copy()
    
    # Identify force and separation columns
    # We assume standard naming from parsers: 'force', 'separation'
    force_col = None
    sep_col = None
    
    for col in df.columns:
        if 'force' in col.lower():
            force_col = col
        if 'separation' in col.lower() or 'distance' in col.lower():
            sep_col = col
    
    if force_col is None or sep_col is None:
        raise ValueError("Could not identify force and separation columns in dataset.")
    
    # Convert to SI
    df['force_N'] = dynes_to_newtons(df[force_col].values)
    df['separation_m'] = micrometers_to_meters(df[sep_col].values)
    
    logger.info(f"Converted {len(df)} rows from {force_col} (dynes) and {sep_col} (microns) to SI units.")
    
    return df

def align_to_grid(
    df_list: list[pd.DataFrame], 
    target_grid: Optional[np.ndarray] = None,
    method: str = 'linear'
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Align multiple datasets to a common separation grid.
    
    This function handles the edge case of non-overlapping separation ranges by:
    1. Detecting the intersection of valid separation ranges across all datasets.
    2. If the intersection is empty or too small, logging a warning and excluding non-overlapping regions.
    3. Interpolating missing points on the target grid for each dataset.
    
    Args:
        df_list: List of DataFrames, each containing 'separation_m' and 'force_N' (and possibly errors).
        target_grid: Optional pre-defined grid. If None, creates a grid based on the intersection of ranges.
        method: Interpolation method (default: 'linear').
        
    Returns:
        Tuple of (Aligned DataFrame with common grid, the target grid used).
        
    Raises:
        ValueError: If no overlapping range exists between datasets.
    """
    if not df_list:
        raise ValueError("df_list cannot be empty.")
    
    # Determine the overlapping range
    min_sep = -np.inf
    max_sep = np.inf
    
    for df in df_list:
        if 'separation_m' not in df.columns:
            raise ValueError("Each DataFrame must contain 'separation_m' column.")
        
        current_min = df['separation_m'].min()
        current_max = df['separation_m'].max()
        
        min_sep = max(min_sep, current_min)
        max_sep = min(max_sep, current_max)
    
    if min_sep >= max_sep:
        # No overlap
        raise ValueError(
            f"No overlapping separation range found across datasets. "
            f"Max of mins: {min_sep}, Min of maxs: {max_sep}. "
            f"Data ranges are disjoint."
        )
    
    logger.info(f"Detected overlapping separation range: [{min_sep:.2e}, {max_sep:.2e}] meters.")
    
    # Create target grid if not provided
    if target_grid is None:
        # Create a grid with sufficient resolution to capture variations
        # Typically 100-200 points in the log or linear space
        n_points = 200
        target_grid = np.linspace(min_sep, max_sep, n_points)
    
    logger.info(f"Target grid created with {len(target_grid)} points.")
    
    # Align each dataset
    aligned_dfs = []
    
    for i, df in enumerate(df_list):
        df_aligned = pd.DataFrame()
        df_aligned['separation_m'] = target_grid
        
        # Interpolate force
        # Check for non-overlapping regions in this specific dataset relative to the global grid
        # (Though we already filtered by global overlap, individual datasets might have gaps)
        x_orig = df['separation_m'].values
        y_orig = df['force_N'].values
        
        # Handle potential NaNs in original data before interpolation
        mask = ~np.isnan(x_orig) & ~np.isnan(y_orig)
        x_orig_clean = x_orig[mask]
        y_orig_clean = y_orig[mask]
        
        if len(x_orig_clean) < 2:
            logger.warning(f"Dataset {i} has insufficient points for interpolation.")
            df_aligned['force_N'] = np.nan
        else:
            try:
                y_interp = np.interp(target_grid, x_orig_clean, y_orig_clean)
                df_aligned['force_N'] = y_interp
            except Exception as e:
                logger.error(f"Interpolation failed for dataset {i}: {e}")
                df_aligned['force_N'] = np.nan
        
        # Interpolate error columns if they exist
        for col in df.columns:
            if 'err' in col.lower() or 'uncertainty' in col.lower():
                if col in df.columns:
                    x_err = df['separation_m'].values
                    y_err = df[col].values
                    mask_err = ~np.isnan(x_err) & ~np.isnan(y_err)
                    if np.sum(mask_err) >= 2:
                        y_err_interp = np.interp(target_grid, x_err[mask_err], y_err[mask_err])
                        df_aligned[col] = y_err_interp
                    else:
                        df_aligned[col] = np.nan
        
        df_aligned['source_id'] = i
        aligned_dfs.append(df_aligned)
    
    # Concatenate all aligned datasets
    result_df = pd.concat(aligned_dfs, ignore_index=True)
    
    # Log warning if any dataset had gaps that resulted in NaNs in the final grid
    nan_count = result_df['force_N'].isna().sum()
    if nan_count > 0:
        logger.warning(f"Interpolation resulted in {nan_count} NaN values in the aligned force column.")
    
    return result_df, target_grid

def construct_covariance_matrix(
    df: pd.DataFrame,
    stat_col: str = 'stat_err',
    sys_col: Optional[str] = None
) -> np.ndarray:
    """
    Construct a covariance matrix from statistical and systematic uncertainties.
    
    Args:
        df: DataFrame with 'force_N' and uncertainty columns.
        stat_col: Name of the statistical error column.
        sys_col: Optional name of the systematic error column.
        
    Returns:
        2D numpy array representing the covariance matrix.
    """
    n = len(df)
    cov = np.zeros((n, n))
    
    # Diagonal: sum of squares of statistical and systematic errors
    stat_err = df[stat_col].values if stat_col in df.columns else np.zeros(n)
    
    if sys_col and sys_col in df.columns:
        sys_err = df[sys_col].values
        # Assuming systematic errors are fully correlated across the dataset?
        # Or diagonal? The task says "full covariance matrix (with fallback to banded)".
        # Standard practice: Statistical is diagonal, Systematic might be correlated.
        # For now, we assume diagonal for both unless specified otherwise in spec.
        # If systematic is fully correlated, the matrix is rank-1 + diagonal.
        # Let's assume diagonal for simplicity unless the spec implies full correlation.
        # Re-reading: "construct a full covariance matrix". Usually implies off-diagonals.
        # If systematic is a constant bias, Cov(i,j) = sys^2 for all i,j.
        # Let's implement the fully correlated systematic case as it's common in force laws.
        
        # Diagonal elements: stat^2 + sys^2
        # Off-diagonal: sys^2
        diag = stat_err**2 + sys_err**2
        off_diag = sys_err**2 # Assuming constant systematic error magnitude across points?
        # Actually, systematic error might be a function of distance.
        # If sys_err is a vector, we assume it's the same bias for all points (fully correlated).
        # Then Cov = diag(stat^2) + outer(sys, sys)
        
        # Let's assume sys_err is a scalar or a vector of the same length.
        # If vector, we treat it as the magnitude of the correlated component.
        # A common model: total error = sqrt(stat^2 + sys^2).
        # Covariance: diag(stat^2) + sys_vec * sys_vec^T (if fully correlated)
        
        # Implementation:
        # 1. Diagonal
        np.fill_diagonal(cov, stat_err**2)
        # 2. Add systematic correlation
        # If sys_err is a vector, we add outer product.
        # If sys_err is a scalar (constant bias), we add scalar^2 to all.
        if isinstance(sys_err, np.ndarray) and len(sys_err) > 0:
            # If it varies, we assume the variation is the correlated component?
            # This is ambiguous. Let's assume a constant systematic uncertainty 
            # derived from the mean or max of the sys_err column if it varies,
            # or just use the vector as the correlated component.
            # Simplest robust approach: Assume sys_err column represents the 
            # magnitude of the fully correlated error at each point.
            # Cov_ij = sys_i * sys_j
            cov += np.outer(sys_err, sys_err)
        else:
            cov += sys_err**2
    else:
        # Only statistical errors -> diagonal matrix
        np.fill_diagonal(cov, stat_err**2)
    
    return cov

def harmonize_experiment(
    data_paths: list[Path],
    output_path: Path,
    target_grid: Optional[np.ndarray] = None
) -> dict:
    """
    Main orchestration function for harmonizing multiple experiment datasets.
    
    Steps:
    1. Load raw CSVs.
    2. Convert to SI units.
    3. Align to a common grid.
    4. Construct covariance matrix.
    5. Save results.
    
    Args:
        data_paths: List of paths to raw CSV files.
        output_path: Path to save the harmonized dataset (CSV) and covariance (NPY).
        target_grid: Optional custom grid.
        
    Returns:
        Dictionary with metadata about the harmonization process.
    """
    logger.info(f"Starting harmonization for {len(data_paths)} datasets.")
    
    dfs = []
    for p in data_paths:
        logger.info(f"Loading {p}")
        df = pd.read_csv(p)
        dfs.append(df)
    
    # Convert to SI
    si_dfs = [convert_to_si(df) for df in dfs]
    
    # Align to grid
    try:
        aligned_df, grid = align_to_grid(si_dfs, target_grid=target_grid)
    except ValueError as e:
        logger.error(f"Grid alignment failed: {e}")
        # Fallback: exclude non-overlapping regions?
        # The spec says: "interpolate missing points or exclude non-overlapping regions and log a warning"
        # Our align_to_grid already handles exclusion by defining the grid on the intersection.
        # If intersection is empty, it raises. We caught that.
        raise
    
    # Construct covariance
    # We need to group by source to calculate covariance per source or globally?
    # The task implies a single covariance matrix for the combined dataset.
    # If data is from different experiments, we might need block diagonal.
    # For now, assume we are treating them as one combined dataset for the fit.
    # We need to identify error columns.
    # Let's assume standard names: 'stat_err' and 'sys_err' exist after parsing.
    # If not, we might need to infer.
    
    # Check for error columns
    stat_col = 'stat_err'
    sys_col = 'sys_err'
    
    if stat_col not in aligned_df.columns:
        # Try to find any column with 'err'
        err_cols = [c for c in aligned_df.columns if 'err' in c.lower()]
        if err_cols:
            stat_col = err_cols[0]
            logger.warning(f"Using '{stat_col}' as statistical error column.")
        else:
            logger.warning("No statistical error column found. Assuming zero error.")
            aligned_df[stat_col] = 0.0
    
    if sys_col not in aligned_df.columns:
        # Try to find systematic
        sys_candidates = [c for c in aligned_df.columns if 'sys' in c.lower()]
        if sys_candidates:
            sys_col = sys_candidates[0]
        else:
            sys_col = None
            logger.warning("No systematic error column found.")
    
    cov_matrix = construct_covariance_matrix(aligned_df, stat_col=stat_col, sys_col=sys_col)
    
    # Save outputs
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    csv_path = output_path.with_suffix('.csv')
    aligned_df.to_csv(csv_path, index=False)
    logger.info(f"Saved harmonized data to {csv_path}")
    
    # Save Covariance
    cov_path = output_path.with_suffix('.npy')
    np.save(cov_path, cov_matrix)
    logger.info(f"Saved covariance matrix to {cov_path}")
    
    # Save metadata
    meta = {
        "n_datasets": len(data_paths),
        "n_points": len(aligned_df),
        "grid_range": [float(grid.min()), float(grid.max())],
        "cov_shape": list(cov_matrix.shape),
        "stat_col": stat_col,
        "sys_col": sys_col
    }
    
    meta_path = output_path.with_suffix('.json')
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    
    return meta

def main():
    """Entry point for command-line execution."""
    setup_logging()
    
    # Example usage - in real pipeline, paths come from config or args
    # This is a placeholder for the actual invocation logic
    logger.info("harmonize.py module loaded.")
    logger.info("Use harmonize_experiment() with data paths to run.")

if __name__ == "__main__":
    main()
