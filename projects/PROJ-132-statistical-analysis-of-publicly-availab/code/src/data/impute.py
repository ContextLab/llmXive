"""
Spatial interpolation module for climate data imputation.

This module implements spatial interpolation for missing climate data points
using scipy's griddata with a 1° radius neighbor search in degrees (lat/lon).
It integrates with the preprocessing pipeline to fill missing values and
flag imputed cells in metadata.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from scipy.spatial import cKDTree

# Configure logger
logger = logging.getLogger(__name__)


def load_climate_data(input_path: str) -> pd.DataFrame:
    """
    Load climate data from parquet file.

    Args:
        input_path: Path to the input climate parquet file.

    Returns:
        DataFrame with columns: lat, lon, temp, week, precip.

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

    logger.info(f"Loaded climate data with {len(df)} rows from {input_path}")
    return df


def identify_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify rows with missing climate values.

    Args:
        df: Input DataFrame.

    Returns:
        Boolean mask indicating rows with missing temp or precip.
    """
    missing_mask = df['temp'].isna() | df['precip'].isna()
    missing_count = missing_mask.sum()
    if missing_count > 0:
        logger.warning(f"Found {missing_count} rows with missing climate values")
    return missing_mask


def interpolate_spatial(
    df: pd.DataFrame,
    temp_col: str = 'temp',
    precip_col: str = 'precip',
    radius_deg: float = 1.0,
    method: str = 'linear'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Perform spatial interpolation for missing climate values.

    Uses scipy.interpolate.griddata with a 1° radius neighbor search.
    Only uses known points within the specified radius for interpolation.

    Args:
        df: DataFrame with lat, lon, temp, precip columns.
        temp_col: Name of the temperature column.
        precip_col: Name of the precipitation column.
        radius_deg: Search radius in degrees (default 1.0°).
        method: Interpolation method ('linear', 'nearest', 'cubic').

    Returns:
        Tuple of (imputed DataFrame, metadata dict with imputation stats).
    """
    df = df.copy()
    df[f'{temp_col}_imputed'] = False
    df[f'{precip_col}_imputed'] = False

    # Get known points (non-missing)
    known_mask = df[temp_col].notna() & df[precip_col].notna()
    known_points = df.loc[known_mask, ['lat', 'lon']].values
    known_temp = df.loc[known_mask, temp_col].values
    known_precip = df.loc[known_mask, precip_col].values

    # Get missing points
    missing_mask = df[temp_col].isna() | df[precip_col].isna()
    if missing_mask.sum() == 0:
        logger.info("No missing values to impute")
        return df, {'imputed_count': 0, 'imputed_temp': 0, 'imputed_precip': 0}

    missing_points = df.loc[missing_mask, ['lat', 'lon']].values

    # Build KDTree for efficient neighbor search
    tree = cKDTree(known_points)

    # Find neighbors within radius for each missing point
    distances, indices = tree.query(missing_points, distance_upper_bound=radius_deg)

    # Track which points had neighbors
    has_neighbors = ~np.isinf(distances[:, 0])  # distances[:, 0] is min distance

    imputed_temp_count = 0
    imputed_precip_count = 0

    # Interpolate temperature
    if known_temp.size > 0:
        # Use griddata with only points that have neighbors
        valid_indices = has_neighbors[:, 0]  # First column is min distance
        if valid_indices.sum() > 0:
            # For each missing point, interpolate using nearby known points
            for i, idx in enumerate(np.where(missing_mask)[0]):
                if has_neighbors[i, 0]:
                    # Get neighbors for this point
                    neighbor_dists, neighbor_idxs = tree.query(
                        missing_points[i], k=min(10, known_points.shape[0]), distance_upper_bound=radius_deg
                    )
                    if neighbor_idxs.size > 0:
                        # Filter out inf distances
                        valid_mask = ~np.isinf(neighbor_dists)
                        if valid_mask.sum() > 0:
                            neighbor_pts = known_points[neighbor_idxs[valid_mask]]
                            neighbor_vals_temp = known_temp[neighbor_idxs[valid_mask]]
                            neighbor_vals_precip = known_precip[neighbor_idxs[valid_mask]]

                            # Interpolate
                            try:
                                temp_interp = griddata(
                                    neighbor_pts, neighbor_vals_temp,
                                    (missing_points[i, 0], missing_points[i, 1]),
                                    method=method
                                )
                                precip_interp = griddata(
                                    neighbor_pts, neighbor_vals_precip,
                                    (missing_points[i, 0], missing_points[i, 1]),
                                    method=method
                                )

                                if not np.isnan(temp_interp):
                                    df.loc[idx, temp_col] = temp_interp
                                    df.loc[idx, f'{temp_col}_imputed'] = True
                                    imputed_temp_count += 1

                                if not np.isnan(precip_interp):
                                    df.loc[idx, precip_col] = precip_interp
                                    df.loc[idx, f'{precip_col}_imputed'] = True
                                    imputed_precip_count += 1
                            except Exception as e:
                                logger.warning(f"Interpolation failed for point {i}: {e}")

    metadata = {
        'imputed_count': int(has_neighbors.sum()),
        'imputed_temp': imputed_temp_count,
        'imputed_precip': imputed_precip_count,
        'radius_deg': radius_deg,
        'method': method,
        'total_missing': int(missing_mask.sum())
    }

    logger.info(f"Imputation complete: {imputed_temp_count} temp, {imputed_precip_count} precip values filled")
    return df, metadata


