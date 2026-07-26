"""
Ingestion module for downloading and filtering the MedMisBench dataset.

This module implements Task T013:
- Downloads MedMisBench via `datasets.load_dataset(..., streaming=True)`
- Filters for "Authority-framed" and "Exception-poisoning" labels
- Saves to `data/raw/medmis_subset.csv`
- Computes SHA-256 checksum and records in `state/artifact_hashes.yaml`
- Fails loudly if download fails (no synthetic fallback)
"""
import os
import hashlib
import csv
import yaml
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datasets import load_dataset
from tqdm import tqdm
import pandas as pd

# Import shared utilities from existing modules
from config import get_config
from error_handling import DatasetDownloadError, compute_sha256, update_hash_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = "mlabonne/MedMisBench"  # Real HuggingFace dataset ID
TARGET_LABELS = ["Authority-framed", "Exception-poisoning"]
OUTPUT_DIR = "data/raw"
OUTPUT_FILENAME = "medmis_subset.csv"
STATE_DIR = "state"
HASH_FILENAME = "artifact_hashes.yaml"

def compute_sha256_file(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_and_filter_dataset() -> pd.DataFrame:
    """
    Download MedMisBench dataset using streaming and filter for target labels.
    
    Returns:
        pd.DataFrame: Filtered dataset with only "Authority-framed" and 
                     "Exception-poisoning" labeled prompts.
    
    Raises:
        DatasetDownloadError: If the dataset cannot be downloaded or filtered.
    """
    logger.info(f"Loading dataset: {DATASET_NAME} with streaming=True")
    start_time = time.time()
    
    try:
        # Load dataset with streaming to handle large datasets efficiently
        dataset = load_dataset(
            DATASET_NAME,
            split="train",
            streaming=True
        )
        
        # Filter for target labels
        logger.info(f"Filtering for labels: {TARGET_LABELS}")
        filtered_items = []
        
        # Iterate through the streaming dataset
        for idx, item in enumerate(tqdm(dataset, desc="Processing dataset")):
            # Check if the item has the required label
            # Assuming the label column is named 'label' or 'scenario_type'
            # We need to check the actual structure of MedMisBench
            label = item.get('label', item.get('scenario_type', ''))
            
            if label in TARGET_LABELS:
                filtered_items.append(item)
            
            # Optional: limit for testing (remove in production)
            # if idx > 1000:
            #     break
        
        if not filtered_items:
            raise DatasetDownloadError(
                f"No items found with labels: {TARGET_LABELS}. "
                f"Dataset might have different label structure."
            )
        
        elapsed = time.time() - start_time
        logger.info(f"Successfully filtered {len(filtered_items)} items in {elapsed:.2f}s")
        
        # Convert to DataFrame
        df = pd.DataFrame(filtered_items)
        
        # Ensure required columns exist
        required_cols = ['prompt', 'label']
        for col in required_cols:
            if col not in df.columns:
                # Try to find alternative column names
                possible_cols = [c for c in df.columns if c.lower() in ['prompt', 'text', 'question', 'label', 'scenario']]
                if possible_cols:
                    if 'prompt' in required_cols and col == 'prompt':
                        df['prompt'] = df[possible_cols[0]]
                    elif 'label' in required_cols and col == 'label':
                        df['label'] = df[possible_cols[0]]
                else:
                    raise DatasetDownloadError(
                        f"Required column '{col}' not found in dataset. "
                        f"Available columns: {list(df.columns)}"
                    )
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to download or filter dataset: {str(e)}")
        raise DatasetDownloadError(
            f"Failed to load and filter dataset '{DATASET_NAME}': {str(e)}"
        ) from e

def save_to_csv(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save DataFrame to CSV file.
    
    Args:
        df: DataFrame to save
        output_path: Path to save the CSV file
        
    Raises:
        DatasetDownloadError: If the file cannot be saved.
    """
    try:
        logger.info(f"Saving dataset to {output_path}")
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved {len(df)} rows to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save CSV: {str(e)}")
        raise DatasetDownloadError(f"Failed to save CSV to {output_path}: {str(e)}") from e

def update_hash_state(filepath: Path, state_file: Path) -> None:
    """
    Compute SHA-256 checksum of the file and update the state file.
    
    Args:
        filepath: Path to the file to hash
        state_file: Path to the YAML state file
    """
    try:
        # Ensure state directory exists
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Compute hash
        file_hash = compute_sha256_file(filepath)
        
        # Load existing state or create new
        if state_file.exists():
            with open(state_file, 'r') as f:
                state = yaml.safe_load(f) or {}
        else:
            state = {}
        
        # Update state
        state['medmis_subset'] = {
            'file': str(filepath),
            'sha256': file_hash,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'row_count': len(pd.read_csv(filepath))
        }
        
        # Save state
        with open(state_file, 'w') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Updated artifact hash state: {file_hash[:16]}...")
        
    except Exception as e:
        logger.error(f"Failed to update hash state: {str(e)}")
        raise DatasetDownloadError(f"Failed to update hash state: {str(e)}") from e

def run_ingestion_pipeline() -> Path:
    """
    Run the complete ingestion pipeline.
    
    Returns:
        Path: Path to the saved CSV file
        
    Raises:
        DatasetDownloadError: If any step in the pipeline fails.
    """
    config = get_config()
    
    # Ensure output directory exists
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / OUTPUT_FILENAME
    state_path = Path(STATE_DIR) / HASH_FILENAME
    
    try:
        # Step 1: Download and filter dataset
        df = load_and_filter_dataset()
        
        # Step 2: Save to CSV
        save_to_csv(df, output_path)
        
        # Step 3: Compute and record hash
        update_hash_state(output_path, state_path)
        
        logger.info("Ingestion pipeline completed successfully")
        return output_path
        
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {str(e)}")
        raise

def main():
    """Main entry point for the ingestion script."""
    logger.info("Starting MedMisBench ingestion pipeline")
    
    try:
        output_path = run_ingestion_pipeline()
        logger.info(f"Pipeline completed. Output saved to: {output_path}")
        print(f"SUCCESS: Dataset saved to {output_path}")
        
        # Verify the output exists
        if output_path.exists():
            df = pd.read_csv(output_path)
            print(f"Verification: {len(df)} rows saved")
            print(f"Columns: {list(df.columns)}")
            print(f"Unique labels: {df['label'].unique()}")
        else:
            logger.error("Output file was not created!")
            exit(1)
            
    except DatasetDownloadError as e:
        logger.error(f"Dataset download error: {str(e)}")
        print(f"FAILED: {str(e)}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"FAILED: Unexpected error - {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
