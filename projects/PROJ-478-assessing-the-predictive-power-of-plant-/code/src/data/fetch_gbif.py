"""
GBIF Data Fetching and Cleaning Pipeline.

This module handles the retrieval of species occurrence data from GBIF,
deduplication, coordinate validation, and spatial thinning. It integrates
with the project's logging and provenance tracking system to ensure
data hygiene and reproducibility.
"""

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
from pygbif import occurrences

from src.utils.logging import get_logger, log_provenance, save_provenance_report
from src.utils.config import RANDOM_SEED

# Configure logger
logger = get_logger(__name__)

# Constants
GBIF_TIMEOUT = 30
MIN_RECORDS_REQUIRED = 10
SPATIAL_THINNING_MIN_KM = 1.0  # Default minimum distance in km

def fetch_gbif_occurrences(
    species_name: str,
    max_records: int = 10000,
    has_coordinates: bool = True,
    country_codes: Optional[List[str]] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None
) -> pd.DataFrame:
    """
    Fetch occurrence records for a specific species from GBIF.

    Args:
        species_name: Scientific name of the species.
        max_records: Maximum number of records to fetch.
        has_coordinates: Only fetch records with valid coordinates.
        country_codes: Optional list of country codes to filter by.
        year_min: Minimum year for occurrence.
        year_max: Maximum year for occurrence.

    Returns:
        DataFrame with occurrence records.

    Raises:
        ValueError: If no records are found or API fails.
    """
    logger.info(f"Fetching GBIF records for species: {species_name}")
    
    params = {
        'species': species_name,
        'hasCoordinate': has_coordinates,
        'limit': max_records,
        'offset': 0,
        'format': 'csv'
    }
    
    if country_codes:
        params['country'] = country_codes
    if year_min:
        params['year'] = f"{year_min}-{year_max}" if year_max else f"{year_min}-"
    
    start_time = time.time()
    
    try:
        # Fetch data using pygbif
        result = occurrences.search(**params)
        
        if result is None or 'results' not in result or len(result['results']) == 0:
            logger.warning(f"No records found for {species_name}")
            raise ValueError(f"No occurrence records found for species: {species_name}")
        
        # Parse results into DataFrame
        # Note: pygbif returns a dict with 'results' key containing list of records
        records = result['results']
        df = pd.DataFrame(records)
        
        # Standardize column names if necessary
        required_cols = ['decimalLatitude', 'decimalLongitude', 'eventDate', 'basisOfRecord']
        existing_cols = df.columns.tolist()
        
        # Filter for required columns if they exist
        available_cols = [c for c in required_cols if c in existing_cols]
        if len(available_cols) < len(required_cols):
            logger.warning(f"Some required columns missing. Available: {available_cols}")
        
        fetch_duration = time.time() - start_time
        logger.info(f"Fetched {len(df)} records for {species_name} in {fetch_duration:.2f}s")
        
        # Log provenance for the fetch step
        log_provenance(
            operation="gbif_fetch",
            parameters={
                "species": species_name,
                "max_records": max_records,
                "has_coordinates": has_coordinates,
                "fetch_duration": fetch_duration,
                "record_count": len(df)
            },
            source="GBIF API",
            timestamp=datetime.now().isoformat()
        )
        
        return df
        
    except Exception as e:
        logger.error(f"Error fetching GBIF data for {species_name}: {str(e)}")
        raise

