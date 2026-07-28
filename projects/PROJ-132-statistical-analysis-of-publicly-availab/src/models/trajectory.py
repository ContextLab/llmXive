"""
Trajectory analysis module for computing weekly migration centroids per species-year.

This module implements the core logic for User Story 3, specifically:
- Computing weekly migration centroids (latitude/longitude) for each species and year combination.
- Aggregating these centroids into migration trajectories.

Dependencies:
- Uses preprocessed data from src/data/preprocess.py (aggregated to weekly grid cells).
- Relies on config constants from src/lib/config.py.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

# Import project constants
from src.lib.config import SEED, GRID_RES

# Setup logger
logger = logging.getLogger(__name__)

def compute_weekly_centroids(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute weekly migration centroids per species-year.
    
    Given a DataFrame with aggregated weekly counts per grid cell, this function
    calculates the weighted centroid (latitude and longitude) for each species,
    year, and week combination. The weighting is based on the observation count.
    
    Args:
        df: DataFrame with columns: species, year, week, grid_cell, count, lat, lon
            (Output from src/data/preprocess.py aggregate_to_weekly_grid)
    
    Returns:
        DataFrame with columns: species, year, week, centroid_lat, centroid_lon, total_count
    """
    logger.info("Computing weekly migration centroids...")
    
    # Ensure required columns exist
    required_cols = ['species', 'year', 'week', 'count', 'lat', 'lon']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for centroid computation: {missing_cols}")
    
    # Filter out rows with zero or negative counts to avoid weighting issues
    valid_df = df[df['count'] > 0].copy()
    
    if valid_df.empty:
        logger.warning("No valid records with count > 0 found for centroid computation.")
        return pd.DataFrame(columns=['species', 'year', 'week', 'centroid_lat', 'centroid_lon', 'total_count'])
    
    # Calculate weighted centroid
    # Centroid Lat = sum(count * lat) / sum(count)
    # Centroid Lon = sum(count * lon) / sum(count)
    
    grouped = valid_df.groupby(['species', 'year', 'week'], as_index=False).agg(
        weighted_lat=('lat', lambda x: (x * valid_df.loc[x.index, 'count']).sum()),
        weighted_lon=('lon', lambda x: (x * valid_df.loc[x.index, 'count']).sum()),
        total_count=('count', 'sum')
    )
    
    # Handle potential division by zero if a group somehow has total_count=0 (though filtered above)
    # Re-calculate safely
    grouped['centroid_lat'] = grouped['weighted_lat'] / grouped['total_count'].replace(0, np.nan)
    grouped['centroid_lon'] = grouped['weighted_lon'] / grouped['total_count'].replace(0, np.nan)
    
    # Drop intermediate columns
    result = grouped.drop(columns=['weighted_lat', 'weighted_lon'])
    
    # Sort for consistency
    result = result.sort_values(['species', 'year', 'week']).reset_index(drop=True)
    
    logger.info(f"Computed centroids for {len(result)} species-year-week combinations.")
    
    return result

def filter_centroids_by_data_quality(centroids_df: pd.DataFrame, quality_threshold: int = 5) -> pd.DataFrame:
    """
    Filter centroids based on data quality (total observation count).
    
    This implements the logic to exclude grid cells/periods with insufficient data,
    consistent with T018 requirements.
    
    Args:
        centroids_df: DataFrame from compute_weekly_centroids
        quality_threshold: Minimum total_count required (default 5, matching T018)
    
    Returns:
        Filtered DataFrame
    """
    logger.info(f"Filtering centroids with total_count < {quality_threshold}...")
    
    filtered = centroids_df[centroids_df['total_count'] >= quality_threshold].copy()
    dropped = len(centroids_df) - len(filtered)
    
    if dropped > 0:
        logger.info(f"Filtered out {dropped} centroids due to insufficient data.")
    
    return filtered

def save_trajectory_results(centroids_df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the computed trajectory data to a JSON file.
    
    Args:
        centroids_df: DataFrame with centroid data
        output_path: Path to the output JSON file
    """
    logger.info(f"Saving trajectory results to {output_path}...")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dictionary for JSON serialization
    # Handle potential NaN values by converting to None
    data = centroids_df.where(pd.notnull(centroids_df), None).to_dict(orient='records')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Successfully saved {len(data)} trajectory records.")

def run_trajectory_pipeline(
    input_path: Path,
    output_path: Path,
    quality_threshold: int = 5
) -> pd.DataFrame:
    """
    Run the full trajectory computation pipeline.
    
    1. Load preprocessed weekly data.
    2. Compute weekly centroids.
    3. Filter by data quality.
    4. Save results.
    
    Args:
        input_path: Path to the preprocessed weekly data (parquet or csv)
        output_path: Path to save the trajectory results (json)
        quality_threshold: Minimum count threshold for data quality
    
    Returns:
        The computed and filtered DataFrame
    """
    logger.info(f"Starting trajectory pipeline. Input: {input_path}, Output: {output_path}")
    
    # Determine file type and load
    if input_path.suffix == '.parquet':
        df = pd.read_parquet(input_path)
    elif input_path.suffix == '.csv':
        df = pd.read_csv(input_path)
    else:
        raise ValueError(f"Unsupported input file format: {input_path.suffix}")
    
    logger.info(f"Loaded {len(df)} records from {input_path}")
    
    # Step 1: Compute centroids
    centroids = compute_weekly_centroids(df)
    
    # Step 2: Filter by data quality
    filtered_centroids = filter_centroids_by_data_quality(centroids, quality_threshold)
    
    # Step 3: Save results
    save_trajectory_results(filtered_centroids, output_path)
    
    return filtered_centroids

def main() -> None:
    """
    Main entry point for the trajectory analysis script.
    
    Expects input data at data/processed/weekly_grid_data.parquet
    (or a similar path defined in a config, but we use defaults for now)
    and outputs to data/processed/trajectory_centroids.json.
    """
    # Setup logging
    from src.lib.config import setup_logging
    setup_logging()
    
    # Define paths relative to project root
    # Assuming standard project structure
    project_root = Path(__file__).parent.parent.parent
    input_path = project_root / "data" / "processed" / "weekly_grid_data.parquet"
    output_path = project_root / "data" / "processed" / "trajectory_centroids.json"
    
    # Fallback if parquet doesn't exist, try csv (from T015 output)
    if not input_path.exists():
        input_path_csv = project_root / "data" / "processed" / "weekly_grid_data.csv"
        if input_path_csv.exists():
            input_path = input_path_csv
        else:
            logger.error(f"Input file not found: {input_path} or {input_path_csv}")
            sys.exit(1)
    
    try:
        run_trajectory_pipeline(input_path, output_path)
        logger.info("Trajectory pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Trajectory pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
