"""
Spatial interpolation module for missing climate data.
Implements grid-based interpolation using scipy.interpolate.griddata.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from scipy.spatial import cKDTree

# Import logging setup from existing config
from src.config import setup_logging

logger = logging.getLogger(__name__)

# Constants
DEFAULT_GRID_RES = 0.5  # Degrees, from T010a config


def load_climate_data(input_path: str) -> pd.DataFrame:
    """
    Load climate data from a parquet file.
    
    Args:
        input_path: Path to the input parquet file.
        
    Returns:
        DataFrame with columns: lat, lon, temp, week, precip
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Climate data file not found: {input_path}")
    
    df = pd.read_parquet(path)
    required_cols = {'lat', 'lon', 'temp', 'week', 'precip'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")
    
    logger.info(f"Loaded climate data: {len(df)} rows, columns: {list(df.columns)}")
    return df


def identify_missing_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[int]]:
    """
    Identify rows with missing climate values (temp or precip).
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Tuple of (DataFrame with missing values flagged, list of indices to impute).
    """
    # Create a copy to avoid modifying original
    df_imputed = df.copy()
    
    # Check for missing values in temp or precip
    missing_mask = df_imputed['temp'].isna() | df_imputed['precip'].isna()
    missing_indices = df_imputed[missing_mask].index.tolist()
    
    logger.info(f"Identified {len(missing_indices)} rows with missing values out of {len(df)} total")
    
    return df_imputed, missing_indices


def interpolate_spatial(
    df: pd.DataFrame, 
    target_cols: List[str], 
    grid_res: float = DEFAULT_GRID_RES
) -> pd.DataFrame:
    """
    Perform spatial interpolation for missing values using griddata.
    
    The interpolation uses a neighbor search in degrees (lat/lon) at the
    specified spatial scale. For each missing point, we find nearby known
    points and interpolate.
    
    Args:
        df: DataFrame with lat, lon, and target columns.
        target_cols: List of column names to interpolate (e.g., ['temp', 'precip']).
        grid_res: Spatial resolution in degrees for the grid.
        
    Returns:
        DataFrame with interpolated values filled in.
    """
    df_result = df.copy()
    missing_mask = df_result['temp'].isna() | df_result['precip'].isna()
    
    if not missing_mask.any():
        logger.info("No missing values to interpolate.")
        return df_result
    
    # Separate known and missing points
    known_mask = ~missing_mask
    known_points = df_result.loc[known_mask, ['lat', 'lon']].values
    missing_points = df_result.loc[missing_mask, ['lat', 'lon']].values
    
    if len(known_points) == 0:
        raise ValueError("No known data points available for interpolation.")
    
    logger.info(f"Interpolating {len(missing_points)} missing points using {len(known_points)} known points")
    
    # Create a KDTree for efficient neighbor search
    tree = cKDTree(known_points)
    
    # For each missing point, find neighbors and interpolate
    for col in target_cols:
        if col not in df_result.columns:
            logger.warning(f"Column {col} not found in DataFrame, skipping.")
            continue
            
        known_values = df_result.loc[known_mask, col].values
        
        # Query the tree for the k nearest neighbors (use k=3 for stability)
        k = min(3, len(known_points))
        distances, indices = tree.query(missing_points, k=k)
        
        # Interpolate using linear method with the neighbor coordinates
        # We use the actual coordinates of the neighbors, not a grid
        neighbor_coords = known_points[indices]
        neighbor_vals = known_values[indices]
        
        # Use griddata for interpolation at the missing points
        # Note: griddata expects (points, values, xi, method)
        # We'll use 'linear' method which requires at least k=3 points in 2D
        try:
            interpolated_vals = griddata(
                known_points, 
                known_values, 
                missing_points, 
                method='linear'
            )
            
            # Handle any NaNs from griddata (e.g., points outside convex hull)
            nan_mask = np.isnan(interpolated_vals)
            if nan_mask.any():
                logger.warning(f"griddata returned NaN for {nan_mask.sum()} points in column {col}. "
                             "Falling back to nearest neighbor for these points.")
                # Fallback: use the nearest neighbor value
                nearest_indices = indices[:, 0]  # First nearest neighbor
                nearest_vals = known_values[nearest_indices]
                interpolated_vals[nan_mask] = nearest_vals[nan_mask]
            
            # Assign interpolated values to the result DataFrame
            df_result.loc[missing_mask, col] = interpolated_vals
            
        except Exception as e:
            logger.error(f"Interpolation failed for column {col}: {e}")
            raise
    
    logger.info("Spatial interpolation completed.")
    return df_result


def save_imputed_data(
    df: pd.DataFrame, 
    output_path: str, 
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save imputed data to a parquet file and write metadata.
    
    Args:
        df: DataFrame with imputed values.
        output_path: Path for the output parquet file.
        metadata: Optional metadata dictionary to include.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure the is_imputed flag is set
    if 'is_imputed' not in df.columns:
        # We need to track which rows were imputed
        # This requires passing the original missing mask
        logger.warning("is_imputed column not found. Assuming all rows were checked.")
        # In a real implementation, we'd track this during interpolation
        df['is_imputed'] = False
    
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved imputed data to {output_path}")
    
    if metadata:
        metadata_path = Path(output_path).parent / 'imputation_metadata.json'
        with open(metadata_path, 'w') as f:
            import json
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved imputation metadata to {metadata_path}")


def run_imputation_pipeline(
    input_path: str, 
    output_path: str, 
    grid_res: float = DEFAULT_GRID_RES
) -> Dict[str, Any]:
    """
    Run the full imputation pipeline.
    
    Args:
        input_path: Path to input climate parquet file.
        output_path: Path for output imputed parquet file.
        grid_res: Spatial resolution for interpolation.
        
    Returns:
        Dictionary with pipeline statistics.
    """
    logger.info(f"Starting imputation pipeline: {input_path} -> {output_path}")
    
    # Step 1: Load data
    df = load_climate_data(input_path)
    
    # Step 2: Identify missing values
    df_flagged, missing_indices = identify_missing_values(df)
    
    # Step 3: Interpolate
    if len(missing_indices) > 0:
        df_imputed = interpolate_spatial(df_flagged, ['temp', 'precip'], grid_res=grid_res)
    else:
        df_imputed = df_flagged
        logger.info("No interpolation needed.")
    
    # Step 4: Create metadata
    metadata = {
        'input_file': input_path,
        'output_file': output_path,
        'total_rows': len(df),
        'missing_rows': len(missing_indices),
        'imputed_rows': len(missing_indices),
        'grid_resolution': grid_res,
        'method': 'scipy.interpolate.griddata (linear)',
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    # Mark which rows were imputed
    df_imputed['is_imputed'] = df_imputed.index.isin(missing_indices)
    
    # Step 5: Save results
    save_imputed_data(df_imputed, output_path, metadata)
    
    logger.info("Imputation pipeline completed successfully.")
    return metadata


def main() -> None:
    """Main entry point for the imputation script."""
    # Setup logging
    log_config = setup_logging()
    
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    input_path = base_dir / 'data' / 'raw' / 'climate.parquet'
    output_path = base_dir / 'data' / 'interim' / 'climate_imputed.parquet'
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        metadata = run_imputation_pipeline(str(input_path), str(output_path))
        print(f"Imputation complete. Metadata: {metadata}")
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
