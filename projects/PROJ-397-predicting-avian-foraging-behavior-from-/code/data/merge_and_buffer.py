import os
import sys
import logging
import json
import zipfile
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.crs import CRS
from shapely.geometry import Point, mapping

# Import from project utils
from utils.config import get_project_root, get_data_dir, get_processed_dir, get_raw_data_dir
from utils.provenance import record_artifact_provenance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration Constants ---
# These should ideally come from config.py, but are hardcoded here for the task scope
# as per the existing API surface constraints.
BUFFER_RADIUS_METERS = 100
OBSERVATION_THRESHOLD = 50
PROJECT_ROOT = get_project_root()
DATA_DIR = get_data_dir()
PROCESSED_DIR = get_processed_dir()
RAW_DATA_DIR = get_raw_data_dir()

def load_filtered_ebd(top_species_path: Optional[Path] = None) -> pd.DataFrame:
    """Load eBird data and filter to top species."""
    if top_species_path is None:
        top_species_path = PROCESSED_DIR / "top_25_species_ids.json"
    
    if not top_species_path.exists():
        raise FileNotFoundError(f"Top species list not found at {top_species_path}")
    
    with open(top_species_path, 'r') as f:
        top_species_ids = json.load(f)
    
    ebd_path = RAW_DATA_DIR / "ebd_train.csv"
    if not ebd_path.exists():
        ebd_path = RAW_DATA_DIR / "ebd_train_fallback.parquet"
    
    if ebd_path.suffix == '.parquet':
        df = pd.read_parquet(ebd_path)
    else:
        df = pd.read_csv(ebd_path)
    
    # Filter to top species
    filtered_df = df[df['species_id'].isin(top_species_ids)].copy()
    logger.info(f"Loaded {len(filtered_df)} observations for {len(top_species_ids)} species.")
    return filtered_df

def load_guild_mapping(mapping_path: Optional[Path] = None) -> pd.DataFrame:
    """Load the generated guild mapping."""
    if mapping_path is None:
        mapping_path = PROCESSED_DIR / "guild_mapping.csv"
    
    if not mapping_path.exists():
        raise FileNotFoundError(f"Guild mapping not found at {mapping_path}")
    
    return pd.read_csv(mapping_path)

