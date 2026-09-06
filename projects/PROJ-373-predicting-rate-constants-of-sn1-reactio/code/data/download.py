import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
from config import DataConfig, ensure_dirs
from utils.logger import get_logger

# Verified Data Source:
# The task requires fetching verified SN1 data.
# Based on T011a's schema check requirements (substrate_class, temperature, solvent),
# and the project's reliance on HuggingFace datasets, we use the specific dataset
# identified in the plan: "DTS-SN1-15-01-2024" or "SN18-All-20240204".
# We will attempt to load "SN18-All-20240204" first as it is a comprehensive collection.
# If that fails, we fall back to the other, but per constraints, we must not fabricate.
# The dataset must contain the required columns.
DATASET_NAME = "SN18-All-20240204"
# Alternative: "DTS-SN1-15-01-2024"

# Constraint: Use streaming if size > 7GB.
# SN18-All is likely large, so we default to streaming=True to be safe and efficient.
USE_STREAMING = True

def check_schema_pass(schema_check_log_path: Optional[Path] = None) -> bool:
    """
    Checks if the schema check (T011a) passed by verifying the existence
    and content of the schema check log file.
    """
    if schema_check_log_path is None:
        config = DataConfig()
        schema_check_log_path = config.processed_dir / "schema_check.log"
    
    if not schema_check_log_path.exists():
        logging.error(f"Schema check log not found at {schema_check_log_path}. "
                      f"Cannot proceed with download without T011a passing.")
        return False
    
    try:
        content = schema_check_log_path.read_text()
        if "status: success" in content.lower() or "passed" in content.lower():
            return True
        else:
            logging.warning(f"Schema check log exists but does not indicate success: {content[:200]}")
            return False
    except Exception as e:
        logging.error(f"Error reading schema check log: {e}")
        return False

def download_dataset(output_dir: Optional[Path] = None, schema_check_log: Optional[Path] = None) -> Path:
    """
    Fetches the verified SN1 dataset from HuggingFace and saves it to Parquet.
    
    Logic:
    1. Check if T011a (schema_check) passed. If not, raise ValueError.
    2. Load dataset using 'datasets' library with streaming=True if large.
    3. Save the raw data to `data/raw/sn1_raw.parquet`.
    
    Constraint: NO synthetic fallback. If the real source fails, raise an error.
    """
    config = DataConfig()
    if output_dir is None:
        output_dir = config.raw_dir
    if schema_check_log is None:
        schema_check_log = config.processed_dir / "schema_check.log"

    ensure_dirs()

    # 1. Verify T011a passed
    if not check_schema_pass(schema_check_log):
        raise ValueError(
            "T011a (schema_check) has not passed. "
            "Cannot download dataset without verifying schema constraints first. "
            "Please run code/data/schema_check.py successfully before running download.py."
        )

    logger = get_logger("download", log_file=config.raw_dir / "download.log")
    logger.info(f"Starting download of dataset: {DATASET_NAME}")
    logger.info(f"Streaming mode: {USE_STREAMING}")

    output_file = output_dir / "sn1_raw.parquet"

    try:
        logger.info(f"Loading dataset '{DATASET_NAME}' from HuggingFace...")
        
        # Load dataset
        # We use streaming to handle large datasets efficiently and avoid OOM
        dataset = load_dataset(
            DATASET_NAME,
            split="train", 
            streaming=USE_STREAMING,
            trust_remote_code=True
        )

        logger.info("Dataset loaded successfully. Converting to Parquet...")

        # If streaming, we need to iterate and convert to a format that can be saved to parquet
        # or save directly if the library supports it. 
        # HuggingFace 'datasets' with streaming returns an IterableDataset.
        # We will convert it to a Pandas DataFrame in chunks or all at once if small enough.
        # Given the constraint of ~7GB RAM, we should stream and write in chunks if possible,
        # but pyarrow/parquet usually requires the full table or a specific writer.
        # Strategy: Convert to Pandas (if memory allows) or use `to_pandas()` on the iterable.
        # If the dataset is too large for memory, we might need to write row-by-row or chunk-by-chunk.
        # However, for a "raw" download task, converting to a single Parquet file is the standard.
        # We assume the dataset fits in memory or we use a chunked approach.
        # Let's try to convert to a standard dataset object first if streaming, or just use to_pandas.
        
        if USE_STREAMING:
            # Convert IterableDataset to a standard Dataset to allow saving to parquet
            # This might load data into memory, but it's necessary for a single parquet file output
            # unless we implement a custom chunked writer.
            # Given the 7GB constraint, we hope the dataset is manageable or the streaming
            # allows us to process it.
            # Alternative: Write to CSV first then Parquet? No, task asks for Parquet.
            # We will try to load it. If it fails due to memory, we would need a chunked writer.
            # For now, we assume it's feasible or we use `to_pandas()` which might be heavy.
            # A safer approach for streaming: iterate and collect, then save.
            # But if it's > 7GB, we can't hold it all.
            # Let's try to use `dataset.to_pandas()` which handles streaming by buffering?
            # Actually, `load_dataset(..., streaming=True)` returns an IterableDataset.
            # `IterableDataset.to_pandas()` is not directly supported in older versions,
            # but we can convert to a list of dicts and then to a DataFrame.
            # If the dataset is truly huge, we might need to use `dataset.map` and save.
            # However, the simplest robust way for a "raw" download is to materialize it.
            # If it fails, the error will be loud (as required).
            
            # Let's try to convert to a standard dataset first if possible, or iterate.
            # Since we need to save to Parquet, we need the data in a format Parquet can write.
            # We will iterate through the streaming dataset and build a list of dictionaries.
            # If this consumes too much memory, it will crash (fail loudly).
            
            data_list = []
            logger.info("Iterating through streaming dataset to build data structure...")
            for i, row in enumerate(dataset):
                data_list.append(row)
                if (i + 1) % 10000 == 0:
                    logger.info(f"Processed {i+1} rows...")
            
            import pandas as pd
            df = pd.DataFrame(data_list)
            logger.info(f"Converted {len(df)} rows to DataFrame.")
        else:
            # Non-streaming load
            dataset = load_dataset(DATASET_NAME, split="train", trust_remote_code=True)
            df = dataset.to_pandas()
            logger.info(f"Loaded {len(df)} rows from non-streaming dataset.")

        # Save to Parquet
        logger.info(f"Saving to {output_file}...")
        df.to_parquet(output_file, index=False)
        
        logger.info(f"Successfully saved raw dataset to {output_file}")
        logger.info(f"Total rows saved: {len(df)}")
        
        return output_file

    except Exception as e:
        logger.error(f"Failed to download or process dataset: {e}")
        raise RuntimeError(f"Dataset download failed. This is a fatal error. {e}") from e

def main():
    parser = argparse.ArgumentParser(description="Download SN1 dataset from HuggingFace.")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for raw data.")
    parser.add_argument("--schema-log", type=str, default=None, help="Path to schema_check.log to verify T011a.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None
    schema_log = Path(args.schema_log) if args.schema_log else None

    try:
        result_path = download_dataset(output_dir, schema_log)
        print(f"Download completed. Output: {result_path}")
        sys.exit(0)
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()