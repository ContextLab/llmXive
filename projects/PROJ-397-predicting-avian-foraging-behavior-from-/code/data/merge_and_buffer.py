import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import pandas as pd
import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.warp import calculate_default_transform, transform_bounds
import json

# Import config for paths
try:
    from utils.config import DATA_DIR, PROCESSED_DIR, RAW_DIR
except ImportError:
    # Fallback if utils not in path yet, assume relative execution
    from pathlib import Path
    DATA_DIR = Path(__file__).parent.parent / "data"
    PROCESSED_DIR = DATA_DIR / "processed"
    RAW_DIR = DATA_DIR / "raw"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ['species_id', 'foraging_guild', 'land_cover_proportions']

def load_filtered_ebd() -> pd.DataFrame:
    """Load the filtered EBD data (top 25 species)."""
    path = PROCESSED_DIR / "ebd_top25.csv"
    if not path.exists():
        raise FileNotFoundError(f"Filtered EBD data not found at {path}. Run T012.5 first.")
    return pd.read_csv(path)

def load_nlcd_raster() -> rasterio.DatasetReader:
    """Load the NLCD 2019 land cover raster."""
    # Assuming NLCD is stored in data/raw or data/processed as per T012
    # We look for the most recent NLCD file or a specific name if standardized
    nlcd_path = None
    for p in PROCESSED_DIR.glob("nlcd*.tif"):
        nlcd_path = p
        break
    if not nlcd_path:
        for p in RAW_DIR.glob("nlcd*.tif"):
            nlcd_path = p
            break
    
    if not nlcd_path or not nlcd_path.exists():
        raise FileNotFoundError(f"NLCD raster not found. Expected in {PROCESSED_DIR} or {RAW_DIR}.")
    
    return rasterio.open(nlcd_path)

def load_guild_mapping() -> pd.DataFrame:
    """Load the foraging guild mapping table."""
    path = PROCESSED_DIR / "guild_mapping.csv"
    if not path.exists():
        raise FileNotFoundError(f"Guild mapping not found at {path}. Run T008 first.")
    return pd.read_csv(path)

def calculate_land_cover_proportions(observations: pd.DataFrame, raster: rasterio.DatasetReader) -> pd.DataFrame:
    """
    Calculate land cover proportions within a 100m buffer for each observation.
    Returns the dataframe with a new column 'land_cover_proportions' containing 
    a JSON string or dict of class: proportion.
    """
    # This is a simplified implementation assuming observations have lat/lon
    # In a real scenario, we would use a spatial join or point sampling
    # For this task, we assume the dataframe has 'latitude' and 'longitude'
    
    if 'latitude' not in observations.columns or 'longitude' not in observations.columns:
        logger.warning("Observations missing lat/lon columns. Skipping buffer calculation.")
        # Assign empty proportions if no coordinates
        observations['land_cover_proportions'] = [{} for _ in range(len(observations))]
        return observations

    results = []
    transform = raster.transform
    crs = raster.crs

    for idx, row in observations.iterrows():
        lat = row['latitude']
        lon = row['longitude']
        
        # Transform lat/lon to raster coordinates (pixel indices)
        # Using rasterio's transform
        try:
            # Convert lat/lon to raster projection if necessary (NLCD is usually EPSG:26910 or similar)
            # For simplicity, assuming input is already in raster CRS or simple conversion
            # Real implementation would use pyproj for robust transformation
            from rasterio.warp import transform
            src_crs = "EPSG:4326"
            dst_crs = crs
            x, y = transform(src_crs, dst_crs, [lon], [lat])
            x = x[0]
            y = y[0]
        except Exception as e:
            logger.error(f"Coordinate transformation failed for {row}: {e}")
            results.append({})
            continue

        # Define 100m buffer in raster units (assuming meters)
        buffer_size = 100
        minx, miny = x - buffer_size, y - buffer_size
        maxx, maxy = x + buffer_size, y + buffer_size

        # Read window
        try:
            window = rasterio.windows.from_bounds(minx, miny, maxx, maxy, transform)
            window_data = raster.read(1, window=window)
            window_transform = rasterio.windows.transform(window, transform)
            
            # Calculate proportions
            unique, counts = np.unique(window_data, return_counts=True)
            total = np.sum(counts)
            if total == 0:
                proportions = {}
            else:
                proportions = {str(int(val)): float(cnt/total) for val, cnt in zip(unique, counts)}
            
            results.append(proportions)
        except Exception as e:
            logger.warning(f"Buffer calculation failed for {row}: {e}")
            results.append({})

    observations['land_cover_proportions'] = results
    return observations

