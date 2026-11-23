import json
import logging
import os
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
import time

import pandas as pd
from datasets import load_dataset

from code.config import CONFIG, set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass

def _compute_file_md5(filepath: Path) -> str:
    """Compute MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def _download_dataset_to_csv(
    dataset_id: str,
    split: str,
    revision: str,
    output_path: Path,
    sample_size: Optional[int] = None
) -> Path:
    """
    Download dataset from HuggingFace and save as CSV.
    
    Args:
        dataset_id: HuggingFace dataset identifier
        split: Dataset split to load
        revision: Dataset revision
        output_path: Path to save the CSV file
        sample_size: If provided, limit the dataset to this many rows
    
    Returns:
        Path to the saved CSV file
    """
    logger.info(f"Downloading dataset: {dataset_id} (split={split}, revision={revision})")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if dataset is already downloaded
    if output_path.exists():
        logger.info(f"Dataset already exists at {output_path}")
        return output_path
    
    try:
        # Load dataset with streaming if sample_size is specified to avoid OOM
        if sample_size:
            logger.info(f"Loading with streaming=True to sample {sample_size} rows")
            dataset = load_dataset(
                dataset_id,
                split=split,
                revision=revision,
                streaming=True
            )
            
            # Sample the dataset
            sampled_data = []
            count = 0
            for item in dataset:
                if count >= sample_size:
                    break
                sampled_data.append(item)
                count += 1
            
            logger.info(f"Sampled {count} rows from dataset")
            df = pd.DataFrame(sampled_data)
        else:
            # Load full dataset into memory (might be large)
            dataset = load_dataset(
                dataset_id,
                split=split,
                revision=revision
            )
            df = dataset.to_pandas()
        
        # Ensure required columns exist
        required_cols = ['text', 'timestamp', 'user_id', 'filter_applied']
        available_cols = set(df.columns)
        missing_cols = set(required_cols) - available_cols
        
        if missing_cols:
            logger.warning(f"Dataset missing columns: {missing_cols}. Attempting to map or handle.")
            # Handle missing columns gracefully - for now, we'll just log and continue
            # In a real scenario, we might need to map columns or use defaults
            for col in missing_cols:
                if col == 'filter_applied':
                    df[col] = False  # Default to False if missing
                elif col == 'user_id':
                    df[col] = range(len(df))  # Generate sequential IDs if missing
                elif col == 'timestamp':
                    # Try to infer from existing data or use default
                    df[col] = pd.Timestamp('2020-01-01')
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Saved dataset to {output_path} with {len(df)} rows")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise DataFetchError(f"Failed to download dataset {dataset_id}: {str(e)}")

def validate_existing_dataset(
    output_path: Path,
    expected_md5: Optional[str] = None
) -> bool:
    """
    Validate an existing dataset file.
    
    Args:
        output_path: Path to the dataset file
        expected_md5: Expected MD5 checksum (optional)
    
    Returns:
        True if validation passes
    
    Raises:
        DataFetchError: If validation fails
    """
    if not output_path.exists():
        raise DataFetchError(f"Dataset file not found: {output_path}")
    
    logger.info(f"Validating dataset at {output_path}")
    
    # Check file size (basic sanity check)
    file_size = output_path.stat().st_size
    if file_size == 0:
        raise DataFetchError(f"Dataset file is empty: {output_path}")
    
    # Compute and log MD5
    actual_md5 = _compute_file_md5(output_path)
    logger.info(f"Dataset MD5: {actual_md5}")
    
    if expected_md5 and actual_md5 != expected_md5:
        raise DataFetchError(
            f"MD5 mismatch! Expected: {expected_md5}, Got: {actual_md5}"
        )
    
    # Basic content validation
    try:
        df = pd.read_csv(output_path, nrows=5)  # Read first 5 rows
        required_cols = ['text', 'timestamp', 'user_id']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise DataFetchError(f"Missing required columns: {missing}")
    except Exception as e:
        raise DataFetchError(f"Failed to validate dataset content: {str(e)}")
    
    logger.info("Dataset validation passed")
    return True

def download_and_validate_dataset(
    dataset_id: str = "cardiffnlp/tweet_sentiment_extraction",
    split: str = "train",
    revision: str = "main",
    output_path: Optional[Path] = None,
    expected_md5: Optional[str] = None
) -> Path:
    """
    Main function to download and validate the dataset.
    
    Args:
        dataset_id: HuggingFace dataset ID
        split: Dataset split
        revision: Dataset revision
        output_path: Where to save the dataset
        expected_md5: Expected MD5 checksum (optional)
    
    Returns:
        Path to the validated dataset
    """
    # Use default path if not specified
    if output_path is None:
        output_path = Path(CONFIG.DATA_RAW_DIR) / "social_media.csv"
    
    # Ensure data directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if already downloaded and valid
    if output_path.exists():
        try:
            validate_existing_dataset(output_path, expected_md5)
            return output_path
        except DataFetchError as e:
            logger.warning(f"Existing dataset validation failed: {e}. Re-downloading...")
            output_path.unlink()  # Remove corrupted file
    
    # Download the dataset
    # Apply sampling if configured to meet runtime limits
    sample_size = CONFIG.get_config_value("SAMPLE_SIZE", 10000)
    
    _download_dataset_to_csv(
        dataset_id=dataset_id,
        split=split,
        revision=revision,
        output_path=output_path,
        sample_size=sample_size
    )
    
    # Validate the downloaded file
    validate_existing_dataset(output_path, expected_md5)
    
    return output_path

def run_data_ingestion_pipeline() -> Dict[str, Any]:
    """
    Run the complete data ingestion pipeline.
    
    Returns:
        Dictionary with pipeline results
    """
    logger.info("Starting data ingestion pipeline")
    
    start_time = time.time()
    
    try:
        # Download and validate dataset
        output_path = download_and_validate_dataset(
            dataset_id="cardiffnlp/tweet_sentiment_extraction",
            split="train",
            revision="main"
        )
        
        # Load and verify the data
        df = pd.read_csv(output_path)
        
        result = {
            "status": "success",
            "output_path": str(output_path),
            "row_count": len(df),
            "columns": list(df.columns),
            "elapsed_time_seconds": time.time() - start_time
        }
        
        logger.info(f"Ingestion complete: {result['row_count']} rows in {result['elapsed_time_seconds']:.2f}s")
        return result
        
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "elapsed_time_seconds": time.time() - start_time
        }

if __name__ == "__main__":
    # Set seed for reproducibility
    set_seed(CONFIG.SEED)
    
    # Run the pipeline
    result = run_data_ingestion_pipeline()
    
    if result["status"] == "success":
        logger.info(f"Success! Dataset saved to {result['output_path']}")
        logger.info(f"Columns: {result['columns']}")
        logger.info(f"Rows: {result['row_count']}")
    else:
        logger.error(f"Failed: {result['error']}")
        exit(1)
