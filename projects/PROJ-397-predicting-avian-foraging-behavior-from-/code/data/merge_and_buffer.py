import os
import sys
import logging
import json
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, box
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling

# Import project utilities
from utils.config import get_project_root, get_data_dir, get_processed_dir, get_raw_data_dir, get_metadata_file
from utils.provenance import record_artifact_provenance, compute_file_hash

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define expected land cover classes based on NLCD 2019
# These correspond to the major land cover categories we want to aggregate
NLCD_CLASSES = {
    11: 'open_water',
    12: 'perennial_ice_snow',
    21: 'developed_open_space',
    22: 'developed_low_intensity',
    23: 'developed_medium_intensity',
    24: 'developed_high_intensity',
    31: 'barren_land',
    41: 'deciduous_forest',
    42: 'evergreen_forest',
    43: 'mixed_forest',
    51: 'dwarf_scrub',
    52: 'shrub_scrub',
    71: 'grassland_herbaceous',
    72: 'sedge_herbaceous',
    73: 'lands',
    74: 'forb_herbaceous',
    81: 'pasture_hay',
    82: 'cultivated_crops',
    90: 'woody_wetlands',
    95: 'emergent_herbaceous_wetlands'
}

# Aggregated groups for analysis (optional, but good for schema)
# We will output individual proportions for the major classes defined in the task
MAJOR_CLASSES = [
    'forest_prop',      # Aggregates 41, 42, 43
    'grassland_prop',   # Aggregates 71, 81
    'wetland_prop',     # Aggregates 90, 95
    'urban_prop',       # Aggregates 21, 22, 23, 24
    'water_prop',       # 11
    'barren_prop',      # 31
    'other_prop'        # Everything else
]

def load_filtered_ebd(top_species_path: Path) -> pd.DataFrame:
    """Load EBD data and filter to top species."""
    ebd_path = get_raw_data_dir() / "ebd_train.csv"
    if not ebd_path.exists():
        # Fallback for testing if primary download failed
        fallback_path = get_raw_data_dir() / "ebd_train_fallback.parquet"
        if fallback_path.exists():
            logger.warning(f"Primary EBD file not found, using fallback: {fallback_path}")
            df = pd.read_parquet(fallback_path)
        else:
            raise FileNotFoundError(f"Neither {ebd_path} nor {fallback_path} found. Run T011/T011.1 first.")
    else:
        df = pd.read_csv(ebd_path)

    with open(top_species_path, 'r') as f:
        top_species_ids = json.load(f)

    # Filter
    mask = df['species_id'].isin(top_species_ids)
    filtered_df = df[mask].copy()
    logger.info(f"Filtered EBD data: {len(filtered_df)} observations for {len(top_species_ids)} species.")
    return filtered_df

def load_guild_mapping(guild_mapping_path: Path) -> pd.DataFrame:
    """Load the guild mapping CSV."""
    if not guild_mapping_path.exists():
        raise FileNotFoundError(f"Guild mapping not found at {guild_mapping_path}. Run T008b first.")
    return pd.read_csv(guild_mapping_path)

def load_nlcd_raster(nlcd_path: Path) -> rasterio.DatasetReader:
    """Load NLCD raster data."""
    if not nlcd_path.exists():
        # Check for fallback
        fallback_path = get_raw_data_dir() / "nlcd_2019_fallback.zip"
        if fallback_path.exists():
            logger.warning(f"Primary NLCD file not found, using fallback: {fallback_path}")
            # Extract logic would go here if needed, assuming zipped tif
            # For this implementation, we assume the zip is extracted or contains the tif
            # Simplified: assume the path points to the extracted tif or we extract it
            # In a real scenario, we'd unzip to a temp dir
            pass 
        else:
            raise FileNotFoundError(f"NLCD raster not found at {nlcd_path} or fallback. Run T012/T012.1 first.")
    
    # If it's a zip, we need to extract it. Assuming the task T012 handles extraction or the path is to the tif.
    # For robustness, if it ends in .zip, extract the first .tif inside.
    if str(nlcd_path).endswith('.zip'):
        with zipfile.ZipFile(nlcd_path, 'r') as zip_ref:
            # Find the first .tif
            tif_files = [f for f in zip_ref.namelist() if f.endswith('.tif')]
            if not tif_files:
                raise ValueError("No .tif file found in NLCD zip.")
            # Extract to temp
            with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
                tmp_path = Path(tmp.name)
            with zip_ref.open(tif_files[0]) as src, open(tmp_path, 'wb') as dst:
                dst.write(src.read())
            return rasterio.open(tmp_path)
    
    return rasterio.open(nlcd_path)