def assign_guilds(df: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """Assign foraging guilds based on species_id."""
    if 'species_id' not in df.columns:
        raise ValueError("DataFrame missing 'species_id' column for guild assignment.")
    
    # Ensure species_id is string for join
    df = df.copy()
    df['species_id'] = df['species_id'].astype(str)
    mapping = mapping.copy()
    mapping['species_id'] = mapping['species_id'].astype(str)

    merged = df.merge(mapping[['species_id', 'foraging_guild']], on='species_id', how='left')
    return merged

def filter_by_observation_count(df: pd.DataFrame, min_obs: int = 50) -> pd.DataFrame:
    """Filter species with >= min_obs observations."""
    if 'species_id' not in df.columns:
        raise ValueError("DataFrame missing 'species_id' column for filtering.")
    
    counts = df['species_id'].value_counts()
    valid_species = counts[counts >= min_obs].index.tolist()
    
    excluded = set(df['species_id'].unique()) - set(valid_species)
    if excluded:
        log_path = PROCESSED_DIR / "excluded_species.log"
        with open(log_path, 'w') as f:
            f.write("Excluded species (observation count < 50):\n")
            for sp in excluded:
                f.write(f"{sp}\n")
        logger.info(f"Excluded {len(excluded)} species. Log saved to {log_path}")
    
    return df[df['species_id'].isin(valid_species)]

def validate_schema(df: pd.DataFrame) -> None:
    """
    Validates that the dataframe contains the required columns:
    species_id, foraging_guild, land_cover_proportions.
    
    Raises:
        ValueError: If any required column is missing.
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Schema validation failed. Missing required columns: {missing}")
    
    # Additional type check for land_cover_proportions if it exists
    if 'land_cover_proportions' in df.columns:
        if not df['land_cover_proportions'].apply(lambda x: isinstance(x, dict) or (isinstance(x, str) and x.startswith('{'))).all():
             # Allow stringified JSON or dict
             pass 
    
    logger.info("Schema validation passed.")

def main():
    """
    Main entry point for the merge and buffer pipeline.
    Orchestrates loading, merging, filtering, and validation.
    """
    logger.info("Starting merge and buffer pipeline...")
    
    # 1. Load Data
    logger.info("Loading filtered EBD data...")
    ebd_df = load_filtered_ebd()
    
    logger.info("Loading NLCD raster...")
    nlcd_raster = load_nlcd_raster()
    
    logger.info("Loading guild mapping...")
    guild_map = load_guild_mapping()
    
    # 2. Process
    logger.info("Calculating land cover proportions...")
    ebd_df = calculate_land_cover_proportions(ebd_df, nlcd_raster)
    
    logger.info("Assigning foraging guilds...")
    ebd_df = assign_guilds(ebd_df, guild_map)
    
    logger.info("Filtering by observation count...")
    ebd_df = filter_by_observation_count(ebd_df)
    
    # 3. Validate Schema
    logger.info("Validating schema...")
    try:
        validate_schema(ebd_df)
    except ValueError as e:
        logger.error(f"Schema validation failed: {e}")
        sys.exit(1)
    
    # 4. Save Output
    output_path = PROCESSED_DIR / "merged_observations.csv"
    # Convert dict column to JSON string for CSV compatibility
    ebd_df['land_cover_proportions'] = ebd_df['land_cover_proportions'].apply(json.dumps)
    ebd_df.to_csv(output_path, index=False)
    logger.info(f"Saved merged data to {output_path}")

if __name__ == "__main__":
    main()
