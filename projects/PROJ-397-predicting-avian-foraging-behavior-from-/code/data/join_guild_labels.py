"""
T039c: Join guild labels to buffered land cover data.

This script reads the filtered EBD data (which now contains land cover proportions
from T039b) and joins it with the guild mapping to assign a 'foraging_guild' to
each observation.

Input:
    - data/processed/filtered_ebd.csv (from T012.5c/T039b)
    - data/processed/guild_mapping.csv (from T008b)

Output:
    - data/processed/joined_observations.csv (Intermediate artifact for T039d)
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Set, Dict, Any

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_processed_dir, get_project_root
from utils.provenance import compute_file_hash, save_provenance_record, load_metadata_config, save_metadata_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_filtered_ebd(filepath: Path) -> Any:
    """Load the filtered EBD CSV."""
    try:
        import pandas as pd
        df = pd.read_csv(filepath)
        logger.info(f"Loaded filtered EBD: {len(df)} rows, columns: {list(df.columns)}")
        return df
    except Exception as e:
        logger.error(f"Failed to load filtered EBD from {filepath}: {e}")
        raise

def load_guild_mapping(filepath: Path) -> Any:
    """Load the guild mapping CSV."""
    try:
        import pandas as pd
        df = pd.read_csv(filepath)
        logger.info(f"Loaded guild mapping: {len(df)} rows, columns: {list(df.columns)}")
        return df
    except Exception as e:
        logger.error(f"Failed to load guild mapping from {filepath}: {e}")
        raise

def validate_inputs(ebd_df: Any, mapping_df: Any) -> None:
    """Validate that required columns exist in both dataframes."""
    required_ebd_cols = {'species_id', 'latitude', 'longitude'}
    # T039b added land cover columns, but we just need species_id for the join
    
    required_mapping_cols = {'species_id', 'foraging_guild'}

    ebd_cols = set(ebd_df.columns)
    mapping_cols = set(mapping_df.columns)

    missing_ebd = required_ebd_cols - ebd_cols
    if missing_ebd:
        raise ValueError(f"Filtered EBD missing required columns: {missing_ebd}")

    missing_mapping = required_mapping_cols - mapping_cols
    if missing_mapping:
        raise ValueError(f"Guild mapping missing required columns: {missing_mapping}")

    logger.info("Input validation passed.")

def join_guild_labels(ebd_df: Any, mapping_df: Any) -> Any:
    """
    Perform a left join of EBD data with guild mapping on species_id.
    Ensures all required columns are present in the result.
    """
    # Ensure species_id is string for consistent joining
    ebd_df = ebd_df.copy()
    mapping_df = mapping_df.copy()
    
    ebd_df['species_id'] = ebd_df['species_id'].astype(str)
    mapping_df['species_id'] = mapping_df['species_id'].astype(str)

    # Merge
    joined_df = ebd_df.merge(
        mapping_df[['species_id', 'foraging_guild']],
        on='species_id',
        how='left'
    )

    # Validate join result
    null_guilds = joined_df['foraging_guild'].isna().sum()
    if null_guilds > 0:
        logger.warning(f"Found {null_guilds} observations with missing guild labels. "
                     "These will be included but flagged in downstream steps if necessary.")
    
    required_result_cols = {'species_id', 'foraging_guild', 'latitude', 'longitude'}
    result_cols = set(joined_df.columns)
    missing_result = required_result_cols - result_cols
    if missing_result:
        raise ValueError(f"Result dataframe missing required columns after join: {missing_result}")

    logger.info(f"Joined data successfully. Result shape: {joined_df.shape}")
    return joined_df

def save_joined_data(df: Any, filepath: Path) -> str:
    """Save the joined dataframe to CSV and return the file hash."""
    df.to_csv(filepath, index=False)
    file_hash = compute_file_hash(filepath)
    logger.info(f"Saved joined observations to {filepath} (hash: {file_hash})")
    return file_hash

def record_provenance(input_files: List[Path], output_file: Path, file_hash: str) -> None:
    """Record provenance in metadata.yaml."""
    metadata_path = get_project_root() / "data" / "metadata.yaml"
    metadata = load_metadata_config(metadata_path)
    
    if 'steps' not in metadata:
        metadata['steps'] = []
    
    step_record = {
        "step_id": "T039c",
        "step_name": "join_guild_labels",
        "input_files": [str(f) for f in input_files],
        "output_file": str(output_file),
        "output_hash": file_hash,
        "timestamp": str(Path(__file__).stat().st_mtime) # Simplified timestamp
    }
    
    metadata['steps'].append(step_record)
    save_metadata_config(metadata, metadata_path)
    logger.info("Provenance recorded in metadata.yaml")

def main():
    """Main entry point for T039c."""
    processed_dir = get_processed_dir()
    
    input_ebd = processed_dir / "filtered_ebd.csv"
    input_mapping = processed_dir / "guild_mapping.csv"
    output_file = processed_dir / "joined_observations.csv"

    if not input_ebd.exists():
        raise FileNotFoundError(f"Input file not found: {input_ebd}. "
                              "Ensure T012.5c/T039b has completed.")
    if not input_mapping.exists():
        raise FileNotFoundError(f"Input file not found: {input_mapping}. "
                              "Ensure T008b has completed.")

    logger.info(f"Starting T039c: Joining guild labels for {input_ebd}")

    # Load
    ebd_df = load_filtered_ebd(input_ebd)
    mapping_df = load_guild_mapping(input_mapping)

    # Validate
    validate_inputs(ebd_df, mapping_df)

    # Join
    joined_df = join_guild_labels(ebd_df, mapping_df)

    # Save
    file_hash = save_joined_data(joined_df, output_file)

    # Record Provenance
    record_provenance([input_ebd, input_mapping], output_file, file_hash)

    logger.info("T039c completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())