def clean_occurrences(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean occurrence data by removing duplicates and invalid coordinates.

    Args:
        df: Raw occurrence DataFrame.

    Returns:
        Cleaned DataFrame.
    """
    logger.info("Cleaning occurrence data...")
    initial_count = len(df)
    
    # Remove rows with missing latitude or longitude
    before_coord_filter = len(df)
    df = df.dropna(subset=['decimalLatitude', 'decimalLongitude'])
    after_coord_filter = len(df)
    logger.info(f"Removed {before_coord_filter - after_coord_filter} records with missing coordinates")
    
    # Filter out coordinates outside valid ranges
    before_range_filter = len(df)
    df = df[
        (df['decimalLatitude'] >= -90) & (df['decimalLatitude'] <= 90) &
        (df['decimalLongitude'] >= -180) & (df['decimalLongitude'] <= 180)
    ]
    after_range_filter = len(df)
    logger.info(f"Removed {before_range_filter - after_range_filter} records with invalid coordinate ranges")
    
    # Remove duplicates based on coordinates and date
    if 'eventDate' in df.columns:
        before_dup_filter = len(df)
        df = df.drop_duplicates(subset=['decimalLatitude', 'decimalLongitude', 'eventDate'])
        after_dup_filter = len(df)
        logger.info(f"Removed {before_dup_filter - after_dup_filter} duplicate records (coords + date)")
    else:
        before_dup_filter = len(df)
        df = df.drop_duplicates(subset=['decimalLatitude', 'decimalLongitude'])
        after_dup_filter = len(df)
        logger.info(f"Removed {before_dup_filter - after_dup_filter} duplicate records (coords only)")
    
    clean_count = len(df)
    retention_rate = clean_count / initial_count if initial_count > 0 else 0.0
    
    logger.info(f"Cleaning complete. Retention rate: {retention_rate:.2%} ({initial_count} -> {clean_count})")
    
    # Log cleaning statistics
    log_provenance(
        operation="data_cleaning",
        parameters={
            "initial_count": initial_count,
            "final_count": clean_count,
            "retention_rate": retention_rate,
            "removed_missing_coords": before_coord_filter - after_coord_filter,
            "removed_invalid_range": before_range_filter - after_range_filter,
            "removed_duplicates": before_dup_filter - after_dup_filter
        },
        source="Internal Processing",
        timestamp=datetime.now().isoformat()
    )
    
    return df

def spatial_thinning(
    df: pd.DataFrame,
    min_distance_km: float = SPATIAL_THINNING_MIN_KM,
    species_column: str = 'species'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Apply spatial thinning to occurrence data to reduce spatial autocorrelation.

    Uses a simple grid-based thinning approach: divides the map into grid cells
    of size min_distance_km and keeps only one record per cell.

    Args:
        df: Cleaned occurrence DataFrame.
        min_distance_km: Minimum distance between points in km.
        species_column: Name of the species column (for logging).

    Returns:
        Tuple of (thinned DataFrame, thinning statistics).
    """
    logger.info(f"Applying spatial thinning with min_distance={min_distance_km} km")
    
    if df.empty:
        logger.warning("Empty DataFrame provided for spatial thinning")
        return df, {"initial": 0, "final": 0, "retention": 0.0}
    
    initial_count = len(df)
    
    # Convert lat/lon to approximate grid cells
    # Simple approach: floor(lat / cell_size) and floor(lon / cell_size)
    # For km to degrees conversion, we use an approximation:
    # 1 degree latitude ≈ 111 km
    # 1 degree longitude ≈ 111 * cos(lat) km (varies with latitude)
    
    # Calculate cell size in degrees
    lat_cell_size = min_distance_km / 111.0
    # Use average latitude for longitude conversion
    avg_lat = df['decimalLatitude'].mean()
    lon_cell_size = min_distance_km / (111.0 * abs(np.cos(np.radians(avg_lat)))) if abs(np.cos(np.radians(avg_lat))) > 0.01 else lat_cell_size
    
    # Create grid cell identifiers
    df['grid_cell'] = (
        df['decimalLatitude'].apply(lambda x: int(x / lat_cell_size)) + 
        df['decimalLongitude'].apply(lambda x: int(x / lon_cell_size) * 10000)
    )
    
    # Keep first record per grid cell
    before_thinning = len(df)
    df_thinned = df.drop_duplicates(subset=['grid_cell'])
    after_thinning = len(df_thinned)
    
    retention_rate = after_thinning / before_thinning if before_thinning > 0 else 0.0
    
    logger.info(f"Spatial thinning complete: {before_thinning} -> {after_thinning} records ({retention_rate:.2%} retention)")
    
    # Prepare statistics
    thinning_stats = {
        "initial_count": before_thinning,
        "final_count": after_thinning,
        "removed_count": before_thinning - after_thinning,
        "retention_rate": retention_rate,
        "min_distance_km": min_distance_km,
        "lat_cell_size_deg": lat_cell_size,
        "lon_cell_size_deg": lon_cell_size,
        "species": species_column
    }
    
    # Log thinning statistics for provenance
    log_provenance(
        operation="spatial_thinning",
        parameters=thinning_stats,
        source="Spatial Processing",
        timestamp=datetime.now().isoformat()
    )
    
    # Drop the temporary grid cell column
    df_thinned = df_thinned.drop(columns=['grid_cell'])
    
    return df_thinned, thinning_stats

def run_fetch_pipeline(
    species_name: str,
    output_dir: str,
    max_records: int = 10000,
    thinning_distance_km: float = SPATIAL_THINNING_MIN_KM,
    min_retention_rate: float = 0.80
) -> Dict[str, Any]:
    """
    Run the full GBIF fetch, clean, and thin pipeline for a species.

    Args:
        species_name: Scientific name of the species.
        output_dir: Directory to save processed files.
        max_records: Maximum records to fetch.
        thinning_distance_km: Distance for spatial thinning.
        min_retention_rate: Minimum acceptable retention rate after cleaning.

    Returns:
        Dictionary with pipeline results and statistics.
    """
    logger.info(f"Starting GBIF pipeline for {species_name}")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = {
        "species": species_name,
        "pipeline_start": datetime.now().isoformat(),
        "steps": {}
    }
    
    try:
        # Step 1: Fetch
        raw_df = fetch_gbif_occurrences(species_name, max_records=max_records)
        results["steps"]["fetch"] = {
            "status": "success",
            "record_count": len(raw_df)
        }
        
        # Step 2: Clean
        cleaned_df = clean_occurrences(raw_df)
        results["steps"]["clean"] = {
            "status": "success",
            "initial_count": len(raw_df),
            "final_count": len(cleaned_df),
            "retention_rate": len(cleaned_df) / len(raw_df) if len(raw_df) > 0 else 0.0
        }
        
        if len(cleaned_df) < MIN_RECORDS_REQUIRED:
            logger.error(f"Insufficient records after cleaning for {species_name}: {len(cleaned_df)} < {MIN_RECORDS_REQUIRED}")
            raise ValueError(f"Insufficient records after cleaning")
        
        # Step 3: Thin
        thinned_df, thinning_stats = spatial_thinning(cleaned_df, min_distance_km=thinning_distance_km)
        results["steps"]["thin"] = {
            "status": "success",
            "initial_count": len(cleaned_df),
            "final_count": len(thinned_df),
            "retention_rate": thinning_stats["retention_rate"],
            "details": thinning_stats
        }
        
        # Validate retention
        total_retention = len(thinned_df) / len(raw_df) if len(raw_df) > 0 else 0.0
        if total_retention < min_retention_rate:
            logger.warning(f"Total retention rate {total_retention:.2%} is below threshold {min_retention_rate}")
        
        # Save outputs
        raw_file = output_path / f"{species_name}_raw.csv"
        cleaned_file = output_path / f"{species_name}_cleaned.csv"
        thinned_file = output_path / f"{species_name}_thinned.csv"
        
        raw_df.to_csv(raw_file, index=False)
        cleaned_df.to_csv(cleaned_file, index=False)
        thinned_df.to_csv(thinned_file, index=False)
        
        results["output_files"] = {
            "raw": str(raw_file),
            "cleaned": str(cleaned_file),
            "thinned": str(thinned_file)
        }
        
        results["pipeline_end"] = datetime.now().isoformat()
        results["final_count"] = len(thinned_df)
        results["overall_retention"] = total_retention
        
        # Save provenance report
        save_provenance_report(output_path / f"{species_name}_provenance.json")
        
        logger.info(f"Pipeline completed successfully for {species_name}. Final count: {len(thinned_df)}")
        
        return results
        
    except Exception as e:
        logger.error(f"Pipeline failed for {species_name}: {str(e)}")
        results["pipeline_end"] = datetime.now().isoformat()
        results["status"] = "failed"
        results["error"] = str(e)
        raise

def main():
    """
    Main entry point for testing the GBIF pipeline.
    """
    # Example usage
    species = "Helianthus annuus"
    output_dir = "data/processed/occurrences"
    
    try:
        results = run_fetch_pipeline(
            species_name=species,
            output_dir=output_dir,
            max_records=5000,
            thinning_distance_km=10.0,
            min_retention_rate=0.80
        )
        print(f"Pipeline completed: {results}")
    except Exception as e:
        print(f"Pipeline failed: {e}")

if __name__ == "__main__":
    main()
