"""
Z-Reward Dataset Ingestion Module.

This module handles the loading, alignment, and initial processing of the Z-Reward dataset.
It reads raw CSV data, aligns teacher logits, student scalars, and human annotations,
identifies the primary quality dimension, and outputs a summary of the ingestion process.

Dependencies:
    - pandas (for DataFrame manipulation)
    - json (for schema loading)
    - logging (for progress tracking)

Outputs:
    - Prints a summary of the dataset to stdout.
    - Does not write files directly (data is passed to features.py for processing).
"""

import argparse
import csv
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def setup_logging() -> logging.Logger:
    """
    Setup logging configuration for the ingestion process.
    Returns the configured logger.
    """
    return logger


def setup_directories(base_path: str) -> None:
    """
    Ensure required directory structure exists.
    Creates: data/raw, data/processed, results, code, tests relative to base_path.
    """
    dirs = [
        "data/raw",
        "data/processed",
        "results",
        "code",
        "tests"
    ]
    for d in dirs:
        path = os.path.join(base_path, d)
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"Created directory: {path}")
        else:
            logger.debug(f"Directory already exists: {path}")


def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA256 checksum of a file.
    Used for verifying data integrity if checksums are provided.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_dataset(output_path: str) -> str:
    """
    Download the Z-Reward dataset.
    This function assumes T037 has already run and the file exists at data/raw/zreward_dataset.csv.
    If the file does not exist, it attempts to fetch it using the datasets library or a direct URL.
    """
    import hashlib

    if os.path.exists(output_path):
        logger.info(f"Dataset found at {output_path}. Skipping download.")
        return output_path

    logger.info(f"Dataset not found at {output_path}. Attempting to download...")

    # Attempt 1: Use datasets library (as per T037 spec)
    try:
        from datasets import load_dataset
        logger.info("Attempting to fetch via datasets.load_dataset('zreward/zreward-v1')...")
        dataset = load_dataset('zreward/zreward-v1', split='train')
        # Convert to pandas and save
        df = dataset.to_pandas()
        df.to_csv(output_path, index=False)
        logger.info(f"Dataset saved to {output_path} via datasets library.")
        
        # Verify checksum if .checksums exists
        checksum_file = os.path.join(os.path.dirname(output_path), ".checksums")
        if os.path.exists(checksum_file):
            with open(checksum_file, 'r') as f:
                expected_checksum = f.read().strip()
            actual_checksum = calculate_sha256(output_path)
            if actual_checksum != expected_checksum:
                raise ValueError(f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}")
            logger.info("Checksum verified successfully.")
        
        return output_path
    except Exception as e:
        logger.warning(f"Datasets library fetch failed: {e}. Attempting direct URL fallback...")

    # Attempt 2: Direct URL fallback (as per T037 spec)
    try:
        import urllib.request
        url = "https://huggingface.co/datasets/zreward/zreward-v1/raw/main/data/train.parquet"
        temp_path = output_path.replace('.csv', '.parquet')
        logger.info(f"Downloading from {url} to {temp_path}...")
        urllib.request.urlretrieve(url, temp_path)
        
        # Convert parquet to csv
        import pyarrow.parquet as pq
        table = pq.read_table(temp_path)
        df = table.to_pandas()
        df.to_csv(output_path, index=False)
        os.remove(temp_path)
        
        logger.info(f"Dataset saved to {output_path} via direct URL.")
        return output_path
    except Exception as e:
        logger.error(f"Failed to download dataset via all methods: {e}")
        raise RuntimeError("Unable to download Z-Reward dataset. Please verify internet connection or dataset availability.")


