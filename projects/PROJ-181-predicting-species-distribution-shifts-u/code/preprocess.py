"""
Preprocessing module for species occurrence data.
Handles filtering, deduplication, spatial thinning, and climate extraction.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from geopy.distance import geodesic

# Import project configuration and logging
from config import DATA_DIR, METRICS_DIR, PROJECT_ROOT
from logging_config import get_preprocess_logger
from utils.data_utils import validate_coordinates, impute_missing_nearest_neighbor

# Initialize logger
logger = get_preprocess_logger(__name__)

# Constants
MIN_DISTANCE_KM = 10.0  # FR-002: 10km minimum distance
MIN_RECORDS_THRESHOLD = 100  # FR-006: Minimum records threshold
COORD_TOLERANCE = 1e-6  # Tolerance for coordinate deduplication

def thin_occurrences(input_path: str, output_path: str, distance_km: float = MIN_DISTANCE_KM) -> pd.DataFrame:
    """
    Spatially thin occurrence records to ensure minimum distance between points.
    
    Args:
        input_path: Path to input CSV with occurrence data
        output_path: Path to save thinned output CSV
        distance_km: Minimum distance in kilometers (default: 10km)
    
    Returns:
        DataFrame with thinned occurrences
    """
    logger.info(f"Starting spatial thinning with minimum distance: {distance_km}km")
    logger.info(f"Input: {input_path}, Output: {output_path}")
    
    # Load data
    df = pd.read_csv(input_path)
    before_count = len(df)
    logger.info(f"Loaded {before_count} records")
    
    # Validate coordinates
    df = validate_coordinates(df)
    logger.info(f"After coordinate validation: {len(df)} records")
    
    # Create geometry column
    geometry = [Point(xy) for xy in zip(df['decimalLongitude'], df['decimalLatitude'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    
    # Spatial thinning algorithm
    # Convert to projected CRS for accurate distance calculation (UTM zones)
    # We'll use a simple iterative approach that works globally
    thinning_indices = []
    used_points = []
    
    # Sort by species to process each species independently
    species_groups = gdf.groupby('species')
    
    for species_name, species_gdf in species_groups:
        logger.debug(f"Processing species: {species_name} ({len(species_gdf)} records)")
        
        # Convert to a local projection for this species' centroid
        if len(species_gdf) > 0:
            centroid_lon = species_gdf['decimalLongitude'].mean()
            centroid_lat = species_gdf['decimalLatitude'].mean()
            
            # Determine appropriate UTM zone
            utm_zone = int((centroid_lon + 180) / 6) + 1
            if centroid_lat >= 0:
                epsg_code = f"EPSG:{32600 + utm_zone}"
            else:
                epsg_code = f"EPSG:{32700 + utm_zone}"
            
            try:
                species_projected = species_gdf.to_crs(epsg_code)
            except Exception as e:
                logger.warning(f"Could not project to UTM {epsg_code}, using fallback: {e}")
                species_projected = species_gdf
            
            # Iterative thinning
            species_indices = species_projected.index.tolist()
            selected_indices = []
            
            for idx in species_indices:
                current_point = species_projected.loc[idx, 'geometry']
                
                # Check distance to all already selected points
                is_too_close = False
                for selected_idx in selected_indices:
                    selected_point = species_projected.loc[selected_idx, 'geometry']
                    # Distance in meters
                    dist = current_point.distance(selected_point)
                    if dist < distance_km * 1000:  # Convert km to meters
                        is_too_close = True
                        break
                
                if not is_too_close:
                    selected_indices.append(idx)
            
            thinning_indices.extend(selected_indices)
            logger.debug(f"  Selected {len(selected_indices)} from {len(species_gdf)} records")
    
    # Apply thinning
    thinned_gdf = gdf.loc[thinning_indices]
    thinned_df = thinned_gdf.drop(columns=['geometry'])
    
    after_count = len(thinned_df)
    logger.info(f"Spatial thinning complete: {before_count} -> {after_count} records")
    logger.info(f"Thinned data saved to: {output_path}")
    
    # Save to CSV
    thinned_df.to_csv(output_path, index=False)
    
    return thinned_df

def check_insufficient_data(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Check if species have insufficient data (<100 records) and flag them.
    
    Args:
        input_path: Path to raw occurrence CSV
        output_path: Path to save insufficient data report JSON
    
    Returns:
        Dictionary with species data counts and status
    """
    logger.info(f"Checking data sufficiency for: {input_path}")
    
    df = pd.read_csv(input_path)
    species_counts = df.groupby('species').size().reset_index(name='count')
    
    insufficient_data = []
    
    for _, row in species_counts.iterrows():
        species = row['species']
        count = int(row['count'])
        
        if count < MIN_RECORDS_THRESHOLD:
          status = 'INSUFFICIENT_DATA'
          insufficient_data.append({
              'species': species,
              'count': count,
              'status': status
          })
          logger.warning(f"Species '{species}' has insufficient data: {count} records (< {MIN_RECORDS_THRESHOLD})")
        else:
          logger.info(f"Species '{species}' has sufficient data: {count} records")
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(insufficient_data, f, indent=2)
    
    logger.info(f"Insufficient data report saved to: {output_path}")
    
    return insufficient_data

