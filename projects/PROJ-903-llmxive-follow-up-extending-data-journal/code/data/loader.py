import os
import json
import hashlib
import logging
import traceback
import sys
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Iterator

import pandas as pd
from datasets import load_dataset, DatasetDict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom Exceptions
class DataFetchError(Exception):
    """Raised when dataset fetching fails."""
    pass

class RAMExceededError(Exception):
    """Raised when dataset estimation exceeds memory limits."""
    pass

class LowPowerError(Exception):
    """Raised when sample size is too small (n < 30)."""
    pass

class LowNumericColumnsError(Exception):
    """Raised when fewer than 5 numeric columns are found."""
    pass

# --- Utility Functions ---

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def estimate_memory_usage(df: pd.DataFrame) -> float:
    """Estimate memory usage of a DataFrame in MB."""
    return df.memory_usage(deep=True).sum() / (1024 * 1024)

def validate_numeric_columns(df: pd.DataFrame, min_cols: int = 5) -> Tuple[bool, List[str]]:
    """
    Validate that the DataFrame has at least `min_cols` numeric columns.
    Returns (is_valid, list_of_numeric_columns).
    """
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    is_valid = len(numeric_cols) >= min_cols
    return is_valid, numeric_cols

def check_sample_size(df: pd.DataFrame, min_rows: int = 30) -> bool:
    """Check if the dataset has at least `min_rows`."""
    return len(df) >= min_rows

# --- Fetching Logic ---

def fetch_dataset_from_hf(dataset_name: str, split: str = "train", streaming: bool = False) -> pd.DataFrame:
    """
    Fetch a dataset from Hugging Face.
    If streaming is True, it iterates in chunks to avoid loading full data into memory immediately.
    """
    logger.info(f"Fetching dataset from HF: {dataset_name}, split: {split}, streaming: {streaming}")
    try:
        if streaming:
            # For streaming, we load as a generator and convert to DF in chunks if needed
            # or just load the first part if we are validating structure.
            # For the loader's primary job (fetching raw file), we might need to download the file.
            # However, the task asks to fetch datasets.
            # If streaming=True, we assume we are processing stats online later, but here we need the raw file or a sample.
            # To strictly follow "fail loudly" and "streaming", we will attempt to load the dataset object.
            # If the dataset is huge, we might not want to materialize it here if not needed for validation.
            # But for the "fetch raw file" step, we usually need the file.
            # Let's assume for T005a we are fetching the data for processing.
            # If streaming is requested, we return a generator or a sample for validation.
            ds = load_dataset(dataset_name, split=split, streaming=True)
            # If we need a dataframe for validation, we take a sample.
            # But the task says "fetch datasets... validate numeric columns".
            # We will fetch a sample to validate, then the processor handles the rest.
            # Actually, T005c handles streaming logic for stats. T005a is about fetching and validating structure.
            # We will fetch a small sample to validate structure, then save the raw file if possible.
            # But HF datasets don't always save to a single CSV file easily without downloading shards.
            # Let's try to get the first chunk to validate.
            sample_df = next(iter(ds))
            if not isinstance(sample_df, pd.DataFrame):
                sample_df = pd.DataFrame(sample_df)
            return sample_df
        else:
            ds = load_dataset(dataset_name, split=split)
            df = ds.to_pandas()
            return df
    except Exception as e:
        logger.error(f"Failed to load HF dataset {dataset_name}: {e}")
        raise DataFetchError(f"Failed to load HF dataset {dataset_name}: {e}")