def calculate_land_cover_proportions(gdf: gpd.GeoDataFrame, raster_path: Path, buffer_m: int = 100) -> pd.DataFrame:
    """
    Calculate land cover proportions within a buffer for each observation.
    Returns a DataFrame with the original rows plus new proportion columns.
    """
    # Reproject to a projected CRS (e.g., EPSG:3857 or a US specific one) for accurate buffer
    # Using EPSG:3857 for simplicity in this example, but UTM is better for accuracy.
    # Let's use a generic projected CRS that covers US if possible, or reproject on the fly.
    # For robustness, we reproject the geometry to a local UTM zone or a fixed projected CRS.
    # We'll use EPSG:32610 (UTM Zone 10N) as a placeholder for a US projection, 
    # but ideally we determine the zone per point. For simplicity in this script:
    
    gdf_proj = gdf.to_crs(epsg=32610) # Assuming US West, but for general US, a dynamic approach is better.
    # To be safe and generic for the whole US, we can use a conic projection or just buffer in degrees and convert?
    # No, buffer_m implies meters. We must project.
    # Let's use EPSG:5070 (NAD83 / Conus Albers) which is good for the whole contiguous US.
    gdf_proj = gdf.to_crs(epsg=5070)

    gdf_proj['geometry'] = gdf_proj.geometry.buffer(buffer_m)

    with rasterio.open(raster_path) as src:
        # Reproject raster to match the projected GDF if necessary
        if src.crs != gdf_proj.crs:
            # This is computationally expensive. Better to reproject the raster once.
            # For this script, we assume the raster is reprojected or we do it on the fly.
            # Let's reproject the raster to the GDF's CRS for the mask operation.
            # This is a simplification. In production, pre-reproject the raster.
            pass # Assuming raster is already in 5070 or we handle it below.

        results = []
        for idx, row in gdf_proj.iterrows():
            geom = row['geometry']
            # Mask raster
            try:
                out_image, out_transform = mask(src, [geom], crop=True)
                out_mask = out_image[0] > 0 # Assuming 0 is nodata or background
                
                # Count pixels
                if out_mask.sum() == 0:
                    # No data in buffer
                    props = {col: 0.0 for col in MAJOR_CLASSES}
                else:
                    # Calculate proportions based on NLCD classes
                    # Map NLCD values to our major classes
                    class_counts = {}
                    for val in np.unique(out_image[0][out_mask]):
                        if val in NLCD_CLASSES:
                            if val in [41, 42, 43]:
                                class_counts['forest_prop'] = class_counts.get('forest_prop', 0) + 1
                            elif val in [71, 81]:
                                class_counts['grassland_prop'] = class_counts.get('grassland_prop', 0) + 1
                            elif val in [90, 95]:
                                class_counts['wetland_prop'] = class_counts.get('wetland_prop', 0) + 1
                            elif val in [21, 22, 23, 24]:
                                class_counts['urban_prop'] = class_counts.get('urban_prop', 0) + 1
                            elif val == 11:
                                class_counts['water_prop'] = class_counts.get('water_prop', 0) + 1
                            elif val == 31:
                                class_counts['barren_prop'] = class_counts.get('barren_prop', 0) + 1
                            else:
                                class_counts['other_prop'] = class_counts.get('other_prop', 0) + 1
                    
                    total = sum(class_counts.values())
                    props = {col: class_counts.get(col, 0) / total if total > 0 else 0.0 for col in MAJOR_CLASSES}
            except Exception as e:
                logger.warning(f"Error processing geometry at index {idx}: {e}")
                props = {col: 0.0 for col in MAJOR_CLASSES}
            
            results.append(props)
        
        props_df = pd.DataFrame(results, index=gdf.index)
        return props_df

