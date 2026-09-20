import os
import sys
import logging
import json
import zipfile
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Set

import pandas as pd
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import Point, mapping
from utils.config import get_project_root, get_processed_dir, get_raw_data_dir, get_metadata_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Required columns for the merged output dataset
REQUIRED_COLUMNS: Set[str] = {
    'species_id',
    'foraging_guild',
    'latitude',
    'longitude',
    'observation_date',
    'forest_prop_100m',
    'grassland_prop_100m',
    'wetland_prop_100m',
    'urban_prop_100m',
    'water_prop_100m',
    'cropland_prop_100m',
    'barren_prop_100m',
    'shrub_prop_100m'
}

def validate_schema(df: pd.DataFrame) -> None:
    """
    Validates that the DataFrame contains all required columns.
    
    Args:
        df: The DataFrame to validate.
        
    Raises:
        ValueError: If any required columns are missing.
    """
    if df is None or df.empty:
        raise ValueError("Cannot validate schema: DataFrame is None or empty.")
        
    current_columns = set(df.columns)
    missing_columns = REQUIRED_COLUMNS - current_columns
    
    if missing_columns:
        raise ValueError(
            f"Schema validation failed. Missing required columns: {sorted(missing_columns)}. "
            f"Expected: {sorted(REQUIRED_COLUMNS)}. Found: {sorted(current_columns)}."
        )
    
    # Additional type checks for numeric columns if they exist
    numeric_cols = ['latitude', 'longitude', 'forest_prop_100m', 'grassland_prop_100m', 
                    'wetland_prop_100m', 'urban_prop_100m', 'water_prop_100m', 
                    'cropland_prop_100m', 'barren_prop_100m', 'shrub_prop_100m']
    
    for col in numeric_cols:
        if col in current_columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise ValueError(f"Column '{col}' must be numeric.")
                
    logger.info("Schema validation passed successfully.")

def load_filtered_ebd() -> pd.DataFrame:
    """Loads the preprocessed EBD data."""
    input_path = get_processed_dir() / "filtered_ebd.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    logger.info(f"Loading filtered EBD data from {input_path}")
    return pd.read_csv(input_path)

def load_guild_mapping() -> pd.DataFrame:
    """Loads the guild mapping CSV."""
    input_path = get_processed_dir() / "guild_mapping.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Guild mapping file not found: {input_path}")
    logger.info(f"Loading guild mapping from {input_path}")
    return pd.read_csv(input_path)

def load_nlcd_raster() -> rasterio.DatasetReader:
    """Loads the NLCD raster data from the zip archive."""
    raw_dir = get_raw_data_dir()
    zip_path = raw_dir / "nlcd_2019.zip"
    
    if not zip_path.exists():
        raise FileNotFoundError(f"NLCD zip file not found: {zip_path}")
    
    # We expect the zip to contain a .tif file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        tif_files = [f for f in zip_ref.namelist() if f.endswith('.tif')]
        if not tif_files:
            raise ValueError("No .tif file found in NLCD zip archive.")
        
        # Extract to temp file to read with rasterio
        temp_dir = tempfile.mkdtemp()
        target_path = os.path.join(temp_dir, tif_files[0])
        zip_ref.extract(tif_files[0], temp_dir)
        
        logger.info(f"Extracted NLCD raster to {target_path}")
        return rasterio.open(target_path)