def fetch_dataset_from_url(url: str, output_path: str) -> str:
    """
    Fetch a dataset from a direct URL and save it to output_path.
    Returns the path to the saved file.
    """
    logger.info(f"Fetching dataset from URL: {url}")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Determine file extension
        ext = os.path.splitext(url.split('?')[0])[-1]
        if not ext:
            ext = '.csv' # Default to CSV if unknown
        
        final_path = f"{output_path}{ext}"
        
        with open(final_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Dataset saved to {final_path}")
        return final_path
    except Exception as e:
        logger.error(f"Failed to download dataset from {url}: {e}")
        raise DataFetchError(f"Failed to download dataset from {url}: {e}")

def fetch_and_save_dataset(dataset_name: str, output_dir: str, source_type: str = "hf") -> str:
    """
    Main entry point to fetch a dataset and save it to disk.
    Returns the path to the saved file.
    """
    logger.info(f"Starting fetch for dataset: {dataset_name}")
    output_path = os.path.join(output_dir, dataset_name)
    
    if source_type == "hf":
        # For HF, we might not have a single file to save in the traditional sense unless we download shards.
        # However, T005a requires "checksum raw files".
        # We will attempt to load the dataset, convert to CSV, and save it as the "raw" file for the pipeline.
        # This satisfies the "fetch" and "save" requirement.
        try:
            ds = load_dataset(dataset_name, split="train")
            df = ds.to_pandas()
            file_path = os.path.join(output_path + ".csv")
            df.to_csv(file_path, index=False)
            logger.info(f"Saved HF dataset to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to process HF dataset {dataset_name} for saving: {e}")
            raise DataFetchError(f"Failed to process HF dataset {dataset_name}: {e}")
    
    elif source_type == "url":
        # Assume dataset_name is the URL
        return fetch_dataset_from_url(dataset_name, output_path)
    
    else:
        raise DataFetchError(f"Unknown source type: {source_type}")

def process_and_validate(file_path: str) -> pd.DataFrame:
    """
    Load a CSV file, validate numeric columns and sample size.
    Raises exceptions if validation fails.
    """
    logger.info(f"Validating dataset: {file_path}")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to read CSV {file_path}: {e}")
        raise DataFetchError(f"Failed to read CSV {file_path}: {e}")

    # Validate numeric columns
    is_valid_num, num_cols = validate_numeric_columns(df)
    if not is_valid_num:
        logger.error(f"Dataset {file_path} has {len(num_cols)} numeric columns, requires >= 5.")
        raise LowNumericColumnsError(f"Insufficient numeric columns in {file_path}: {len(num_cols)}")

    # Validate sample size
    if not check_sample_size(df):
        logger.warning(f"Dataset {file_path} has {len(df)} rows (< 30). Setting low_power_flag.")
        # We raise LowPowerError here to be caught by the pipeline to set the flag,
        # but the task says "skip downstream counterfactual generation".
        # The loader raises, main catches, sets flag, continues.
        raise LowPowerError(f"Sample size too small in {file_path}: {len(df)}")

    return df

def load_all_datasets(registry_path: str, data_dir: str) -> Dict[str, pd.DataFrame]:
    """
    Load all datasets from the registry.
    Returns a dict of {dataset_name: df}.
    """
    # Placeholder for registry loading logic
    # In a real scenario, this would parse data/dataset_registry.yaml
    # and call fetch_and_save_dataset for each.
    # For this task, we assume the registry exists and we iterate it.
    # Since we can't import the registry logic directly without circular deps or missing files,
    # we implement a minimal registry loader here or assume the caller passes entries.
    # However, T004b created validate_registry.py which likely reads the registry.
    # Let's assume we have a simple list of datasets for now or read the yaml.
    import yaml
    with open(registry_path, 'r') as f:
        registry = yaml.safe_load(f)
    
    datasets = {}
    for entry in registry.get('datasets', []):
        name = entry.get('name')
        source = entry.get('source') # e.g., 'hf' or 'url'
        url_or_id = entry.get('url') or entry.get('dataset_id')
        
        if not name:
            continue
        
        try:
            # Fetch and save
            file_path = fetch_and_save_dataset(url_or_id, data_dir, source_type=source)
            
            # Validate
            df = process_and_validate(file_path)
            
            # Checksum
            checksum = compute_sha256(file_path)
            logger.info(f"Dataset {name} loaded and validated. Checksum: {checksum}")
            
            datasets[name] = df
        except LowPowerError:
            # Re-raise to be caught by main.py to set flag
            raise
        except DataFetchError:
            # Re-raise to be caught by main.py to skip
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing {name}: {e}")
            raise DataFetchError(f"Unexpected error processing {name}: {e}")
    
    return datasets

def main():
    """
    CLI entry point for the loader.
    Usage: python code/data/loader.py --dataset <name> --mode <download|validate>
    """
    import argparse
    parser = argparse.ArgumentParser(description="Data Loader for llmXive")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset name or ID")
    parser.add_argument("--mode", type=str, choices=["download", "validate", "full"], default="full", help="Operation mode")
    parser.add_argument("--output_dir", type=str, default="data/raw", help="Output directory for raw files")
    parser.add_argument("--registry", type=str, default="data/dataset_registry.yaml", help="Path to dataset registry")
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        if args.mode == "download":
            file_path = fetch_and_save_dataset(args.dataset, args.output_dir)
            logger.info(f"Download complete: {file_path}")
        elif args.mode == "validate":
            # Assume file exists or download first
            if not os.path.exists(args.dataset):
                file_path = fetch_and_save_dataset(args.dataset, args.output_dir)
            else:
                file_path = args.dataset
            df = process_and_validate(file_path)
            logger.info(f"Validation complete for {file_path}")
        elif args.mode == "full":
            # Load from registry
            datasets = load_all_datasets(args.registry, args.output_dir)
            logger.info(f"Loaded {len(datasets)} datasets successfully.")
            
    except DataFetchError as e:
        logger.error(f"DataFetchError: {e}")
        raise
    except LowPowerError as e:
        logger.warning(f"LowPowerError: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
