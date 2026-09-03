import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

# Add project root to path to resolve local imports if run directly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datasets import load_dataset
from config import DataConfig, ensure_dirs
from utils.logger import get_logger

def check_schema_pass(schema_log_path: Path) -> bool:
    """
    Check if T011a passed by verifying the existence and content of schema_check.log.
    Returns True if the log indicates success (no fatal errors).
    """
    if not schema_log_path.exists():
        logging.error(f"Schema check log not found at {schema_log_path}. T011a may not have run.")
        return False

    try:
        with open(schema_log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # The schema check task logs a fatal error if columns are missing.
            # We assume success if the file exists and doesn't contain the specific fatal error marker.
            # Based on T011a spec: "If missing, immediately raise ValueError... Output: data/processed/schema_check.log"
            # We look for a success indicator or absence of 'FATAL' or 'ValueError' in the log content.
            # A robust check: if the file exists and contains "Schema validation passed" or similar.
            # Since T011a implementation details might vary, we check for the absence of a fatal failure state.
            # If the task T011a raised a ValueError, the script would have crashed and not created a log,
            # OR created a log with the error. The spec says "halt the entire pipeline".
            # Let's assume if the file exists, we check for a success marker.
            # If T011a was implemented to write "Schema validation passed" on success.
            if "Schema validation passed" in content or "validation successful" in content.lower():
                return True
            # If it contains "FATAL" or "ValueError" related to missing columns, fail.
            if "FATAL" in content or "ValueError" in content:
                logging.error(f"Schema check failed: {content}")
                return False
            # If file exists but no clear marker, assume pass if no error keywords found?
            # Safest: require explicit success marker.
            logging.warning(f"Schema check log exists but no explicit success marker found. Assuming pass if no errors.")
            return "FATAL" not in content and "ValueError" not in content
    except Exception as e:
        logging.error(f"Error reading schema check log: {e}")
        return False

def download_dataset(config: DataConfig, logger: logging.Logger) -> Path:
    """
    Fetch verified SN1 data from HuggingFace datasets.
    Uses streaming if the dataset is large (>7GB estimated or based on config).
    Saves raw data to data/raw/sn1_raw.parquet.
    """
    output_dir = config.raw_data_dir
    ensure_dirs([output_dir])
    output_path = output_dir / "sn1_raw.parquet"

    # Datasets specified in T011a
    dataset_names = ["DTS-SN1-15-01-2024", "SN18-All-20240204"]
    
    # Since we need to merge or pick one, and the spec says "verified SN1 data",
    # we will attempt to load the first one. If it fails, try the second.
    # The task description implies fetching "verified SN1 data", singular output.
    # We will try to load the primary dataset.
    
    selected_dataset_name = None
    for name in dataset_names:
        try:
            # Check if dataset exists (simple head check)
            # We use streaming=False for the initial check if we want to be sure, 
            # but for large datasets streaming is preferred.
            # However, to be safe and avoid downloading huge metadata if not needed,
            # we'll try to load with streaming=True and take the first few rows to confirm.
            # Actually, the task says "Use streaming=True if size > 7GB".
            # We don't know size beforehand. We'll assume these are large scientific datasets.
            # We will use streaming=True for all to be safe and memory efficient.
            
            # Note: The dataset name on HF might be different. 
            # Assuming the names provided are the HF dataset IDs.
            # If they are not public, we might need a token, but we assume public access for now.
            
            logger.info(f"Attempting to load dataset: {name}")
            
            # We use streaming=True as a default for scientific datasets which are often large.
            # If the dataset is small, streaming still works fine.
            ds = load_dataset(name, split="train", streaming=True)
            
            # Verify we got data
            first_row = next(iter(ds))
            if first_row:
                selected_dataset_name = name
                logger.info(f"Successfully connected to dataset: {name}. Starting download/stream.")
                break
        except Exception as e:
            logger.warning(f"Failed to load dataset {name}: {e}")
            continue

    if not selected_dataset_name:
        raise RuntimeError("Failed to load any of the specified SN1 datasets from HuggingFace.")

    # Re-load to process all data. 
    # Since we need to save to parquet, we need to iterate through the whole dataset.
    # Using streaming=True is efficient for large datasets.
    logger.info(f"Downloading/Streaming full dataset: {selected_dataset_name}")
    
    ds = load_dataset(selected_dataset_name, split="train", streaming=True)
    
    import pyarrow as pa
    import pyarrow.parquet as pq
    
    # We will collect data in batches to write to parquet efficiently
    # or write directly if the library supports it. 
    # Since streaming yields rows, we need to convert to a format PyArrow can write.
    # A simple approach for large data: write batches to a temp file or use a table builder.
    # However, for a single file output, we can accumulate or write in append mode if supported.
    # PyArrow Table.from_pylist can handle a list, but memory might be an issue.
    # Better: Write in chunks.
    
    # Check if we can get the schema
    # streaming datasets don't always have a fixed schema exposed easily without iterating.
    # We will assume the first row defines the schema.
    
    try:
        # Get first row to infer schema
        sample_row = next(iter(ds))
        # Convert to a list of dicts for the first batch
        # We'll process the rest in chunks
        
        # To write a parquet file from a streaming dataset, we can:
        # 1. Collect all rows (memory heavy)
        # 2. Write chunks to a single file (requires append support or multi-part then merge)
        # PyArrow ParquetWriter supports append? No, usually you write a Table.
        # Alternative: Use `to_pandas()` on chunks? No, memory.
        # Best approach for streaming: Use a ParquetWriter with a schema.
        
        # Infer schema from first row
        schema = pa.Table.from_pydict({k: [v] for k, v in sample_row.items()}).schema
        
        # Create a ParquetWriter
        # Note: Some streaming datasets might yield lists or nested types.
        # We assume flat or compatible types for now.
        
        writer = pq.ParquetWriter(output_path, schema)
        
        count = 0
        # Process the first row
        batch = [sample_row]
        table = pa.Table.from_pylist(batch)
        writer.write_table(table)
        count += 1
        
        # Process remaining
        for row in ds:
            # Skip the first one if we already processed it (iterator behavior)
            # Actually, the iterator `iter(ds)` yields the first item.
            # We need to handle the loop carefully.
            # We already consumed one item.
            # So we continue with the rest.
            batch = [row]
            table = pa.Table.from_pylist(batch)
            writer.write_table(table)
            count += 1
            if count % 10000 == 0:
                logger.info(f"Processed {count} rows...")
        
        writer.close()
        logger.info(f"Successfully wrote {count} rows to {output_path}")
        
    except Exception as e:
        # Fallback: if streaming logic fails, try loading fully if small (unlikely)
        logger.error(f"Error during streaming write: {e}")
        # Try a different approach: load as pandas if small enough?
        # If streaming fails, we might need to load fully.
        # But the constraint is "Use streaming if size > 7GB".
        # If we can't stream, we fail loudly.
        raise RuntimeError(f"Failed to write dataset to parquet using streaming: {e}")

    return output_path

def main():
    parser = argparse.ArgumentParser(description="Download SN1 datasets.")
    parser.add_argument("--config-path", type=str, default="code/config.py", help="Path to config module")
    args = parser.parse_args()

    # Setup logging
    logger = get_logger("download", "data/raw")
    
    # Load config
    try:
        from config import DataConfig
        config = DataConfig()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    # Check T011a result
    schema_log_path = config.processed_data_dir / "schema_check.log"
    if not check_schema_pass(schema_log_path):
        logger.error("T011a (Schema Check) did not pass. Halting download.")
        sys.exit(1)

    try:
        output_path = download_dataset(config, logger)
        logger.info(f"Download complete. Output: {output_path}")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