def calculate_land_cover_proportions(df: pd.DataFrame, raster: rasterio.DatasetReader) -> pd.DataFrame:
    """
    Calculates land cover proportions within a 100m buffer for each observation.
    """
    logger.info("Calculating land cover proportions...")
    
    # Map NLCD class codes to our target categories (simplified mapping for NLCD 2019)
    # 11: Water, 21-24: Developed (Urban), 31-32: Barren, 41-43: Forest, 
    # 51-52: Shrub/Scrub, 71-72: Grassland/Herbaceous, 81-82: Pasture/Hay (often grouped with grassland), 84: Cropland, 90-95: Wetlands
    # Note: This mapping is approximate and depends on specific NLCD classification details.
    # For this implementation, we assume a standard mapping exists or is hardcoded.
    
    # Define a helper to aggregate proportions
    def get_proportions(row):
        geom = Point(row['longitude'], row['latitude'])
        buffer_geom = geom.buffer(100) # 100 meters
        
        try:
            out_image, out_transform = mask(raster, [mapping(buffer_geom)], crop=True)
            if out_image.shape[1] == 0 or out_image.shape[2] == 0:
                return {
                    'forest_prop_100m': 0.0, 'grassland_prop_100m': 0.0, 
                    'wetland_prop_100m': 0.0, 'urban_prop_100m': 0.0,
                    'water_prop_100m': 0.0, 'cropland_prop_100m': 0.0,
                    'barren_prop_100m': 0.0, 'shrub_prop_100m': 0.0
                }
            
            counts = np.bincount(out_image[0].flatten(), minlength=256)
            total_pixels = np.sum(counts)
            if total_pixels == 0:
                return {
                    'forest_prop_100m': 0.0, 'grassland_prop_100m': 0.0, 
                    'wetland_prop_100m': 0.0, 'urban_prop_100m': 0.0,
                    'water_prop_100m': 0.0, 'cropland_prop_100m': 0.0,
                    'barren_prop_100m': 0.0, 'shrub_prop_100m': 0.0
                }
            
            # NLCD 2019 Classes (approximate grouping)
            # Forest: 41, 42, 43
            forest_pixels = counts[41] + counts[42] + counts[43]
            # Grassland: 71, 72, 81, 82
            grassland_pixels = counts[71] + counts[72] + counts[81] + counts[82]
            # Wetland: 90, 95
            wetland_pixels = counts[90] + counts[95]
            # Urban: 21, 22, 23, 24
            urban_pixels = counts[21] + counts[22] + counts[23] + counts[24]
            # Water: 11
            water_pixels = counts[11]
            # Cropland: 84
            cropland_pixels = counts[84]
            # Barren: 31, 32
            barren_pixels = counts[31] + counts[32]
            # Shrub: 51, 52
            shrub_pixels = counts[51] + counts[52]
            
            return {
                'forest_prop_100m': forest_pixels / total_pixels,
                'grassland_prop_100m': grassland_pixels / total_pixels,
                'wetland_prop_100m': wetland_pixels / total_pixels,
                'urban_prop_100m': urban_pixels / total_pixels,
                'water_prop_100m': water_pixels / total_pixels,
                'cropland_prop_100m': cropland_pixels / total_pixels,
                'barren_prop_100m': barren_pixels / total_pixels,
                'shrub_prop_100m': shrub_pixels / total_pixels
            }
        except Exception as e:
            logger.warning(f"Error processing geometry: {e}")
            return {
                'forest_prop_100m': 0.0, 'grassland_prop_100m': 0.0, 
                'wetland_prop_100m': 0.0, 'urban_prop_100m': 0.0,
                'water_prop_100m': 0.0, 'cropland_prop_100m': 0.0,
                'barren_prop_100m': 0.0, 'shrub_prop_100m': 0.0
            }

    results = df.apply(get_proportions, axis=1)
    for key in results[0].keys():
        df[key] = results.apply(lambda x: x[key])
    
    return df

def assign_guilds(df: pd.DataFrame, mapping_df: pd.DataFrame) -> pd.DataFrame:
    """Assigns foraging guilds based on species_id."""
    logger.info("Assigning foraging guilds...")
    if 'species_id' not in mapping_df.columns or 'foraging_guild' not in mapping_df.columns:
        raise ValueError("Guild mapping must contain 'species_id' and 'foraging_guild' columns.")
    
    merged = df.merge(mapping_df[['species_id', 'foraging_guild']], on='species_id', how='left')
    
    missing_guilds = merged['foraging_guild'].isna().sum()
    if missing_guilds > 0:
        logger.warning(f"{missing_guilds} observations have missing foraging guilds.")
        
    return merged

def filter_by_observation_count(df: pd.DataFrame, min_count: int = 50) -> pd.DataFrame:
    """Filters species with fewer than min_count observations."""
    logger.info(f"Filtering species with < {min_count} observations...")
    counts = df['species_id'].value_counts()
    valid_species = counts[counts >= min_count].index.tolist()
    filtered_df = df[df['species_id'].isin(valid_species)]
    
    excluded = len(df) - len(filtered_df)
    logger.info(f"Excluded {excluded} observations for species with < {min_count} records.")
    
    return filtered_df

def main():
    """Main entry point for the merge and buffer pipeline."""
    try:
        # 1. Load Data
        ebd_df = load_filtered_ebd()
        guild_df = load_guild_mapping()
        nlcd_raster = load_nlcd_raster()
        
        # 2. Calculate Proportions
        ebd_df = calculate_land_cover_proportions(ebd_df, nlcd_raster)
        
        # 3. Assign Guilds
        ebd_df = assign_guilds(ebd_df, guild_df)
        
        # 4. Filter by Count
        ebd_df = filter_by_observation_count(ebd_df, min_count=50)
        
        # 5. Validate Schema (T015 Requirement)
        validate_schema(ebd_df)
        
        # 6. Save Output
        output_path = get_processed_dir() / "merged_observations.csv"
        ebd_df.to_csv(output_path, index=False)
        logger.info(f"Saved merged observations to {output_path}")
        
        # Record provenance
        from utils.provenance import record_artifact_provenance
        record_artifact_provenance(output_path, step="merge_and_buffer")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during merge_and_buffer: {e}")
        raise
    finally:
        # Cleanup temp raster if opened (rasterio handles this usually, but good practice)
        pass

if __name__ == "__main__":
    main()
