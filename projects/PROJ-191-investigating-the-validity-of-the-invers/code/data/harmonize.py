"""
Harmonization module for inverse-square law experiment data.

Handles unit conversion (dynes to Newtons, micrometers to meters),
grid alignment across multiple experimental runs, and edge-case
handling for non-overlapping separation ranges.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path
import logging
import json
from scipy.interpolate import interp1d
from scipy.stats import linregress
import warnings

from config import get_logger
from data.models import HarmonizedDataset

logger = get_logger(__name__)

# Constants
DYNE_TO_NEWTON = 1e-5
MICROMETER_TO_METER = 1e-6

def dynes_to_newtons(force_dyne: np.ndarray) -> np.ndarray:
    """
    Convert force from dynes to Newtons.
    
    Args:
        force_dyne: Array of force values in dynes.
        
    Returns:
        Array of force values in Newtons.
    """
    if not isinstance(force_dyne, np.ndarray):
        force_dyne = np.array(force_dyne)
    return force_dyne * DYNE_TO_NEWTON

def micrometers_to_meters(separation_um: np.ndarray) -> np.ndarray:
    """
    Convert separation distance from micrometers to meters.
    
    Args:
        separation_um: Array of separation distances in micrometers.
        
    Returns:
        Array of separation distances in meters.
    """
    if not isinstance(separation_um, np.ndarray):
        separation_um = np.array(separation_um)
    return separation_um * MICROMETER_TO_METER

def convert_to_si(df: pd.DataFrame, force_col: str = 'force_dyne', 
                 separation_col: str = 'separation_um') -> pd.DataFrame:
    """
    Convert force and separation columns in a DataFrame to SI units.
    
    Args:
        df: Input DataFrame with force and separation data.
        force_col: Name of the force column (expected in dynes).
        separation_col: Name of the separation column (expected in micrometers).
        
    Returns:
        DataFrame with converted SI units (Newtons, meters).
    """
    df = df.copy()
    
    if force_col in df.columns:
        df[force_col.replace('force', 'force_n')] = dynes_to_newtons(df[force_col].values)
        logger.debug(f"Converted {force_col} to Newtons")
    else:
        logger.warning(f"Force column '{force_col}' not found in DataFrame")
        
    if separation_col in df.columns:
        df[separation_col.replace('separation', 'separation_m')] = micrometers_to_meters(df[separation_col].values)
        logger.debug(f"Converted {separation_col} to meters")
    else:
        logger.warning(f"Separation column '{separation_col}' not found in DataFrame")
        
    return df

def align_to_grid(dataframes: List[pd.DataFrame], 
                 target_separation: Optional[np.ndarray] = None,
                 method: str = 'linear',
                 fill_value: float = np.nan) -> Tuple[List[pd.DataFrame], np.ndarray]:
    """
    Align multiple datasets to a common separation grid.
    
    Args:
        dataframes: List of DataFrames, each containing 'separation_m' and 'force_n' columns.
        target_separation: Optional target grid. If None, uses the union of all separation points.
        method: Interpolation method ('linear', 'nearest', 'cubic', etc.).
        fill_value: Value to use for extrapolation.
        
    Returns:
        Tuple of (aligned_dataframes, target_separation_grid).
        
    Raises:
        ValueError: If no overlapping regions exist between datasets.
    """
    if not dataframes:
        raise ValueError("No dataframes provided for alignment")
        
    # Determine target grid
    if target_separation is None:
        all_separations = []
        for df in dataframes:
            if 'separation_m' in df.columns:
                all_separations.extend(df['separation_m'].dropna().values)
        
        if not all_separations:
            raise ValueError("No valid separation data found in any dataframe")
            
        # Create a dense grid covering the union of all ranges
        min_sep = min(all_separations)
        max_sep = max(all_separations)
        # Use a fine grid (e.g., 1000 points) for alignment
        target_separation = np.linspace(min_sep, max_sep, 1000)
        logger.info(f"Generated target grid from {min_sep:.6e} to {max_sep:.6e} m with 1000 points")
    else:
        target_separation = np.array(target_separation)
        
    aligned_dfs = []
    non_overlapping_ranges = []
    
    for i, df in enumerate(dataframes):
        if 'separation_m' not in df.columns or 'force_n' not in df.columns:
            logger.error(f"DataFrame {i} missing required columns")
            continue
            
        sep = df['separation_m'].values
        force = df['force_n'].values
        
        # Check for valid data
        valid_mask = ~(np.isnan(sep) | np.isnan(force))
        if not np.any(valid_mask):
            logger.warning(f"DataFrame {i} has no valid data points")
            aligned_dfs.append(df)
            continue
            
        valid_sep = sep[valid_mask]
        valid_force = force[valid_mask]
        
        # Check for overlapping region with target grid
        df_min = np.min(valid_sep)
        df_max = np.max(valid_sep)
        target_min = np.min(target_separation)
        target_max = np.max(target_separation)
        
        overlap_min = max(df_min, target_min)
        overlap_max = min(df_max, target_max)
        
        if overlap_min >= overlap_max:
            warning_msg = (f"DataFrame {i} has no overlap with target grid. "
                         f"Data range: [{df_min:.6e}, {df_max:.6e}], "
                         f"Target range: [{target_min:.6e}, {target_max:.6e}]")
            logger.warning(warning_msg)
            non_overlapping_ranges.append({
                'dataset_index': i,
                'data_range': (df_min, df_max),
                'target_range': (target_min, target_max)
            })
            # Create empty aligned dataframe
            aligned_df = pd.DataFrame({
                'separation_m': target_separation,
                'force_n': np.full(len(target_separation), fill_value)
            })
            aligned_dfs.append(aligned_df)
            continue
        
        # Create interpolation function
        try:
            f_interp = interp1d(valid_sep, valid_force, kind=method, 
                              bounds_error=False, fill_value=fill_value)
            
            # Interpolate to target grid
            aligned_force = f_interp(target_separation)
            
            # Log warning if extrapolation occurred
            extrapolated_mask = (target_separation < df_min) | (target_separation > df_max)
            if np.any(extrapolated_mask):
                n_extrap = np.sum(extrapolated_mask)
                logger.warning(f"DataFrame {i}: {n_extrap} points extrapolated beyond data range")
                
        except ValueError as e:
            logger.error(f"Interpolation failed for DataFrame {i}: {e}")
            aligned_force = np.full(len(target_separation), fill_value)
            
        aligned_df = pd.DataFrame({
            'separation_m': target_separation,
            'force_n': aligned_force
        })
        
        # Preserve other columns if they exist
        for col in df.columns:
            if col not in ['separation_m', 'force_n', 'separation_um', 'force_dyne']:
                aligned_df[col] = df[col].values if len(df) == len(target_separation) else np.nan
                
        aligned_dfs.append(aligned_df)
        
    if non_overlapping_ranges:
        logger.warning(f"Found {len(non_overlapping_ranges)} datasets with no overlap. "
                     "These will be filled with NaN values in the aligned grid.")
        
    return aligned_dfs, target_separation

def harmonize_experiment(raw_data_paths: List[Path], 
                        output_path: Path,
                        force_col: str = 'force_dyne',
                        separation_col: str = 'separation_um',
                        grid_method: str = 'linear') -> HarmonizedDataset:
    """
    Main harmonization pipeline for a single experiment.
    
    1. Load raw CSV files
    2. Convert to SI units
    3. Align to common grid
    4. Construct covariance matrix (diagonal for now)
    5. Save to output path
    
    Args:
        raw_data_paths: List of paths to raw CSV files.
        output_path: Path to save the harmonized dataset.
        force_col: Column name for force in raw data.
        separation_col: Column name for separation in raw data.
        grid_method: Interpolation method for grid alignment.
        
    Returns:
        HarmonizedDataset object.
    """
    logger.info(f"Starting harmonization for {len(raw_data_paths)} files")
    
    # Load and convert to SI
    dfs_si = []
    for path in raw_data_paths:
        if not path.exists():
            logger.error(f"File not found: {path}")
            continue
            
        try:
            df = pd.read_csv(path)
            logger.debug(f"Loaded {path}: {len(df)} rows")
            
            df_si = convert_to_si(df, force_col=force_col, separation_col=separation_col)
            dfs_si.append(df_si)
            logger.info(f"Successfully converted {path} to SI units")
            
        except Exception as e:
            logger.error(f"Failed to process {path}: {e}")
            continue
            
    if not dfs_si:
        raise ValueError("No valid data files processed")
        
    # Align to common grid
    aligned_dfs, target_grid = align_to_grid(
        dfs_si, 
        method=grid_method,
        fill_value=np.nan
    )
    
    # Combine into single dataset
    # For now, take the mean of aligned forces where data exists
    # In a full implementation, we might weight by uncertainty
    combined_force = np.zeros(len(target_grid))
    combined_count = np.zeros(len(target_grid))
    combined_var = np.zeros(len(target_grid))
    
    for df in aligned_dfs:
        force = df['force_n'].values
        valid = ~np.isnan(force)
        combined_force[valid] += force[valid]
        combined_count[valid] += 1
        if np.any(valid):
            # Simple variance estimation from the single point (placeholder)
            # In reality, we'd use the reported uncertainties
            combined_var[valid] += (force[valid] - np.mean(force[valid]))**2
            
    # Average
    valid_count = combined_count > 0
    final_force = np.full(len(target_grid), np.nan)
    final_force[valid_count] = combined_force[valid_count] / combined_count[valid_count]
    
    # Estimate uncertainty (placeholder: use standard error of mean if multiple sources)
    final_uncertainty = np.full(len(target_grid), np.nan)
    if np.any(valid_count):
        # Placeholder: assume 1% uncertainty for now
        final_uncertainty[valid_count] = np.abs(final_force[valid_count]) * 0.01
        
    # Construct covariance matrix (diagonal for now)
    # In a full implementation, this would combine statistical and systematic errors
    covariance_matrix = np.diag(final_uncertainty[valid_count]**2)
    
    # Create metadata
    metadata = {
        'source_files': [str(p) for p in raw_data_paths],
        'grid_method': grid_method,
        'target_grid_range': [float(np.min(target_grid)), float(np.max(target_grid))],
        'target_grid_points': int(len(target_grid)),
        'valid_points': int(np.sum(valid_count)),
        'conversion_factors': {
            'force': DYNE_TO_NEWTON,
            'separation': MICROMETER_TO_METER
        }
    }
    
    # Create HarmonizedDataset
    dataset = HarmonizedDataset(
        separation_m=target_grid[valid_count],
        force_n=final_force[valid_count],
        covariance_matrix=covariance_matrix,
        metadata=metadata
    )
    
    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON (force and separation) and NPY (covariance)
    output_json = output_path.with_suffix('.json')
    output_cov = output_path.with_suffix('.npy')
    
    data_dict = {
        'separation_m': dataset.separation_m.tolist(),
        'force_n': dataset.force_n.tolist(),
        'metadata': dataset.metadata
    }
    
    with open(output_json, 'w') as f:
        json.dump(data_dict, f, indent=2)
        
    np.save(output_cov, dataset.covariance_matrix)
    
    logger.info(f"Harmonized dataset saved to {output_json} and {output_cov}")
    
    return dataset

def construct_covariance_matrix(separation_m: np.ndarray, 
                                force_n: np.ndarray,
                                statistical_uncertainty: Optional[np.ndarray] = None,
                                systematic_uncertainty: float = 0.0) -> np.ndarray:
    """
    Construct a full covariance matrix from force data and uncertainties.
    
    Args:
        separation_m: Separation distances in meters.
        force_n: Force values in Newtons.
        statistical_uncertainty: Array of statistical uncertainties (if available).
        systematic_uncertainty: Global systematic uncertainty factor (fractional).
        
    Returns:
        Covariance matrix (N x N).
    """
    n_points = len(separation_m)
    
    # Initialize diagonal with statistical uncertainties
    if statistical_uncertainty is not None:
        diag = statistical_uncertainty**2
    else:
        # Placeholder: estimate from data if no uncertainties provided
        # Using 1% of force as a placeholder
        diag = (np.abs(force_n) * 0.01)**2
        
    # Add systematic uncertainty (correlated across all points)
    if systematic_uncertainty > 0:
        sys_var = (np.abs(force_n) * systematic_uncertainty)**2
        diag += sys_var
        
    # Start with diagonal matrix
    cov_matrix = np.diag(diag)
    
    # In a full implementation, we would add off-diagonal terms for systematic errors
    # For now, we return a diagonal matrix
    # TODO: Implement banded covariance for correlated systematic errors
    
    # Verify positive definiteness
    try:
        np.linalg.cholesky(cov_matrix)
    except np.linalg.LinAlgError:
        logger.warning("Covariance matrix is not positive definite. Adding small regularization.")
        cov_matrix += np.eye(n_points) * 1e-20
        
    return cov_matrix

def main():
    """
    Main entry point for harmonization script.
    
    Reads configuration from command line or default paths,
    processes raw data, and outputs harmonized dataset.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Harmonize inverse-square law experiment data')
    parser.add_argument('--input-dir', type=Path, default=Path('data/raw'),
                      help='Directory containing raw CSV files')
    parser.add_argument('--output-dir', type=Path, default=Path('data/processed'),
                      help='Directory for output files')
    parser.add_argument('--force-col', type=str, default='force_dyne',
                      help='Column name for force in raw data')
    parser.add_argument('--separation-col', type=str, default='separation_um',
                      help='Column name for separation in raw data')
    parser.add_argument('--grid-method', type=str, default='linear',
                      help='Interpolation method for grid alignment')
    parser.add_argument('--output-name', type=str, default='harmonized_experiment',
                      help='Base name for output files')
                      
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Find raw CSV files
    raw_files = list(args.input_dir.glob('*.csv'))
    if not raw_files:
        logger.error(f"No CSV files found in {args.input_dir}")
        return 1
        
    logger.info(f"Found {len(raw_files)} raw files")
    
    # Harmonize
    output_path = args.output_dir / f"{args.output_name}.csv"
    
    try:
        dataset = harmonize_experiment(
            raw_data_paths=raw_files,
            output_path=output_path,
            force_col=args.force_col,
            separation_col=args.separation_col,
            grid_method=args.grid_method
        )
        logger.info("Harmonization completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Harmonization failed: {e}")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())