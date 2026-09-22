"""
Load and validate inputs for the buffer calculation and merging step.

This script reads:
  - data/processed/filtered_ebd.csv
  - data/raw/nlcd_2019.zip
  - data/processed/guild_mapping.csv

It validates that:
  - All files exist and are non-empty.
  - The EBD CSV has required columns: species_id, latitude, longitude.
  - The NLCD archive is a valid zip file containing raster data.
  - The guild mapping CSV has required columns: species_id, foraging_guild.

Raises ValueError if any input is malformed or missing.
"""
import os
import sys
import logging
import zipfile
from pathlib import Path
from typing import Tuple, List, Set, Dict, Any
import pandas as pd

# Add project root to path if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_processed_dir, get_raw_data_dir, get_project_root, get_logger

logger = get_logger(__name__)

# Required columns for filtered_ebd.csv
REQUIRED_EBD_COLUMNS = {'species_id', 'latitude', 'longitude'}

# Required columns for guild_mapping.csv
REQUIRED_GUILD_COLUMNS = {'species_id', 'foraging_guild'}

def load_filtered_ebd() -> pd.DataFrame:
    """
    Load the filtered eBird data from CSV.
    
    Returns:
        pd.DataFrame: The filtered eBird observations.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    processed_dir = get_processed_dir()
    file_path = processed_dir / "filtered_ebd.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Filtered EBD file not found: {file_path}")
    
    logger.info(f"Loading filtered EBD from {file_path}")
    df = pd.read_csv(file_path)
    
    missing_cols = REQUIRED_EBD_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in filtered_ebd.csv: {missing_cols}")
    
    # Validate coordinate ranges
    if df['latitude'].isnull().any() or df['longitude'].isnull().any():
        raise ValueError("Filtered EBD contains null coordinates.")
    
    if not (-90 <= df['latitude'].min() <= 90) or not (-90 <= df['latitude'].max() <= 90):
        raise ValueError("Latitude values out of range [-90, 90].")
        
    if not (-180 <= df['longitude'].min() <= 180) or not (-180 <= df['longitude'].max() <= 180):
        raise ValueError("Longitude values out of range [-180, 180].")
    
    logger.info(f"Loaded {len(df)} records from filtered_ebd.csv")
    return df

def load_guild_mapping() -> pd.DataFrame:
    """
    Load the guild mapping from CSV.
    
    Returns:
        pd.DataFrame: The guild mapping table.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    processed_dir = get_processed_dir()
    file_path = processed_dir / "guild_mapping.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Guild mapping file not found: {file_path}")
    
    logger.info(f"Loading guild mapping from {file_path}")
    df = pd.read_csv(file_path)
    
    missing_cols = REQUIRED_GUILD_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns in guild_mapping.csv: {missing_cols}")
    
    if df['species_id'].isnull().any():
        raise ValueError("Guild mapping contains null species_id values.")
    
    if df['foraging_guild'].isnull().any():
        raise ValueError("Guild mapping contains null foraging_guild values.")
    
    logger.info(f"Loaded guild mapping with {len(df)} species")
    return df

def validate_nlcd_archive() -> Tuple[Path, zipfile.ZipFile]:
    """
    Validate the NLCD 2019 zip archive.
    
    Returns:
        Tuple[Path, zipfile.ZipFile]: The path to the archive and an open ZipFile object.
        
    Raises:
        FileNotFoundError: If the archive does not exist.
        ValueError: If the archive is invalid or empty.
    """
    raw_dir = get_raw_data_dir()
    file_path = raw_dir / "nlcd_2019.zip"
    
    if not file_path.exists():
        raise FileNotFoundError(f"NLCD archive not found: {file_path}")
    
    logger.info(f"Validating NLCD archive: {file_path}")
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            bad_file = zf.testzip()
            if bad_file:
                raise ValueError(f"Corrupt file in archive: {bad_file}")
            
            namelist = zf.namelist()
            if not namelist:
                raise ValueError("NLCD archive is empty.")
            
            # Check for raster files (common extensions)
            raster_files = [f for f in namelist if f.endswith(('.tif', '.tiff', '.img', '.hdf'))]
            if not raster_files:
                raise ValueError(f"No raster files found in NLCD archive. Found: {namelist[:5]}...")
            
            logger.info(f"NLCD archive validated. Contains {len(raster_files)} raster files.")
            # Return a new open file handle for the caller
            return file_path, zipfile.ZipFile(file_path, 'r')
            
    except zipfile.BadZipFile:
        raise ValueError(f"NLCD archive is not a valid zip file: {file_path}")

def validate_inputs(ebd_df: pd.DataFrame, guild_df: pd.DataFrame, nlcd_path: Path) -> bool:
    """
    Perform cross-validation between inputs.
    
    Checks:
      - At least one species in EBD exists in guild mapping.
      - NLCD archive is valid (already checked in validate_nlcd_archive).
      
    Returns:
        bool: True if validation passes.
        
    Raises:
        ValueError: If cross-validation fails.
    """
    ebd_species = set(ebd_df['species_id'].unique())
    guild_species = set(guild_df['species_id'].unique())
    
    intersection = ebd_species.intersection(guild_species)
    
    if not intersection:
        raise ValueError(
            f"No common species between filtered EBD ({len(ebd_species)} species) "
            f"and guild mapping ({len(guild_species)} species)."
        )
    
    logger.info(f"Cross-validation passed. {len(intersection)} species have both observations and guild labels.")
    return True

def main():
    """Main entry point for the validation script."""
    try:
        # Load and validate individual inputs
        ebd_df = load_filtered_ebd()
        guild_df = load_guild_mapping()
        nlcd_path, nlcd_zip = validate_nlcd_archive()
        
        # Perform cross-validation
        validate_inputs(ebd_df, guild_df, nlcd_path)
        
        logger.info("All inputs validated successfully.")
        
        # Close the zip file handle opened in validation
        nlcd_zip.close()
        
        return 0
        
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Validation failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