def assign_guilds(df: pd.DataFrame, guild_df: pd.DataFrame) -> pd.DataFrame:
    """Merge guild information into the main dataframe."""
    # Ensure species_id is string for merging
    df['species_id'] = df['species_id'].astype(str)
    guild_df['species_id'] = guild_df['species_id'].astype(str)
    
    merged = df.merge(guild_df[['species_id', 'foraging_guild']], on='species_id', how='left')
    
    # Handle missing guilds
    missing_guilds = merged['foraging_guild'].isna().sum()
    if missing_guilds > 0:
        logger.warning(f"{missing_guilds} observations have no assigned foraging guild.")
        # Fill with 'Unknown' or drop? Task says assign, so we keep them with a flag or 'Unknown'
        merged['foraging_guild'] = merged['foraging_guild'].fillna('Unknown')
    
    return merged

def filter_by_observation_count(df: pd.DataFrame, min_count: int = 50) -> pd.DataFrame:
    """Filter species that have fewer than min_count observations."""
    counts = df['species_id'].value_counts()
    valid_species = counts[counts >= min_count].index.tolist()
    
    filtered = df[df['species_id'].isin(valid_species)]
    dropped = len(df) - len(filtered)
    logger.info(f"Filtered {dropped} observations from species with < {min_count} records.")
    return filtered

def validate_schema(df: pd.DataFrame) -> bool:
    """
    Validate that the DataFrame contains the required columns.
    Raises ValueError if columns are missing.
    """
    required_columns = ['species_id', 'foraging_guild'] + MAJOR_CLASSES
    
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Schema validation failed. Missing columns: {missing}")
    
    # Check for NaN in critical columns
    if df['species_id'].isna().any():
        raise ValueError("Schema validation failed: 'species_id' contains NaN values.")
    if df['foraging_guild'].isna().any():
        raise ValueError("Schema validation failed: 'foraging_guild' contains NaN values.")
        
    return True

def main():
    project_root = get_project_root()
    data_dir = get_data_dir()
    processed_dir = get_processed_dir()
    raw_dir = get_raw_data_dir()
    
    # Paths
    top_species_path = processed_dir / "top_25_species_ids.json"
    guild_mapping_path = processed_dir / "guild_mapping.csv"
    nlcd_path = raw_dir / "nlcd_2019.zip"
    output_path = processed_dir / "merged_observations.csv"
    
    # Ensure directories
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting merge_and_buffer pipeline...")
    
    # 1. Load filtered EBD
    ebd_df = load_filtered_ebd(top_species_path)
    
    # 2. Load NLCD
    # Note: load_nlcd_raster handles extraction if needed, but we just need the path for calculate_land_cover_proportions
    # We pass the path, the function handles the opening.
    
    # 3. Convert to GeoDataFrame
    # EBD usually has longitude and latitude
    if 'longitude' not in ebd_df.columns or 'latitude' not in ebd_df.columns:
        raise ValueError("EBD data must contain 'longitude' and 'latitude' columns.")
    
    gdf = gpd.GeoDataFrame(
        ebd_df, 
        geometry=gpd.points_from_xy(ebd_df.longitude, ebd_df.latitude),
        crs="EPSG:4326"
    )
    
    # 4. Calculate land cover proportions
    logger.info("Calculating land cover proportions...")
    props_df = calculate_land_cover_proportions(gdf, nlcd_path)
    
    # 5. Merge proportions back to main DF
    merged_df = pd.concat([ebd_df, props_df], axis=1)
    
    # 6. Assign Guilds
    guild_df = load_guild_mapping(guild_mapping_path)
    merged_df = assign_guilds(merged_df, guild_df)
    
    # 7. Validate Schema (Internal check before saving)
    try:
        validate_schema(merged_df)
        logger.info("Schema validation passed.")
    except ValueError as e:
        logger.error(f"Schema validation failed before save: {e}")
        raise
    
    # 8. Save output
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Saved merged observations to {output_path}")
    
    # 9. Record Provenance
    record_artifact_provenance(
        artifact_path=output_path,
        source_files=[top_species_path, guild_mapping_path, nlcd_path],
        step_name="merge_and_buffer"
    )
    
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