def load_nlcd_raster(nlcd_path: Optional[Path] = None) -> rasterio.DatasetReader:
    """Load the NLCD raster dataset."""
    if nlcd_path is None:
        # Check for primary then fallback
        primary = RAW_DATA_DIR / "nlcd_2019.zip"
        fallback = RAW_DATA_DIR / "nlcd_2019_fallback.zip"
        
        if primary.exists():
            nlcd_path = primary
        elif fallback.exists():
            nlcd_path = fallback
        else:
            raise FileNotFoundError("NLCD data not found. Run download_nlcd.py first.")
    
    # Unzip if necessary
    if nlcd_path.suffix == '.zip':
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(nlcd_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
                # Find the .tif file
                tif_files = list(Path(tmpdir).rglob("*.tif"))
                if not tif_files:
                    raise FileNotFoundError("No .tif file found in NLCD zip.")
                raster_path = tif_files[0]
            return rasterio.open(raster_path)
    else:
        return rasterio.open(nlcd_path)

def calculate_land_cover_proportions(
    obs_df: pd.DataFrame, 
    raster: rasterio.DatasetReader,
    buffer_m: int = BUFFER_RADIUS_METERS
) -> pd.DataFrame:
    """Calculate land cover proportions within a buffer for each observation."""
    # Ensure CRS is projected for distance calculations
    if not raster.crs.is_projected:
        # Reproject raster to a projected CRS (e.g., UTM Zone 15N for central US)
        # In a real pipeline, we might reproject on the fly or use a global projection
        # For this task, we assume the raster is already projected or we handle it simply.
        # A robust solution would reproject the raster or the points.
        logger.warning("Raster CRS is not projected. Assuming data is already in a projected CRS or using a default projection.")
    
    # Create geometry column for observations
    # Assuming columns 'longitude' and 'latitude' exist in obs_df
    if 'longitude' not in obs_df.columns or 'latitude' not in obs_df.columns:
        # Try common aliases
        if 'lon' in obs_df.columns and 'lat' in obs_df.columns:
            obs_df['longitude'] = obs_df['lon']
            obs_df['latitude'] = obs_df['lat']
        else:
            raise ValueError("Observation data must contain 'longitude' and 'latitude' columns.")
    
    geometry = [Point(xy) for xy in zip(obs_df['longitude'], obs_df['latitude'])]
    gdf = gpd.GeoDataFrame(obs_df, geometry=geometry, crs="EPSG:4326")
    
    # Reproject to a projected CRS (e.g., UTM) for accurate buffer calculation
    # We'll use a generic UTM zone or a state plane if we knew the location, 
    # but for simplicity in this script, we'll assume a generic projected CRS 
    # or reproject to the raster's CRS if it's projected.
    if raster.crs.is_projected:
        gdf = gdf.to_crs(raster.crs)
    else:
        # Fallback to a standard projected CRS if raster is not projected
        # This is a simplification; in production, we'd determine the appropriate UTM zone.
        gdf = gdf.to_crs("EPSG:3857") # Web Mercator (approximate for small areas)
    
    # Calculate buffer proportions
    results = []
    for idx, row in gdf.iterrows():
        buffer_geom = row['geometry'].buffer(buffer_m)
        # Mask the raster with the buffer
        try:
            out_image, out_transform = mask(raster, [mapping(buffer_geom)], crop=True)
            out_mask = out_image[0] > 0 # Assuming 0 is nodata
            
            # Count values
            unique, counts = np.unique(out_image[0][out_mask], return_counts=True)
            total_pixels = len(out_image[0][out_mask])
            
            if total_pixels == 0:
                proportions = {}
            else:
                proportions = {f"lc_{int(val)}": int(cnt) / total_pixels for val, cnt in zip(unique, counts)}
            
            # Store original row data + proportions
            row_dict = row.drop('geometry').to_dict()
            row_dict.update(proportions)
            results.append(row_dict)
        except Exception as e:
            logger.warning(f"Failed to calculate buffer for observation {idx}: {e}")
            # Append row with NaN or 0 proportions
            row_dict = row.drop('geometry').to_dict()
            # Add placeholder columns for known land cover classes if needed
            results.append(row_dict)
    
    return pd.DataFrame(results)

def assign_guilds(merged_df: pd.DataFrame, guild_df: pd.DataFrame) -> pd.DataFrame:
    """Assign foraging guilds to observations based on species_id."""
    if 'species_id' not in guild_df.columns or 'foraging_guild' not in guild_df.columns:
        raise ValueError("Guild mapping must contain 'species_id' and 'foraging_guild' columns.")
    
    merged_df = merged_df.merge(
        guild_df[['species_id', 'foraging_guild']], 
        on='species_id', 
        how='left'
    )
    return merged_df

def filter_by_observation_count(df: pd.DataFrame, min_count: int = OBSERVATION_THRESHOLD) -> pd.DataFrame:
    """Filter observations to ensure statistical power (>= min_count per species)."""
    # This is usually done before merging, but if done here, we count again.
    # The task description says "filter for statistical power", which implies
    # the final output should only contain species meeting this criteria.
    # However, T012.5 already selects top species and T013 filters EBD.
    # This function serves as a final safety check or re-filtering if needed.
    species_counts = df['species_id'].value_counts()
    valid_species = species_counts[species_counts >= min_count].index
    filtered_df = df[df['species_id'].isin(valid_species)]
    
    dropped = df.shape[0] - filtered_df.shape[0]
    if dropped > 0:
        logger.info(f"Dropped {dropped} observations for species with < {min_count} records.")
    
    return filtered_df

def validate_schema(df: pd.DataFrame) -> None:
    """
    Validate that the DataFrame contains required columns.
    Raises ValueError if columns are missing.
    """
    required_columns = ['species_id', 'foraging_guild']
    
    # Check for standard land cover proportion columns
    # The schema might define specific LC classes, but we check for the pattern
    # or the existence of at least one land cover column if the schema is dynamic.
    # Based on the task: "individual columns for land cover proportions"
    # We check for the presence of columns starting with 'lc_' or 'prop_'
    # or specifically defined in a schema file if available.
    # For this implementation, we enforce the presence of the core columns
    # and verify that land cover columns exist.
    
    missing_core = [col for col in required_columns if col not in df.columns]
    if missing_core:
        raise ValueError(f"Missing required core columns: {missing_core}")
    
    # Check for land cover proportions
    lc_cols = [col for col in df.columns if col.startswith('lc_') or 'prop' in col.lower()]
    if not lc_cols:
        # It's possible the schema expects specific columns like 'forest_prop', etc.
        # If the schema is strict, we might need to load it.
        # For now, we assume if no 'lc_' or 'prop' columns exist, it's invalid.
        # However, to be robust against the specific "individual columns" requirement,
        # we check if ANY land cover related columns exist.
        # If the task implies specific names, we might need to hardcode them or load a schema.
        # Let's assume the pattern 'lc_<value>' is used based on calculate_land_cover_proportions.
        raise ValueError("Missing land cover proportion columns. Expected columns starting with 'lc_' or containing 'prop'.")
    
    logger.info(f"Schema validation passed. Found {len(lc_cols)} land cover columns.")

def main():
    """Main execution function for T013 (merge_and_buffer)."""
    logger.info("Starting merge_and_buffer pipeline (T013).")
    
    try:
        # 1. Load data
        ebd_df = load_filtered_ebd()
        guild_df = load_guild_mapping()
        raster = load_nlcd_raster()
        
        # 2. Calculate land cover proportions
        logger.info("Calculating land cover proportions...")
        merged_df = calculate_land_cover_proportions(ebd_df, raster)
        
        # 3. Assign guilds
        logger.info("Assigning foraging guilds...")
        merged_df = assign_guilds(merged_df, guild_df)
        
        # 4. Validate Schema (T015 requirement)
        logger.info("Validating schema...")
        validate_schema(merged_df)
        
        # 5. Filter by observation count (safety check)
        merged_df = filter_by_observation_count(merged_df)
        
        # 6. Save output
        output_path = PROCESSED_DIR / "merged_observations.csv"
        merged_df.to_csv(output_path, index=False)
        logger.info(f"Saved merged observations to {output_path}")
        
        # 7. Record provenance
        record_artifact_provenance(output_path, "T013-merge_and_buffer")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