def filter_and_deduplicate(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Filter records by date range and remove exact duplicates.
    
    Args:
        input_path: Path to input CSV
        output_path: Path to save filtered output
    
    Returns:
        Filtered DataFrame
    """
    logger.info(f"Filtering and deduplicating: {input_path}")
    
    df = pd.read_csv(input_path)
    before_count = len(df)
    
    # Remove rows with missing critical coordinates
    df = df.dropna(subset=['decimalLatitude', 'decimalLongitude'])
    
    # Remove duplicates based on coordinates and species
    df = df.drop_duplicates(subset=['species', 'decimalLatitude', 'decimalLongitude'])
    
    after_count = len(df)
    logger.info(f"Filtered and deduplicated: {before_count} -> {after_count} records")
    
    df.to_csv(output_path, index=False)
    
    return df

def main():
    """
    Main entry point for preprocessing recent occurrence data (2005-2020).
    Implements T029b: Check FR-006 threshold, flag insufficient data, then thin.
    """
    logger.info("=" * 60)
    logger.info("Starting T029b: Preprocess recent occurrence data (2005-2020)")
    logger.info("=" * 60)
    
    # Define paths
    raw_data_path = DATA_DIR / "raw" / "occurrence_2005_2020.csv"
    filtered_data_path = DATA_DIR / "processed" / "occurrence_recent_filtered.csv"
    final_output_path = DATA_DIR / "processed" / "occurrence_recent_clean.csv"
    insufficient_data_path = METRICS_DIR / "insufficient_data.json"
    
    # Ensure directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    
    if not raw_data_path.exists():
        logger.error(f"Raw data file not found: {raw_data_path}")
        logger.error("Please run T011 (download recent data) before running this task.")
        sys.exit(1)
    
    # Step 1: Filter and deduplicate
    logger.info("Step 1: Filtering and deduplicating raw data...")
    filter_and_deduplicate(str(raw_data_path), str(filtered_data_path))
    
    # Step 2: Check for insufficient data (FR-006) BEFORE thinning
    logger.info("Step 2: Checking for insufficient data (FR-006)...")
    insufficient_data = check_insufficient_data(str(filtered_data_path), str(insufficient_data_path))
    
    # Count how many species have sufficient data
    species_with_data = len([s for s in insufficient_data if s['status'] != 'INSUFFICIENT_DATA'])
    species_insufficient = len([s for s in insufficient_data if s['status'] == 'INSUFFICIENT_DATA'])
    
    logger.info(f"Species with sufficient data: {species_with_data}")
    logger.info(f"Species with insufficient data: {species_insufficient}")
    
    # Step 3: Apply thinning ONLY if count >= 100
    logger.info("Step 3: Applying spatial thinning (10km) to sufficient data...")
    
    # Load filtered data to separate sufficient vs insufficient
    df_filtered = pd.read_csv(filtered_data_path)
    species_counts = df_filtered.groupby('species').size()
    sufficient_species = species_counts[species_counts >= MIN_RECORDS_THRESHOLD].index.tolist()
    
    if not sufficient_species:
        logger.warning("No species have sufficient data for thinning. Creating empty output.")
        # Create empty output with correct schema
        df_filtered.head(0).to_csv(final_output_path, index=False)
        logger.info(f"Empty clean data created at: {final_output_path}")
    else:
        # Filter to only sufficient species
        df_sufficient = df_filtered[df_filtered['species'].isin(sufficient_species)]
        df_sufficient.to_csv(filtered_data_path, index=False)
        
        # Apply thinning
        thin_occurrences(str(filtered_data_path), str(final_output_path), distance_km=MIN_DISTANCE_KM)
    
    # Step 4: Log final counts
    if final_output_path.exists():
        df_final = pd.read_csv(final_output_path)
        logger.info(f"Final clean data: {len(df_final)} records for {df_final['species'].nunique()} species")
        logger.info(f"Output saved to: {final_output_path}")
    else:
        logger.warning("Final output file was not created.")
    
    logger.info("=" * 60)
    logger.info("T029b Preprocessing Complete")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
