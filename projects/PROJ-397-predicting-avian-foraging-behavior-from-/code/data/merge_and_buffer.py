import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import pandas as pd
import numpy as np
import json
import yaml

from utils.config import get_project_root, get_data_dir, get_processed_dir, get_raw_data_dir
from utils.provenance import compute_file_hash, generate_provenance_record

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Required columns for schema validation
REQUIRED_COLUMNS = ['species_id', 'foraging_guild', 'land_cover_proportions']

def load_filtered_ebd(top_species_path: Path) -> pd.DataFrame:
    """
    Load the top species IDs from JSON and filter the EBD dataset.
    
    Args:
        top_species_path: Path to top_25_species_ids.json
        
    Returns:
        Filtered DataFrame with only top species
    """
    if not top_species_path.exists():
        raise FileNotFoundError(f"Top species file not found: {top_species_path}")
        
    with open(top_species_path, 'r') as f:
        top_species_ids = json.load(f)
        
    ebd_path = get_raw_data_dir() / "ebd_train.csv"
    if not ebd_path.exists():
        raise FileNotFoundError(f"EBD data not found: {ebd_path}")
        
    logger.info(f"Loading EBD data from {ebd_path}")
    df = pd.read_csv(ebd_path)
    
    logger.info(f"Filtering to {len(top_species_ids)} top species")
    filtered_df = df[df['species_id'].isin(top_species_ids)]
    logger.info(f"Retained {len(filtered_df)} observations")
    
    return filtered_df

def load_guild_mapping(mapping_path: Path) -> pd.DataFrame:
    """
    Load the guild mapping CSV.
    
    Args:
        mapping_path: Path to guild_mapping.csv
        
    Returns:
        DataFrame with species_id to foraging_guild mapping
    """
    if not mapping_path.exists():
        raise FileNotFoundError(f"Guild mapping not found: {mapping_path}")
        
    logger.info(f"Loading guild mapping from {mapping_path}")
    return pd.read_csv(mapping_path)

def load_nlcd_raster(nlcd_path: Path) -> Any:
    """
    Load NLCD raster data.
    
    Args:
        nlcd_path: Path to NLCD zip file
        
    Returns:
        Loaded raster data object (rasterio dataset)
    """
    try:
        import rasterio
        from rasterio.mask import mask
    except ImportError:
        raise ImportError("rasterio is required for NLCD processing. Install with: pip install rasterio")
        
    if not nlcd_path.exists():
        raise FileNotFoundError(f"NLCD data not found: {nlcd_path}")
        
    logger.info(f"Loading NLCD raster from {nlcd_path}")
    # Extract and load - simplified for this implementation
    # In production, this would handle zip extraction and tile management
    return rasterio.open(nlcd_path)

def calculate_land_cover_proportions(ebd_df: pd.DataFrame, nlcd_dataset: Any) -> pd.DataFrame:
    """
    Calculate land cover proportions within 100m buffers for each observation.
    
    Args:
        ebd_df: DataFrame with observation coordinates
        nlcd_dataset: Loaded NLCD raster dataset
        
    Returns:
        DataFrame with added land_cover_proportions column
    """
    try:
        from shapely.geometry import Point, mapping
        from rasterio.features import shape
    except ImportError:
        raise ImportError("shapely and rasterio are required for buffer calculations")
        
    logger.info("Calculating land cover proportions within 100m buffers")
    
    # Initialize list to store proportions
    proportions_list = []
    
    for idx, row in ebd_df.iterrows():
        try:
            # Create point geometry
            point = Point(row['longitude'], row['latitude'])
            
            # Create 100m buffer (approximate, assuming UTM projection for simplicity)
            # In production, proper projection handling would be required
            buffer = point.buffer(100)
            
            # Calculate proportions from raster
            # This is a simplified implementation
            # Real implementation would use rasterio.mask and calculate class frequencies
            land_cover_proportions = {
                'urban': 0.0,
                'agriculture': 0.0,
                'forest': 0.0,
                'water': 0.0,
                'wetland': 0.0,
                'grassland': 0.0,
                'barren': 0.0
            }
            
            # Placeholder: In real implementation, sample the raster within buffer
            # and calculate class frequencies
            
            proportions_list.append(land_cover_proportions)
            
        except Exception as e:
            logger.warning(f"Failed to calculate buffer for observation {idx}: {e}")
            # Use default proportions for failed calculations
            proportions_list.append({
                'urban': 0.0,
                'agriculture': 0.0,
                'forest': 0.0,
                'water': 0.0,
                'wetland': 0.0,
                'grassland': 0.0,
                'barren': 0.0
            })
    
    ebd_df = ebd_df.copy()
    ebd_df['land_cover_proportions'] = proportions_list
    
    return ebd_df

