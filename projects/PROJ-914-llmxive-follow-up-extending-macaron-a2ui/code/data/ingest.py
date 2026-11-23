"""
Data ingestion module for Macaron-A2UI dataset.
Handles streaming downloads and large dataset chunking to prevent OOM.
"""
import os
import sys
import argparse
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Iterator

import pandas as pd

# Import shared config
try:
    from config import get_raw_data_path, ensure_dirs, RANDOM_SEED
except ImportError:
    # Fallback for direct execution in code/
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_raw_data_path, ensure_dirs, RANDOM_SEED

# Constants
DATASET_ID = "macaron-data/a2ui-bench"
STREAMING_CHUNK_SIZE = 1000  # Rows per chunk for processing
MAX_MEMORY_ROWS = 50000  # Safety limit to prevent OOM on small machines

logger = None

def _get_logger():
    global logger
    if logger is None:
        import logging
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    return logger

def load_dataset_from_hf(
    dataset_id: str = DATASET_ID,
    split: str = "train",
    streaming: bool = True,
    sample_size: Optional[int] = None
) -> Iterator[pd.DataFrame]:
    """
    Load dataset from Hugging Face Hub with streaming support.
    
    Args:
        dataset_id: Hugging Face dataset identifier (namespace/name)
        split: Dataset split to load
        streaming: If True, loads in chunks to save memory
        sample_size: Optional limit on number of rows to process
        
    Returns:
        Iterator of pandas DataFrames (chunks) or a single DataFrame if not streaming
        
    Raises:
        RuntimeError: If the dataset cannot be loaded from the real source.
        ValueError: If the dataset ID is invalid or inaccessible.
    """
    logger = _get_logger()
    logger.info(f"Attempting to load dataset: {dataset_id} (streaming={streaming})...")
    
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("The 'datasets' library is required. Install with: pip install datasets")

    # Verify the dataset exists and is accessible BEFORE attempting to load
    # This prevents hanging on invalid IDs
    try:
        # Attempt a quick head request or info fetch to validate existence
        # We use streaming=True here to avoid downloading metadata if possible
        ds_info = load_dataset(dataset_id, split=split, streaming=True, trust_remote_code=False)
    except Exception as e:
        # Specific error handling for common HuggingFace issues
        error_msg = str(e)
        if "doesn't exist" in error_msg or "404" in error_msg:
            raise RuntimeError(
                f"FATAL ERROR: CRITICAL: Failed to load real dataset from {dataset_id}. "
                f"Error: {error_msg}. Per Data Hygiene Principle, this script does NOT support synthetic fallback. "
                f"Please check your internet connection, dataset ID, or HuggingFace access."
            ) from e
        elif "trust_remote_code" in error_msg:
            raise RuntimeError(
                f"FATAL ERROR: The dataset {dataset_id} requires 'trust_remote_code' which is no longer supported. "
                f"Please check the dataset repository for a standard format (Parquet/CSV) or a fixed loading script. "
                f"Error: {error_msg}"
            ) from e
        else:
            raise RuntimeError(
                f"FATAL ERROR: Failed to load real dataset from {dataset_id}. "
                f"Error: {error_msg}. Per Data Hygiene Principle, this script does NOT support synthetic fallback."
            ) from e

    logger.info(f"Dataset connection established. Fetching data...")

    if streaming:
        # Return an iterator that yields chunks
        count = 0
        for batch in ds_info:
            # Convert batch to DataFrame
            df = pd.DataFrame(batch)
            yield df
            count += len(df)
            if sample_size and count >= sample_size:
                logger.info(f"Reached sample size limit of {sample_size}. Stopping.")
                break
    else:
        # Load full dataset into memory (risky for large datasets)
        ds = load_dataset(dataset_id, split=split, trust_remote_code=False)
        df = ds.to_pandas()
        if sample_size:
            df = df.head(sample_size)
        yield df

def validate_dataframe(df: pd.DataFrame) -> bool:
    """
    Validate that the dataframe has required columns and no missing critical values.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if valid, raises ValueError otherwise
    """
    logger = _get_logger()
    
    # Expected columns based on Macaron-A2UI schema
    required_cols = ["query", "intent", "response", "latency_ms"]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}")
    
    # Check for empty dataset
    if df.empty:
        raise ValueError("Dataset is empty after loading.")
        
    # Check for missing critical values
    if df["query"].isna().any():
        raise ValueError("Dataset contains missing values in 'query' column.")
        
    logger.info(f"Validation passed: {len(df)} rows, {len(df.columns)} columns.")
    return True

def save_raw_csv(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Save the dataframe to a CSV file.
    
    Args:
        df: DataFrame to save
        output_path: Optional path to save to. Defaults to config path.
        
    Returns:
        Path to the saved file
    """
    logger = _get_logger()
    
    if output_path is None:
        output_path = str(get_raw_data_path())
        
    output_path = Path(output_path)
    ensure_dirs()
    
    # Calculate hash for versioning
    content_hash = hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()[:16]
    final_path = output_path.parent / f"raw_data_{content_hash}.csv"
    
    df.to_csv(final_path, index=False)
    logger.info(f"Saved raw data to: {final_path}")
    
    return str(final_path)

def main():
    """
    CLI entry point for data ingestion.
    Usage: python -m code.data.ingest --sample-size 500
    """
    parser = argparse.ArgumentParser(description="Ingest Macaron-A2UI dataset")
    parser.add_argument("--dataset-id", type=str, default=DATASET_ID, help="HuggingFace dataset ID")
    parser.add_argument("--split", type=str, default="train", help="Dataset split")
    parser.add_argument("--streaming", action="store_true", default=True, help="Use streaming mode (default)")
    parser.add_argument("--sample-size", type=int, default=None, help="Limit number of rows")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    
    args = parser.parse_args()
    
    logger = _get_logger()
    logger.info("Starting data ingestion...")
    
    try:
        # Load data in streaming chunks
        # Note: We accumulate into a list for the CLI to save, but for very large
        # datasets, the downstream process should handle the iterator directly.
        # Here we respect the sample_size to keep memory usage low for the CLI demo.
        
        all_chunks = []
        total_rows = 0
        
        for chunk in load_dataset_from_hf(
            dataset_id=args.dataset_id,
            split=args.split,
            streaming=args.streaming,
            sample_size=args.sample_size
        ):
            # Validate each chunk immediately
            validate_dataframe(chunk)
            all_chunks.append(chunk)
            total_rows += len(chunk)
            
            if args.sample_size and total_rows >= args.sample_size:
                break
        
        if not all_chunks:
            raise RuntimeError("No data was loaded from the source.")
        
        # Concatenate chunks
        full_df = pd.concat(all_chunks, ignore_index=True)
        
        # Final validation
        validate_dataframe(full_df)
        
        # Save
        output_file = save_raw_csv(full_df, args.output)
        
        logger.info(f"Ingestion complete. Total rows: {total_rows}")
        logger.info(f"Output saved to: {output_file}")
        
    except RuntimeError as e:
        # Re-raise runtime errors (data source issues) as is
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        raise

if __name__ == "__main__":
    main()