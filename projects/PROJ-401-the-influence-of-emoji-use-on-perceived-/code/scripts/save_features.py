"""
Task T014: Save processed features to data/processed/features.csv with checksums.

This script assumes T012 (data loading) and T013 (joining) have completed successfully.
It reads the joined dataframe from the state directory, saves it to data/processed/features.csv,
computes a checksum, and records the metadata in state/features_metadata.yaml.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

# Add project root to path if not already present
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.io import compute_file_checksum, ensure_directory, set_global_seed
from src.data.pipeline_join import join_raw_with_features

logger = logging.getLogger(__name__)

# Configuration
SEED = 42
INPUT_STATE_FILE = "data/processed/joined_data.parquet"  # Assumed output of T013
OUTPUT_CSV = "data/processed/features.csv"
METADATA_FILE = "state/features_metadata.yaml"

def load_joined_data(input_path: Path) -> pd.DataFrame:
    """Load the joined dataframe from the previous pipeline step."""
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T013 (pipeline_join) has completed successfully."
        )
    
    logger.info(f"Loading joined data from {input_path}")
    if input_path.suffix == ".parquet":
        return pd.read_parquet(input_path)
    elif input_path.suffix == ".csv":
        return pd.read_csv(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")

def save_features(df: pd.DataFrame, output_path: Path) -> None:
    """Save the dataframe to CSV with proper formatting."""
    ensure_directory(output_path)
    logger.info(f"Saving features to {output_path}")
    
    # Ensure deterministic output for reproducibility
    # Sort by message_id if available, otherwise by index
    if 'message_id' in df.columns:
        df = df.sort_values('message_id').reset_index(drop=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} records to {output_path}")

def save_metadata(output_path: Path, checksum: str, record_count: int) -> None:
    """Save metadata including checksum and record count."""
    metadata = {
        "task_id": "T014",
        "output_file": str(output_path.relative_to(project_root)),
        "checksum_algorithm": "sha256",
        "checksum": checksum,
        "record_count": record_count,
        "seed": SEED
    }
    
    metadata_path = Path(METADATA_FILE)
    ensure_directory(metadata_path)
    
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)
    
    logger.info(f"Saved metadata to {metadata_path}")

def main() -> int:
    """Main entry point for T014."""
    set_global_seed(SEED)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        input_path = project_root / INPUT_STATE_FILE
        output_path = project_root / OUTPUT_CSV
        
        # Load data from previous step
        df = load_joined_data(input_path)
        
        # Validate expected columns exist (basic sanity check)
        expected_cols = ['message_id', 'text', 'human_intensity_score']
        missing_cols = [c for c in expected_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in joined data: {missing_cols}")
        
        logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
        
        # Save to CSV
        save_features(df, output_path)
        
        # Compute checksum
        checksum = compute_file_checksum(output_path)
        logger.info(f"Computed checksum: {checksum}")
        
        # Save metadata
        save_metadata(output_path, checksum, len(df))
        
        logger.info("T014 completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        logger.error("T014 failed. Ensure T013 (pipeline_join) has run successfully.")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during T014: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