def load_and_align_data(
    data_path: str,
    schema_path: str
) -> pd.DataFrame:
    """
    Load the Z-Reward dataset from CSV and align teacher logits, student scores, and human annotations.
    
    Args:
        data_path: Path to the raw CSV file.
        schema_path: Path to the dataset schema YAML file.
        
    Returns:
        A pandas DataFrame with aligned data.
    """
    logger.info(f"Loading data from {data_path}")
    
    # Load schema
    import yaml
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_columns = schema.get('required_columns', [])
    logger.info(f"Expected columns from schema: {required_columns}")
    
    # Load data
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    
    # Validate presence of required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")
    
    # Align data: Ensure consistent types and handle missing values
    # Standardize column names if necessary (case-insensitive match)
    df.columns = df.columns.str.strip()
    
    # Log missing data flags
    for col in required_columns:
        if df[col].isnull().any():
            null_count = df[col].isnull().sum()
            logger.warning(f"Column '{col}' has {null_count} missing values.")
        
    # Ensure teacher_logits is a list of floats if stored as string
    if 'teacher_logits' in df.columns:
        def parse_logits(val):
            if isinstance(val, list):
                return val
            try:
                # Handle string representation of list
                import ast
                return ast.literal_eval(val)
            except:
                return [0.0, 0.0, 0.0, 0.0] # Fallback for malformed data
        
        df['teacher_logits'] = df['teacher_logits'].apply(parse_logits)
    
    # Ensure human_annotations is a dict if stored as string
    if 'human_annotations' in df.columns:
        def parse_annotations(val):
            if isinstance(val, dict):
                return val
            try:
                import ast
                return ast.literal_eval(val)
            except:
                return {}
        
        df['human_annotations'] = df['human_annotations'].apply(parse_annotations)
    
    logger.info("Data alignment complete.")
    return df


def identify_primary_quality_dimension(df: pd.DataFrame) -> str:
    """
    Identify the primary quality dimension for the dataset.
    
    Rule: Use the value of the column `primary_dimension` if present in the dataset;
    otherwise, default to the first dimension in the schema (`Alignment`).
    
    Args:
        df: The aligned DataFrame.
        
    Returns:
        The string name of the primary dimension.
    """
    if 'primary_dimension' in df.columns:
        # Check if the column has a consistent value or if we should take the first non-null
        primary = df['primary_dimension'].dropna().iloc[0] if not df['primary_dimension'].dropna().empty else None
        if primary:
            logger.info(f"Primary dimension identified from column: {primary}")
            return str(primary)
    
    # Default fallback
    default_dim = "Alignment"
    logger.info(f"Primary dimension column not found or empty. Defaulting to: {default_dim}")
    return default_dim


def print_summary(df: pd.DataFrame, primary_dimension: str) -> None:
    """
    Print a summary of the ingested dataset.
    
    Args:
        df: The aligned DataFrame.
        primary_dimension: The identified primary dimension.
    """
    logger.info("=" * 60)
    logger.info("INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total samples: {len(df)}")
    logger.info(f"Primary Dimension: {primary_dimension}")
    
    # Dimension coverage
    if 'human_annotations' in df.columns:
        dims_found = set()
        for ann in df['human_annotations']:
            if isinstance(ann, dict):
                dims_found.update(ann.keys())
        logger.info(f"Human annotation dimensions found: {list(dims_found)}")
    
    # Missing data stats
    logger.info("Missing data stats:")
    for col in df.columns:
        if df[col].isnull().sum() > 0:
            logger.info(f"  - {col}: {df[col].isnull().sum()} missing")
    
    logger.info("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Ingest Z-Reward dataset")
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/raw/zreward_dataset.csv",
        help="Path to the raw dataset CSV file"
    )
    parser.add_argument(
        "--schema-path",
        type=str,
        default="contracts/dataset.schema.yaml",
        help="Path to the dataset schema YAML file"
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala",
        help="Base project path"
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for ingestion."""
    args = parse_args()
    setup_logging()
    
    # Setup directories
    setup_directories(args.base_path)
    
    # Download dataset if needed
    full_data_path = os.path.join(args.base_path, args.data_path)
    download_dataset(full_data_path)
    
    # Load and align
    full_schema_path = os.path.join(args.base_path, args.schema_path)
    df = load_and_align_data(full_data_path, full_schema_path)
    
    # Identify primary dimension
    primary_dim = identify_primary_quality_dimension(df)
    
    # Print summary
    print_summary(df, primary_dim)
    
    logger.info("Ingestion completed successfully.")


if __name__ == "__main__":
    main()
