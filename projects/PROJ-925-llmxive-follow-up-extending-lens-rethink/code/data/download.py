import hashlib
import json
import os
import sys
import logging
import random
from pathlib import Path
from typing import Iterator, Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field, asdict
import yaml

# Local imports
from utils.errors import DataSchemaError
from utils.logging import get_logger
from config import get_paths

logger = get_logger(__name__)

@dataclass
class DownloadState:
    raw_data_path: Optional[str] = None
    checksums: Dict[str, str] = field(default_factory=dict)
    total_rows: int = 0
    sampled_rows: int = 0
    sampling_seed: Optional[int] = None
    sampling_fraction: Optional[float] = None
    strata_columns: List[str] = field(default_factory=list)
    status: str = "not_started"  # not_started, downloaded, sampled, failed
    error_message: Optional[str] = None

def load_project_state() -> DownloadState:
    """Load the project state from the YAML file."""
    paths = get_paths()
    state_file = paths["state_file"]
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)
            return DownloadState(**data)
    return DownloadState()

def save_project_state(state: DownloadState) -> None:
    """Save the project state to the YAML file."""
    paths = get_paths()
    state_file = paths["state_file"]
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, 'w') as f:
        yaml.dump(asdict(state), f, default_flow_style=False)

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_row(row: Dict[str, Any]) -> bool:
    """Validate a row from the dataset."""
    if not row.get('caption') or not row.get('image_path'):
        return False
    if not row['caption'].strip():
        return False
    return True