def save_imputed_data(
    df: pd.DataFrame,
    metadata: Dict[str, Any],
    output_path: str,
    metadata_path: Optional[str] = None
) -> None:
    """
    Save imputed data and metadata to disk.

    Args:
        df: Imputed DataFrame.
        metadata: Imputation metadata dictionary.
        output_path: Path for the output parquet file.
        metadata_path: Optional path for the metadata JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    df.to_parquet(path, index=False)
    logger.info(f"Saved imputed data to {output_path}")

    if metadata_path:
        meta_path = Path(metadata_path)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved imputation metadata to {metadata_path}")


def run_imputation_pipeline(
    input_path: str,
    output_path: str,
    metadata_path: Optional[str] = None,
    radius_deg: float = 1.0,
    method: str = 'linear'
) -> Dict[str, Any]:
    """
    Run the full imputation pipeline.

    Args:
        input_path: Path to input climate parquet file.
        output_path: Path for output imputed parquet file.
        metadata_path: Optional path for metadata JSON file.
        radius_deg: Search radius in degrees.
        method: Interpolation method.

    Returns:
        Imputation metadata dictionary.
    """
    logger.info(f"Starting imputation pipeline for {input_path}")

    # Load data
    df = load_climate_data(input_path)

    # Check for missing values
    missing_mask = identify_missing_values(df)

    if missing_mask.sum() == 0:
        # No missing values, just save a copy
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=False)
        metadata = {'imputed_count': 0, 'imputed_temp': 0, 'imputed_precip': 0, 'message': 'No missing values'}
        if metadata_path:
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        return metadata

    # Perform interpolation
    df_imputed, metadata = interpolate_spatial(
        df, radius_deg=radius_deg, method=method
    )

    # Save results
    save_imputed_data(df_imputed, metadata, output_path, metadata_path)

    return metadata


def main():
    """Main entry point for running imputation from command line."""
    import argparse

    parser = argparse.ArgumentParser(description='Impute missing climate data via spatial interpolation')
    parser.add_argument('--input', '-i', default='data/raw/climate.parquet',
                        help='Input climate parquet file')
    parser.add_argument('--output', '-o', default='data/interim/climate_imputed.parquet',
                        help='Output imputed parquet file')
    parser.add_argument('--metadata', '-m', default='data/interim/imputation_metadata.json',
                        help='Output metadata JSON file')
    parser.add_argument('--radius', '-r', type=float, default=1.0,
                        help='Search radius in degrees (default: 1.0)')
    parser.add_argument('--method', default='linear',
                        choices=['linear', 'nearest', 'cubic'],
                        help='Interpolation method (default: linear)')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    metadata = run_imputation_pipeline(
        input_path=args.input,
        output_path=args.output,
        metadata_path=args.metadata,
        radius_deg=args.radius,
        method=args.method
    )

    print(f"Imputation complete. Metadata: {metadata}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
