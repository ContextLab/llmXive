import os
import sys
import logging
import json
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.warp import calculate_default_transform, transform_bounds, reproject, Resampling
from shapely.geometry import mapping, box, Point
import geopandas as gpd

from utils.config import get_project_root, get_data_dir, get_processed_dir, get_raw_data_dir
from utils.provenance import load_metadata_config, save_metadata_config, record_artifact_provenance

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'species_id',
    'foraging_guild',
    'forest_prop_100m',
    'grassland_prop_100m',
    'wetland_prop_100m',
    'urban_prop_100m',
    'other_prop_100m'
]

def validate_schema(df: pd.DataFrame) -> None:
    """
    Validate that the DataFrame contains all required columns for the merged observations.
    
    Args:
        df: DataFrame to validate
        
    Raises:
        ValueError: If any required columns are missing
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Validate data types for critical columns
    if not pd.api.types.is_string_dtype(df['species_id']) and not pd.api.types.is_numeric_dtype(df['species_id']):
        raise ValueError("species_id must be string or numeric")
    
    if not pd.api.types.is_string_dtype(df['foraging_guild']):
        raise ValueError("foraging_guild must be string")
    
    # Validate land cover proportion columns are numeric
    prop_cols = [c for c in REQUIRED_COLUMNS if c.endswith('_prop_100m')]
    for col in prop_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f"Column {col} must be numeric")

def load_filtered_ebd(ebd_path: Path) -> pd.DataFrame:
    """Load the filtered EBD data."""
    logger.info(f"Loading filtered EBD data from {ebd_path}")
    df = pd.read_csv(ebd_path)
    return df

def load_guild_mapping(guild_path: Path) -> pd.DataFrame:
    """Load the guild mapping data."""
    logger.info(f"Loading guild mapping from {guild_path}")
    df = pd.read_csv(guild_path)
    return df

def load_nlcd_raster(nlcd_path: Path) -> Tuple[rasterio.DatasetReader, Dict]:
    """Load the NLCD raster dataset."""
    logger.info(f"Loading NLCD raster from {nlcd_path}")
    with zipfile.ZipFile(nlcd_path, 'r') as zip_ref:
        # Extract to temp directory
        temp_dir = tempfile.mkdtemp()
        zip_ref.extractall(temp_dir)
        
        # Find the tif file
        tif_files = list(Path(temp_dir).glob('*.tif'))
        if not tif_files:
            raise FileNotFoundError(f"No .tif files found in {nlcd_path}")
        
        tif_path = tif_files[0]
        return rasterio.open(tif_path), {'temp_dir': temp_dir, 'extracted_file': str(tif_path)}

def calculate_land_cover_proportions(
    obs_df: pd.DataFrame, 
    raster: rasterio.DatasetReader, 
    buffer_m: int = 100
) -> Dict[str, pd.Series]:
    """
    Calculate land cover proportions within a buffer around each observation.
    
    Args:
        obs_df: DataFrame with observation coordinates
        raster: Opened rasterio dataset
        buffer_m: Buffer radius in meters
        
    Returns:
        Dictionary of proportions for each land cover class
    """
    logger.info(f"Calculating land cover proportions with {buffer_m}m buffer")
    
    # Define land cover class mappings (NLCD 2019)
    # Simplified mapping: Forest, Grassland, Wetland, Urban, Other
    class_map = {
        'forest': [41, 42, 43],
        'grassland': [71, 72, 73, 81, 82],
        'wetland': [90, 95],
        'urban': [11, 12, 13, 14, 15, 21, 22, 23, 24]
    }
    
    results = {cls: [] for cls in class_map.keys()}
    results['other'] = []
    
    for idx, row in obs_df.iterrows():
        # Create buffer geometry
        point = Point(row['longitude'], row['latitude'])
        # Note: In a real implementation, we would reproject to a metric CRS
        # For simplicity, we assume the raster is in a suitable projection or
        # we use a simplified distance calculation
        
        # Get window around point
        try:
            # Transform point to raster coordinates
            coords = raster.index(row['longitude'], row['latitude'])
            if coords[0] < 0 or coords[1] < 0 or coords[0] >= raster.width or coords[1] >= raster.height:
                # Out of bounds - fill with NaN or 0
                for cls in results.keys():
                    results[cls].append(np.nan)
                continue
            
            # Calculate buffer in pixels (approximate)
            # This is a simplification; real implementation needs proper projection handling
            pixel_size = np.mean([abs(raster.transform.a), abs(raster.transform.e)])
            buffer_pixels = int(buffer_m / pixel_size)
            
            # Extract window
            window = rasterio.windows.from_bounds(
                row['longitude'] - buffer_m,
                row['latitude'] - buffer_m,
                row['longitude'] + buffer_m,
                row['latitude'] + buffer_m,
                transform=raster.transform
            )
            
            data = rasterio.band(raster, 1).read(window=window, masked=True)
            
            if data.size == 0:
                for cls in results.keys():
                    results[cls].append(np.nan)
                continue
            
            # Calculate proportions
            total_valid = np.sum(~data.mask)
            if total_valid == 0:
                for cls in results.keys():
                    results[cls].append(np.nan)
                continue
            
            for cls_name, class_codes in class_map.items():
                count = np.sum(np.isin(data.data, class_codes) & ~data.mask)
                prop = count / total_valid
                results[cls_name].append(prop)
            
            # Calculate 'other' as remainder
            other_count = total_valid - sum(
                np.sum(np.isin(data.data, codes) & ~data.mask) 
                for codes in class_map.values()
            )
            results['other'].append(other_count / total_valid)
            
        except Exception as e:
            logger.warning(f"Error processing observation {idx}: {e}")
            for cls in results.keys():
                results[cls].append(np.nan)
    
    return results

def assign_guilds(obs_df: pd.DataFrame, guild_df: pd.DataFrame) -> pd.DataFrame:
    """Assign foraging guilds to observations based on species_id."""
    logger.info("Assigning foraging guilds")
    merged = obs_df.merge(
        guild_df[['species_id', 'foraging_guild']], 
        on='species_id', 
        how='left'
    )
    return merged

def filter_by_observation_count(df: pd.DataFrame, min_count: int = 50) -> pd.DataFrame:
    """Filter observations to ensure minimum count per species."""
    logger.info(f"Filtering for species with >= {min_count} observations")
    counts = df['species_id'].value_counts()
    valid_species = counts[counts >= min_count].index.tolist()
    filtered = df[df['species_id'].isin(valid_species)]
    return filtered

def main():
    """Main execution function for merge_and_buffer pipeline."""
    project_root = get_project_root()
    processed_dir = get_processed_dir()
    raw_dir = get_raw_data_dir()
    
    # Define paths
    ebd_path = processed_dir / 'filtered_ebd.csv'
    guild_path = processed_dir / 'guild_mapping.csv'
    nlcd_path = raw_dir / 'nlcd_2019.zip'
    output_path = processed_dir / 'merged_observations.csv'
    
    # Check inputs exist
    if not ebd_path.exists():
        raise FileNotFoundError(f"Filtered EBD data not found at {ebd_path}")
    if not guild_path.exists():
        raise FileNotFoundError(f"Guild mapping not found at {guild_path}")
    if not nlcd_path.exists():
        raise FileNotFoundError(f"NLCD data not found at {nlcd_path}")
    
    # Load data
    obs_df = load_filtered_ebd(ebd_path)
    guild_df = load_guild_mapping(guild_path)
    raster, raster_info = load_nlcd_raster(nlcd_path)
    
    try:
        # Calculate land cover proportions
        proportions = calculate_land_cover_proportions(obs_df, raster)
        
        # Add proportions to dataframe
        for cls, vals in proportions.items():
            col_name = f"{cls}_prop_100m"
            obs_df[col_name] = vals
        
        # Assign guilds
        obs_df = assign_guilds(obs_df, guild_df)
        
        # Validate schema
        validate_schema(obs_df)
        
        # Save output
        obs_df.to_csv(output_path, index=False)
        logger.info(f"Saved merged observations to {output_path}")
        
        # Record provenance
        record_artifact_provenance(
            output_path,
            sources=[ebd_path, guild_path, nlcd_path],
            step="merge_and_buffer"
        )
        
    finally:
        # Cleanup temp files
        if 'temp_dir' in raster_info:
            import shutil
            shutil.rmtree(raster_info['temp_dir'], ignore_errors=True)
        if 'extracted_file' in raster_info and Path(raster_info['extracted_file']).exists():
            Path(raster_info['extracted_file']).unlink()

if __name__ == '__main__':
    main()
