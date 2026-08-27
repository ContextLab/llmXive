import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path
import logging
import json
import scipy.interpolate as interp
from scipy.linalg import cholesky, LinAlgError

from config import get_logger
from data.models import HarmonizedDataset

# Initialize logger
logger = get_logger(__name__)

# Constants
DYNE_TO_NEWTON = 1e-5
MICROMETER_TO_METER = 1e-6

def dynes_to_newtons(force_dynes: np.ndarray) -> np.ndarray:
    """Convert force from dynes to Newtons."""
    return force_dynes * DYNE_TO_NEWTON

def micrometers_to_meters(separation_um: np.ndarray) -> np.ndarray:
    """Convert separation from micrometers to meters."""
    return separation_um * MICROMETER_TO_METER

def convert_to_si(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert all force and separation columns in the dataframe to SI units.
    Assumes columns are named 'force', 'separation', 'force_uncertainty', 'separation_uncertainty'
    or similar patterns. Adjusts based on column content if units are not explicit in names.
    
    For this implementation, we assume:
    - 'force' or 'force_dyne' -> convert to Newtons
    - 'separation' or 'distance_um' -> convert to meters
    """
    df_si = df.copy()
    
    # Identify force columns
    force_cols = [col for col in df.columns if 'force' in col.lower()]
    # Identify separation columns
    sep_cols = [col for col in df.columns if 'sep' in col.lower() or 'dist' in col.lower() or 'gap' in col.lower()]
    
    if not force_cols:
        raise ValueError("No force column found in dataframe")
    if not sep_cols:
        raise ValueError("No separation/distance column found in dataframe")
        
    # Assume the first matching column is the primary one
    force_col = force_cols[0]
    sep_col = sep_cols[0]
    
    # Convert force to Newtons
    if force_col in df_si.columns:
        # Check if values look like they are in dynes (typically small numbers if already N, or larger if dynes)
        # Heuristic: if max value > 1e-9, likely dynes (since 1 dyne = 1e-5 N, and forces are typically nN range)
        # But safer to assume input is in dynes as per spec
        df_si[force_col] = dynes_to_newtons(df_si[force_col].values)
        
        # Convert uncertainty if present
        force_uncol = f"{force_col}_uncertainty"
        if force_uncol in df_si.columns:
            df_si[force_uncol] = dynes_to_newtons(df_si[force_uncol].values)
    
    # Convert separation to meters
    if sep_col in df_si.columns:
        df_si[sep_col] = micrometers_to_meters(df_si[sep_col].values)
        
        # Convert uncertainty if present
        sep_uncol = f"{sep_col}_uncertainty"
        if sep_uncol in df_si.columns:
            df_si[sep_uncol] = micrometers_to_meters(df_si[sep_uncol].values)
            
    return df_si

def align_to_grid(
    datasets: List[Dict[str, Any]], 
    grid_min: Optional[float] = None, 
    grid_max: Optional[float] = None, 
    grid_step: Optional[float] = None
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Align multiple datasets to a common separation grid.
    
    Args:
        datasets: List of dicts containing 'separation' and 'force' (and uncertainties)
        grid_min: Minimum separation for the grid (defaults to min of all data)
        grid_max: Maximum separation for the grid (defaults to max of all data)
        grid_step: Step size for the grid (defaults to 0.01 * min separation range or 1e-9 m)
        
    Returns:
        aligned_df: DataFrame with columns [separation, force, force_uncertainty, source_id]
        grid: The common separation grid used
    """
    if not datasets:
        raise ValueError("No datasets provided for alignment")
        
    # Extract all separations to determine grid bounds
    all_seps = []
    for ds in datasets:
        if 'separation' in ds:
            all_seps.extend(ds['separation'])
            
    if not all_seps:
        raise ValueError("No separation data found in provided datasets")
        
    min_sep = min(all_seps)
    max_sep = max(all_seps)
    
    # Handle non-overlapping ranges
    # Check if datasets have overlapping ranges
    ranges = [(min(ds.get('separation', [np.inf])), max(ds.get('separation', [-np.inf]))) 
              for ds in datasets if 'separation' in ds]
    
    if len(ranges) > 1:
        # Check for overlaps
        has_overlap = False
        for i in range(len(ranges)):
            for j in range(i+1, len(ranges)):
                r1, r2 = ranges[i], ranges[j]
                # Check if intervals overlap
                if r1[0] < r2[1] and r2[0] < r1[1]:
                    has_overlap = True
                    break
            if has_overlap:
                break
                
        if not has_overlap:
            logger.warning("Non-overlapping separation ranges detected between datasets. "
                         "Interpolation will be performed, but results outside overlapping regions "
                         "should be interpreted with caution.")
    
    # Determine grid parameters
    if grid_min is None:
        grid_min = min_sep
    if grid_max is None:
        grid_max = max_sep
    if grid_step is None:
        # Use a reasonable default: 1% of the range or 1e-9 m, whichever is larger
        range_size = max_sep - min_sep
        grid_step = max(range_size * 0.01, 1e-9)
        
    # Create common grid
    grid = np.arange(grid_min, grid_max + grid_step, grid_step)
    
    # Interpolate each dataset to the common grid
    aligned_rows = []
    for idx, ds in enumerate(datasets):
        if 'separation' not in ds or 'force' not in ds:
            continue
            
        sep = np.array(ds['separation'])
        force = np.array(ds['force'])
        force_unc = ds.get('force_uncertainty', np.zeros_like(force))
        
        # Sort by separation for interpolation
        sort_idx = np.argsort(sep)
        sep_sorted = sep[sort_idx]
        force_sorted = force[sort_idx]
        force_unc_sorted = force_unc[sort_idx]
        
        # Interpolate force and uncertainty
        # Use linear interpolation; extrapolate with nearest neighbor (bounds_error=False, fill_value="extrapolate" might be risky)
        # Instead, we'll only interpolate within the range of the data
        valid_mask = (grid >= sep_sorted.min()) & (grid <= sep_sorted.max())
        
        if not valid_mask.any():
            logger.warning(f"Dataset {idx} has no overlap with the common grid. Skipping.")
            continue
            
        # Create interpolators
        try:
            interp_force = interp.interp1d(sep_sorted, force_sorted, kind='linear', 
                                         bounds_error=False, fill_value=np.nan)
            interp_unc = interp.interp1d(sep_sorted, force_unc_sorted, kind='linear', 
                                       bounds_error=False, fill_value=np.nan)
        except ValueError:
            logger.warning(f"Dataset {idx} has insufficient points for interpolation. Skipping.")
            continue
            
        # Interpolate
        force_interp = interp_force(grid)
        unc_interp = interp_unc(grid)
        
        # Mask invalid values (outside original range)
        valid_grid = grid[valid_mask]
        force_valid = force_interp[valid_mask]
        unc_valid = unc_interp[valid_mask]
        
        for i in range(len(valid_grid)):
            aligned_rows.append({
                'separation': valid_grid[i],
                'force': force_valid[i],
                'force_uncertainty': unc_valid[i],
                'source_id': idx
            })
            
    aligned_df = pd.DataFrame(aligned_rows)
    
    if aligned_df.empty:
        raise ValueError("No valid data could be aligned to the common grid")
        
    return aligned_df, grid

def construct_covariance_matrix(
    aligned_df: pd.DataFrame, 
    grid: np.ndarray,
    systematic_correlation: Optional[float] = None
) -> np.ndarray:
    """
    Construct a full covariance matrix from the aligned dataset.
    
    Args:
        aligned_df: DataFrame with separation, force, force_uncertainty
        grid: The common separation grid
        systematic_correlation: Optional correlation coefficient for systematic errors
                                (0 to 1). If None, assumes independent errors.
                                
    Returns:
        cov_matrix: Full covariance matrix (N x N)
    """
    n = len(grid)
    cov_matrix = np.zeros((n, n))
    
    # Get uncertainties for each grid point
    # We need to aggregate uncertainties from all sources at each grid point
    # For simplicity, we'll take the mean uncertainty at each grid point if multiple sources exist
    # Or use the first source if only one
    grid_seps = aligned_df['separation'].values
    grid_forces = aligned_df['force'].values
    grid_uncs = aligned_df['force_uncertainty'].values
    
    # Aggregate uncertainties per grid point
    unique_seps = np.unique(grid_seps)
    if len(unique_seps) != n:
        # This shouldn't happen if aligned_df was created correctly, but handle it
        logger.warning("Mismatch between grid size and unique separations in aligned_df")
        
    # Create a mapping from separation to uncertainty (using mean if multiple)
    sep_to_unc = {}
    for sep in unique_seps:
        mask = grid_seps == sep
        uncs = grid_uncs[mask]
        sep_to_unc[sep] = np.mean(uncs)
        
    # Diagonal: statistical uncertainties
    for i, sep in enumerate(grid):
        unc = sep_to_unc.get(sep, 0.0)
        cov_matrix[i, i] = unc ** 2
        
    # Off-diagonal: systematic correlations
    if systematic_correlation is not None and systematic_correlation > 0:
        # Assume a simple correlation model: correlation decays with distance
        # For now, use a constant correlation for all pairs (simplified)
        # A more sophisticated model would use an exponential decay or similar
        for i in range(n):
            for j in range(i+1, n):
                # Correlation based on systematic error budget
                # Assuming systematic errors are fully correlated across all measurements
                # This is a simplification; real data might have distance-dependent correlation
                sys_unc = systematic_correlation * np.sqrt(cov_matrix[i, i] * cov_matrix[j, j])
                cov_matrix[i, j] = sys_unc
                cov_matrix[j, i] = sys_unc
                
    # Ensure positive definiteness
    try:
        cholesky(cov_matrix)
    except LinAlgError:
        logger.warning("Covariance matrix is not positive definite. Adding small regularization.")
        # Add small diagonal regularization
        min_eig = np.min(np.linalg.eigvalsh(cov_matrix))
        if min_eig < 0:
            cov_matrix += np.eye(n) * (-min_eig + 1e-10)
            
    return cov_matrix

def harmonize_experiment(
    raw_data_paths: List[Path], 
    output_dir: Path,
    grid_min: Optional[float] = None,
    grid_max: Optional[float] = None,
    grid_step: Optional[float] = None,
    systematic_correlation: Optional[float] = None
) -> HarmonizedDataset:
    """
    Main function to harmonize one or more experimental datasets.
    
    Args:
        raw_data_paths: List of paths to raw CSV files
        output_dir: Directory to save processed outputs
        grid_min, grid_max, grid_step: Parameters for the common grid
        systematic_correlation: Correlation coefficient for systematic errors
        
    Returns:
        HarmonizedDataset object containing aligned data and covariance matrix
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse and convert each dataset
    datasets = []
    for path in raw_data_paths:
        logger.info(f"Processing {path}")
        df = pd.read_csv(path)
        df_si = convert_to_si(df)
        
        datasets.append({
            'separation': df_si['separation'].values,
            'force': df_si['force'].values,
            'force_uncertainty': df_si.get('force_uncertainty', np.zeros(len(df_si))).values,
            'source_id': path.name
        })
        
    # Align to common grid
    aligned_df, grid = align_to_grid(datasets, grid_min, grid_max, grid_step)
    
    # Construct covariance matrix
    cov_matrix = construct_covariance_matrix(aligned_df, grid, systematic_correlation)
    
    # Save outputs
    aligned_path = output_dir / "harmonized_data.csv"
    aligned_df.to_csv(aligned_path, index=False)
    logger.info(f"Saved harmonized data to {aligned_path}")
    
    cov_path = output_dir / "covariance_matrix.npy"
    np.save(cov_path, cov_matrix)
    logger.info(f"Saved covariance matrix to {cov_path}")
    
    # Create HarmonizedDataset object
    dataset = HarmonizedDataset(
        separation=grid,
        force=aligned_df['force'].values,
        force_uncertainty=aligned_df['force_uncertainty'].values,
        covariance_matrix=cov_matrix,
        source_files=[str(p) for p in raw_data_paths],
        grid_min=grid.min(),
        grid_max=grid.max(),
        grid_step=grid[1] - grid[0] if len(grid) > 1 else 0
    )
    
    return dataset

def main():
    """Entry point for command-line execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Harmonize experimental force data")
    parser.add_argument("--input", nargs="+", required=True, help="Input CSV files")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--grid-min", type=float, default=None, help="Minimum grid value")
    parser.add_argument("--grid-max", type=float, default=None, help="Maximum grid value")
    parser.add_argument("--grid-step", type=float, default=None, help="Grid step size")
    parser.add_argument("--sys-corr", type=float, default=None, help="Systematic correlation coefficient")
    
    args = parser.parse_args()
    
    input_paths = [Path(p) for p in args.input]
    output_dir = Path(args.output)
    
    harmonize_experiment(
        raw_data_paths=input_paths,
        output_dir=output_dir,
        grid_min=args.grid_min,
        grid_max=args.grid_max,
        grid_step=args.grid_step,
        systematic_correlation=args.sys_corr
    )
    
    logger.info("Harmonization complete.")

if __name__ == "__main__":
    main()