def stream_pick_a_pic_dataset() -> Iterator[Dict[str, Any]]:
    """
    Stream the pick-a-pic dataset from Hugging Face.
    Validates the presence of 'human_rating' and 'caption' columns.
    Fails loudly if the dataset is unavailable or schema is missing.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise DataSchemaError("Missing required dataset or column: pick-a-pic/human_rating. 'datasets' package not installed.")

    try:
        # Load in streaming mode to handle large datasets
        dataset = load_dataset("pick-a-pic", split="train", streaming=True)
        
        # Validate schema: check for required columns
        if 'human_rating' not in dataset.column_names:
            raise DataSchemaError("Missing required dataset or column: pick-a-pic/human_rating")
        if 'caption' not in dataset.column_names:
            raise DataSchemaError("Missing required dataset or column: pick-a-pic/caption")
        
        logger.info(f"Dataset loaded successfully. Columns: {dataset.column_names}")
        
        for row in dataset:
            yield row
            
    except Exception as e:
        # Log the specific error and re-raise as DataSchemaError to fail loudly
        logger.error(f"Failed to load pick-a-pic dataset: {e}")
        raise DataSchemaError(f"Missing required dataset or column: pick-a-pic/human_rating. Reason: {str(e)}")

def download_and_checksum(state: DownloadState) -> None:
    """
    Download the dataset in streaming mode, validate rows, and compute checksums.
    This function writes the raw data to disk and updates the state.
    """
    paths = get_paths()
    raw_data_dir = paths["raw_data_dir"]
    os.makedirs(raw_data_dir, exist_ok=True)
    
    output_file = os.path.join(raw_data_dir, "pick_a_pic_raw.jsonl")
    state.raw_data_path = output_file
    state.status = "downloading"
    save_project_state(state)
    
    logger.info(f"Starting download to {output_file}")
    
    total_rows = 0
    valid_rows = 0
    checksum_data = []
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for row in stream_pick_a_pic_dataset():
                if validate_row(row):
                    json_line = json.dumps(row, ensure_ascii=False)
                    f.write(json_line + '\n')
                    valid_rows += 1
                    checksum_data.append(json_line)
                else:
                    logger.debug(f"Skipping invalid row")
                total_rows += 1
                
        state.total_rows = valid_rows
        state.status = "downloaded"
        
        # Compute checksum for the file
        file_hash = compute_sha256(output_file)
        state.checksums[os.path.basename(output_file)] = file_hash
        
        logger.info(f"Download complete. Total rows: {total_rows}, Valid rows: {valid_rows}")
        
    except DataSchemaError as e:
        state.status = "failed"
        state.error_message = str(e)
        logger.critical(f"Download failed: {e}")
        raise
    except Exception as e:
        state.status = "failed"
        state.error_message = str(e)
        logger.critical(f"Download failed with unexpected error: {e}")
        raise

def apply_stratified_sampling(
    state: DownloadState, 
    strata_columns: List[str], 
    sample_fraction: float, 
    seed: int
) -> None:
    """
    Apply stratified random sampling to the downloaded dataset.
    
    Args:
        state: Current download state.
        strata_columns: List of column names to use for stratification.
        sample_fraction: Fraction of data to sample (0.0 to 1.0).
        seed: Random seed for reproducibility.
        
    Raises:
        DataSchemaError: If sampling fails due to missing columns or invalid parameters.
    """
    paths = get_paths()
    raw_data_file = state.raw_data_path
    
    if not raw_data_file or not os.path.exists(raw_data_file):
        raise DataSchemaError("Raw data file not found. Run download_and_checksum first.")
    
    if not (0.0 < sample_fraction <= 1.0):
        raise DataSchemaError(f"Invalid sample_fraction: {sample_fraction}. Must be between 0 and 1 (exclusive of 0).")
        
    if not strata_columns:
        # If no strata columns provided, perform simple random sampling
        logger.warning("No strata columns provided. Performing simple random sampling.")
        strata_columns = []
    
    try:
        from datasets import Dataset
        import pandas as pd
    except ImportError:
        raise DataSchemaError("Required packages 'datasets' or 'pandas' not installed for sampling.")

    logger.info(f"Applying stratified sampling with seed={seed}, fraction={sample_fraction}, strata={strata_columns}")
    
    # Load data into memory for sampling (assuming it fits in memory after initial filter)
    # If the file is too large, we would need to stream and sample, but for now we load.
    data_list = []
    with open(raw_data_file, 'r', encoding='utf-8') as f:
        for line in f:
            data_list.append(json.loads(line))
    
    if not data_list:
        raise DataSchemaError("No data found in raw file.")
        
    df = pd.DataFrame(data_list)
    
    # Validate strata columns exist
    missing_cols = [col for col in strata_columns if col not in df.columns]
    if missing_cols:
        raise DataSchemaError(f"Strata columns not found in dataset: {missing_cols}")
    
    # Set seed
    random.seed(seed)
    np.random.seed(seed)
    
    sampled_df = None
    
    if strata_columns:
        # Perform stratified sampling
        logger.info(f"Performing stratified sampling on columns: {strata_columns}")
        # Ensure strata columns are treated as strings for grouping
        for col in strata_columns:
            df[col] = df[col].astype(str)
        
        try:
            sampled_df = df.groupby(strata_columns, group_keys=False).apply(
                lambda x: x.sample(frac=sample_fraction, random_state=seed)
            )
        except Exception as e:
            raise DataSchemaError(f"Stratified sampling failed: {e}")
    else:
        # Simple random sampling
        logger.info("Performing simple random sampling.")
        sampled_df = df.sample(frac=sample_fraction, random_state=seed)
    
    # Update state
    state.sampled_rows = len(sampled_df)
    state.sampling_seed = seed
    state.sampling_fraction = sample_fraction
    state.strata_columns = strata_columns
    state.status = "sampled"
    
    # Save sampled data
    sampled_file = os.path.join(paths["processed_data_dir"], "pick_a_pic_sampled.jsonl")
    os.makedirs(paths["processed_data_dir"], exist_ok=True)
    
    with open(sampled_file, 'w', encoding='utf-8') as f:
        for _, row in sampled_df.iterrows():
            f.write(json.dumps(row.to_dict(), ensure_ascii=False) + '\n')
    
    logger.info(f"Sampled data saved to {sampled_file}. Rows: {state.sampled_rows}")
    
    # Update checksums for sampled file
    sampled_hash = compute_sha256(sampled_file)
    state.checksums["pick_a_pic_sampled.jsonl"] = sampled_hash

def update_state_with_checksum(state: DownloadState, filename: str, file_path: str) -> None:
    """Update the state with a new checksum."""
    state.checksums[filename] = compute_sha256(file_path)

def main():
    """
    Main entry point for the download and sampling pipeline.
    Usage: python code/data/download.py --sample --strata-columns column1,column2 --fraction 0.1 --seed 42
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Download and sample pick-a-pic dataset")
    parser.add_argument("--sample", action="store_true", help="Enable stratified sampling")
    parser.add_argument("--strata-columns", type=str, default="", help="Comma-separated list of columns for stratification")
    parser.add_argument("--fraction", type=float, default=1.0, help="Fraction of data to sample")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling")
    
    args = parser.parse_args()
    
    state = load_project_state()
    
    try:
        # Step 1: Download and validate
        download_and_checksum(state)
        
        # Step 2: Apply sampling if requested
        if args.sample:
            strata_cols = [col.strip() for col in args.strata_columns.split(',') if col.strip()]
            apply_stratified_sampling(state, strata_cols, args.fraction, args.seed)
        
        save_project_state(state)
        logger.info("Pipeline completed successfully.")
        
    except DataSchemaError as e:
        logger.critical(f"Pipeline failed: {e}")
        save_project_state(state)
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline failed with unexpected error: {e}")
        state.status = "failed"
        state.error_message = str(e)
        save_project_state(state)
        sys.exit(1)

if __name__ == "__main__":
    main()