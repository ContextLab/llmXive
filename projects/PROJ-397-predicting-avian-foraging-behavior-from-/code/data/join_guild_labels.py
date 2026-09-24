"""
T039c: Join buffered land cover data with guild mapping to assign foraging guilds.

This script reads the buffered land cover data (produced by calculate_100m_buffers.py)
and joins it with the guild mapping (produced by generate_guild_mapping.py) to assign
a foraging guild to each observation. It ensures all required columns are present
and validates the join operation.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Set, Dict, Any
import pandas as pd

from utils.config import get_processed_dir, get_project_root
from utils.provenance import record_artifact_provenance, compute_file_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths
PROJECT_ROOT = get_project_root()
PROCESSED_DIR = get_processed_dir()

INPUT_FILE = PROCESSED_DIR / "buffered_observations.csv"
GUILD_MAPPING_FILE = PROCESSED_DIR / "guild_mapping.csv"
OUTPUT_FILE = PROCESSED_DIR / "joined_observations.csv"
LOG_FILE = PROCESSED_DIR / "guild_join_log.txt"

# Required columns for the buffered data
REQUIRED_BUFFERED_COLUMNS = [
    "species_id",
    "latitude",
    "longitude",
    "forest_prop_100m",
    "grassland_prop_100m",
    "wetland_prop_100m",
    "urban_prop_100m",
    "other_prop_100m"
]

# Required columns for the guild mapping
REQUIRED_GUILD_COLUMNS = [
    "species_id",
    "foraging_guild",
    "source_citation",
    "extraction_date"
]


def load_filtered_ebd() -> pd.DataFrame:
    """Load the buffered observations CSV."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")
    
    logger.info(f"Loading buffered observations from {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    
    if df.empty:
        raise ValueError(f"Input file {INPUT_FILE} is empty")
    
    return df


def load_guild_mapping() -> pd.DataFrame:
    """Load the guild mapping CSV."""
    if not GUILD_MAPPING_FILE.exists():
        raise FileNotFoundError(f"Guild mapping file not found: {GUILD_MAPPING_FILE}")
    
    logger.info(f"Loading guild mapping from {GUILD_MAPPING_FILE}")
    df = pd.read_csv(GUILD_MAPPING_FILE)
    
    if df.empty:
        raise ValueError(f"Guild mapping file {GUILD_MAPPING_FILE} is empty")
    
    return df


def validate_inputs(buffered_df: pd.DataFrame, guild_df: pd.DataFrame) -> None:
    """Validate that required columns are present in both DataFrames."""
    # Check buffered data columns
    missing_buffered = set(REQUIRED_BUFFERED_COLUMNS) - set(buffered_df.columns)
    if missing_buffered:
        raise ValueError(f"Missing required columns in buffered data: {missing_buffered}")
    
    # Check guild mapping columns
    missing_guild = set(REQUIRED_GUILD_COLUMNS) - set(guild_df.columns)
    if missing_guild:
        raise ValueError(f"Missing required columns in guild mapping: {missing_guild}")
    
    # Check for duplicate species_id in guild mapping (should be unique)
    if guild_df['species_id'].duplicated().any():
        raise ValueError("Duplicate species_id found in guild mapping. Each species should have exactly one guild.")
    
    logger.info("Input validation passed")


def join_guild_labels(buffered_df: pd.DataFrame, guild_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join buffered land cover data with guild mapping on species_id.
    
    This performs a left join to keep all buffered observations and assign
    the corresponding foraging guild. Observations for species without a
    guild mapping will be dropped and logged.
    """
    logger.info(f"Performing join on {len(buffered_df)} buffered observations with {len(guild_df)} guild mappings")
    
    # Select relevant columns from guild mapping for the join
    guild_select = guild_df[["species_id", "foraging_guild", "source_citation", "extraction_date"]]
    
    # Perform left join
    joined_df = buffered_df.merge(
        guild_select,
        on="species_id",
        how="left"
    )
    
    # Identify observations without a guild mapping
    null_guild_mask = joined_df["foraging_guild"].isna()
    missing_count = null_guild_mask.sum()
    
    if missing_count > 0:
        missing_species = joined_df.loc[null_guild_mask, "species_id"].unique()
        logger.warning(f"Found {missing_count} observations for {len(missing_species)} species without guild mapping")
        
        # Log missing species
        with open(LOG_FILE, 'w') as f:
            f.write(f"Species without guild mapping (dropped from output):\n")
            for sp in sorted(missing_species):
                count = (joined_df["species_id"] == sp).sum()
                f.write(f"  {sp}: {count} observations\n")
        
        # Drop rows without guild
        joined_df = joined_df.dropna(subset=["foraging_guild"])
        logger.info(f"Dropped {missing_count} observations. Remaining: {len(joined_df)}")
    else:
        with open(LOG_FILE, 'w') as f:
            f.write("All observations successfully joined with guild mapping.\n")
    
    # Verify no nulls remain in foraging_guild
    if joined_df["foraging_guild"].isna().any():
        raise ValueError("After dropping, there are still observations without foraging_guild")
    
    return joined_df


def save_joined_data(joined_df: pd.DataFrame) -> None:
    """Save the joined DataFrame to CSV."""
    if not PROCESSED_DIR.exists():
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving joined observations to {OUTPUT_FILE}")
    joined_df.to_csv(OUTPUT_FILE, index=False)
    
    # Compute and record hash
    file_hash = compute_file_hash(OUTPUT_FILE)
    logger.info(f"Output file hash: {file_hash}")


def record_provenance() -> None:
    """Record provenance information for this step."""
    record_artifact_provenance(
        step_name="join_guild_labels",
        input_files=[str(INPUT_FILE), str(GUILD_MAPPING_FILE)],
        output_files=[str(OUTPUT_FILE), str(LOG_FILE)],
        script_path=__file__
    )


def main() -> None:
    """Main entry point for the script."""
    try:
        # Load data
        buffered_df = load_filtered_ebd()
        guild_df = load_guild_mapping()
        
        # Validate inputs
        validate_inputs(buffered_df, guild_df)
        
        # Perform join
        joined_df = join_guild_labels(buffered_df, guild_df)
        
        # Save output
        save_joined_data(joined_df)
        
        # Record provenance
        record_provenance()
        
        logger.info(f"Successfully joined {len(joined_df)} observations with guild labels")
        logger.info(f"Unique species: {joined_df['species_id'].nunique()}")
        logger.info(f"Unique guilds: {joined_df['foraging_guild'].nunique()}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
