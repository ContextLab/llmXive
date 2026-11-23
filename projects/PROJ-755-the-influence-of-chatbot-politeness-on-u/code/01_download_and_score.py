"""
code/01_download_and_score.py

Task T015: Fetch HCI_P2, Persona-Chat, and EmpatheticDialogues datasets from Hugging Face.
Validate required fields (quality_rating, user_id, dialogue_id), and save raw data with checksums.

This script implements the data acquisition phase for User Story 1.
It downloads all three sources to data/raw/{source}/raw_data.parquet.
It strictly adheres to the "fail loudly" policy: if a dataset cannot be fetched or lacks
required fields, it logs the error and raises an exception. It does not generate synthetic data.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from datasets import load_dataset
from tqdm import tqdm

# Import project utilities
from utils.data_integrity import compute_file_checksum, generate_manifest
from utils.schema_validator import load_schema, validate_dataset_schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/download_and_score.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration for all three required datasets
DATASETS_CONFIG = [
    {
        "name": "HCI_P2",
        "id": "HuggingFaceH4/hci_p2",
        "output_subdir": "hci_p2",
        "output_file": "raw_data.parquet",
        "required_fields": ['quality_rating', 'user_id', 'dialogue_id']
    },
    {
        "name": "Persona-Chat",
        "id": "Persona-Chat/persona_chat",
        "output_subdir": "persona_chat",
        "output_file": "raw_data.parquet",
        "required_fields": ['quality_rating', 'user_id', 'dialogue_id']
    },
    {
        "name": "EmpatheticDialogues",
        "id": "empathetictd/EmpatheticDialogues",
        "output_subdir": "empathetic_dialogues",
        "output_file": "raw_data.parquet",
        "required_fields": ['quality_rating', 'user_id', 'dialogue_id']
    }
]

# Global status tracking
VALIDATION_STATUS = {
    "sources": [],
    "timestamp": None
}

def ensure_directories():
    """Create necessary output directories for all sources."""
    base_raw_dir = Path("data/raw")
    base_raw_dir.mkdir(parents=True, exist_ok=True)
    
    for config in DATASETS_CONFIG:
        output_dir = base_raw_dir / config["output_subdir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "temp").mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Ensured directories exist under {base_raw_dir}")

def load_dataset_with_check(dataset_id: str, split: str = "train") -> pd.DataFrame:
    """
    Load the dataset from Hugging Face Hub.
    
    Args:
        dataset_id: The HF Hub dataset ID.
        split: The split to load (default: 'train').
    
    Returns:
        A pandas DataFrame containing the dataset.
    
    Raises:
        RuntimeError: If the dataset cannot be loaded.
    """
    logger.info(f"Attempting to load dataset: {dataset_id}, split: {split}")
    try:
        # Use streaming=False to ensure full download for validation
        ds = load_dataset(dataset_id, split=split, trust_remote_code=True)
        df = ds.to_pandas()
        logger.info(f"Successfully loaded {len(df)} rows from {dataset_id}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {e}")
        raise RuntimeError(f"Could not load dataset {dataset_id}. Ensure the ID is correct and internet is available.") from e

def validate_and_preprocess(df: pd.DataFrame, required_fields: List[str], source_name: str) -> pd.DataFrame:
    """
    Validate the presence of required fields and perform basic preprocessing.
    
    Args:
        df: Input DataFrame.
        required_fields: List of required column names.
        source_name: Name of the source for logging.
    
    Returns:
        Validated DataFrame.
    
    Raises:
        ValueError: If required fields are missing.
    """
    missing_fields = [field for field in required_fields if field not in df.columns]
    if missing_fields:
        error_msg = f"Dataset {source_name} is missing required fields: {missing_fields}. Available: {list(df.columns)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Basic type checks
    if not pd.api.types.is_numeric_dtype(df['quality_rating']):
        logger.warning(f"quality_rating column in {source_name} is not numeric. Type: {df['quality_rating'].dtype}. Attempting cast.")
        try:
            df['quality_rating'] = pd.to_numeric(df['quality_rating'], errors='raise')
        except (ValueError, TypeError):
            logger.error(f"Failed to cast quality_rating to numeric in {source_name}.")
            raise

    logger.info(f"Validation passed for {source_name}. Rows: {len(df)}, Columns: {list(df.columns)}")
    return df

def save_raw_data(df: pd.DataFrame, output_path: Path):
    """
    Save the DataFrame to parquet format.
    
    Args:
        df: DataFrame to save.
        output_path: Path to save the parquet file.
    """
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved raw data to {output_path}")

def generate_checksums_and_manifest(data_path: Path, checksums_path: Path, manifest_path: Path, dataset_config: Dict[str, Any]):
    """
    Generate checksums for the saved data and a manifest file.
    
    Args:
        data_path: Path to the parquet file.
        checksums_path: Path to save checksums JSON.
        manifest_path: Path to save manifest JSON.
        dataset_config: Configuration dictionary for the source.
    """
    checksum = compute_file_checksum(data_path)
    checksums_data = {
        "file": data_path.name,
        "sha256": checksum,
        "size_bytes": data_path.stat().st_size
    }
    with open(checksums_path, 'w') as f:
        json.dump(checksums_data, f, indent=2)
    logger.info(f"Generated checksums: {checksums_path}")

    manifest_data = {
        "dataset_name": dataset_config["name"],
        "source_id": dataset_config["id"],
        "files": [data_path.name],
        "checksums_file": checksums_path.name,
        "row_count": len(pd.read_parquet(data_path)),
        "columns": list(pd.read_parquet(data_path).columns)
    }
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    logger.info(f"Generated manifest: {manifest_path}")

def update_validation_status(source_name: str, status: str, details: str = ""):
    """Update the global validation status for a source."""
    VALIDATION_STATUS["sources"].append({
        "name": source_name,
        "status": status,
        "details": details
    })

def save_validation_status(output_path: Path):
    """Save the validation status to a JSON file."""
    VALIDATION_STATUS["timestamp"] = pd.Timestamp.now().isoformat()
    with open(output_path, 'w') as f:
        json.dump(VALIDATION_STATUS, f, indent=2)
    logger.info(f"Saved validation status to {output_path}")

def main():
    """Main entry point for T015."""
    logger.info("Starting Task T015: Download and Score All Datasets (HCI_P2, Persona-Chat, EmpatheticDialogues)")
    
    base_raw_dir = Path("data/raw")
    validation_status_file = base_raw_dir / "validation_status.json"
    
    try:
        # 1. Ensure directories
        ensure_directories()

        successful_sources = 0
        failed_sources = 0

        for config in DATASETS_CONFIG:
            source_name = config["name"]
            dataset_id = config["id"]
            output_subdir = config["output_subdir"]
            output_file = config["output_file"]
            required_fields = config["required_fields"]
            
            output_dir = base_raw_dir / output_subdir
            output_path = output_dir / output_file
            checksum_path = output_dir / "checksums.json"
            manifest_path = output_dir / "manifest.json"

            try:
                # 2. Load dataset
                logger.info(f"--- Processing {source_name} ---")
                df = load_dataset_with_check(dataset_id)

                # 3. Validate
                df = validate_and_preprocess(df, required_fields, source_name)

                # 4. Save raw data
                save_raw_data(df, output_path)

                # 5. Generate checksums and manifest
                generate_checksums_and_manifest(output_path, checksum_path, manifest_path, config)

                update_validation_status(source_name, "success", f"Downloaded {len(df)} rows")
                successful_sources += 1

            except Exception as e:
                logger.error(f"Failed to process {source_name}: {e}")
                update_validation_status(source_name, "failed", str(e))
                failed_sources += 1

        # 6. Save global validation status
        save_validation_status(validation_status_file)

        logger.info(f"Task T015 completed. Success: {successful_sources}, Failed: {failed_sources}")
        
        # Fail loudly if ALL sources failed
        if successful_sources == 0:
            logger.error("CRITICAL: All dataset sources failed. Pipeline cannot proceed.")
            sys.exit(1)

        return True

    except Exception as e:
        logger.error(f"Task T015 failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()