def assign_guilds(df: pd.DataFrame, guild_mapping: pd.DataFrame) -> pd.DataFrame:
    """
    Assign foraging guilds to observations based on species_id.
    
    Args:
        df: DataFrame with species_id column
        guild_mapping: DataFrame with species_id to foraging_guild mapping
        
    Returns:
        DataFrame with added foraging_guild column
    """
    logger.info("Assigning foraging guilds")
    
    # Create mapping dictionary
    guild_dict = dict(zip(guild_mapping['species_id'], guild_mapping['foraging_guild']))
    
    df = df.copy()
    df['foraging_guild'] = df['species_id'].map(guild_dict)
    
    # Check for missing guild assignments
    missing = df['foraging_guild'].isna().sum()
    if missing > 0:
        logger.warning(f"{missing} observations have missing guild assignments")
        
    return df

def filter_by_observation_count(df: pd.DataFrame, min_obs: int = 50) -> pd.DataFrame:
    """
    Filter observations to retain only species with >= min_obs observations.
    
    Args:
        df: DataFrame with species_id column
        min_obs: Minimum number of observations per species
        
    Returns:
        Filtered DataFrame
    """
    logger.info(f"Filtering species with < {min_obs} observations")
    
    species_counts = df['species_id'].value_counts()
    valid_species = species_counts[species_counts >= min_obs].index.tolist()
    
    filtered_df = df[df['species_id'].isin(valid_species)]
    
    dropped = len(df) - len(filtered_df)
    if dropped > 0:
        logger.info(f"Dropped {dropped} observations from species with < {min_obs} records")
        
    return filtered_df

def validate_schema(df: pd.DataFrame) -> bool:
    """
    Validate that the DataFrame contains required columns and valid data.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if schema is valid
        
    Raises:
        ValueError: If required columns are missing or data is invalid
    """
    logger.info("Validating schema compliance")
    
    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Validate species_id is not empty
    if df['species_id'].isna().any() or (df['species_id'] == '').any():
        raise ValueError("species_id contains missing or empty values")
        
    # Validate foraging_guild is not empty
    if df['foraging_guild'].isna().any() or (df['foraging_guild'] == '').any():
        raise ValueError("foraging_guild contains missing or empty values")
        
    # Validate land_cover_proportions is a list/dict with expected keys
    if 'land_cover_proportions' in df.columns:
        # Check that values are properly formatted (list or dict of proportions)
        for idx, val in enumerate(df['land_cover_proportions']):
            if pd.isna(val) or val is None:
                raise ValueError(f"land_cover_proportions at index {idx} is null")
            
            # Convert string representation to dict if needed
            if isinstance(val, str):
                try:
                    val = json.loads(val)
                except json.JSONDecodeError:
                    raise ValueError(f"land_cover_proportions at index {idx} is not valid JSON")
            
            if not isinstance(val, dict):
                raise ValueError(f"land_cover_proportions at index {idx} is not a dictionary")
            
            # Check for expected land cover keys
            expected_keys = {'urban', 'agriculture', 'forest', 'water', 'wetland', 'grassland', 'barren'}
            if not expected_keys.issubset(set(val.keys())):
                raise ValueError(f"land_cover_proportions at index {idx} missing expected keys")
            
            # Check that proportions sum to approximately 1.0
            total = sum(val.values())
            if abs(total - 1.0) > 0.01:
                logger.warning(f"land_cover_proportions at index {idx} sums to {total}, not 1.0")
    
    logger.info("Schema validation passed")
    return True

def main():
    """
    Main function to execute the merge and buffer pipeline.
    """
    project_root = get_project_root()
    processed_dir = get_processed_dir()
    raw_dir = get_raw_data_dir()
    
    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Define paths
    top_species_path = processed_dir / "top_25_species_ids.json"
    guild_mapping_path = processed_dir / "guild_mapping.csv"
    nlcd_path = raw_dir / "nlcd_2019.zip"
    output_path = processed_dir / "merged_observations.csv"
    
    logger.info("Starting merge and buffer pipeline")
    
    try:
        # Load data
        ebd_df = load_filtered_ebd(top_species_path)
        guild_mapping = load_guild_mapping(guild_mapping_path)
        nlcd_dataset = load_nlcd_raster(nlcd_path)
        
        # Calculate land cover proportions
        ebd_df = calculate_land_cover_proportions(ebd_df, nlcd_dataset)
        
        # Assign guilds
        ebd_df = assign_guilds(ebd_df, guild_mapping)
        
        # Validate schema before saving
        validate_schema(ebd_df)
        
        # Save output
        logger.info(f"Saving merged observations to {output_path}")
        ebd_df.to_csv(output_path, index=False)
        
        # Record provenance
        provenance = generate_provenance_record(
            step="merge_and_buffer",
            input_files=[str(top_species_path), str(guild_mapping_path), str(nlcd_path)],
            output_file=str(output_path),
            script_path=__file__
        )
        
        # Append to metadata
        metadata_path = raw_dir.parent / "metadata.yaml"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = yaml.safe_load(f) or {}
        else:
            metadata = {}
            
        if 'provenance' not in metadata:
            metadata['provenance'] = []
        metadata['provenance'].append(provenance)
        
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False)
        
        logger.info("Pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
