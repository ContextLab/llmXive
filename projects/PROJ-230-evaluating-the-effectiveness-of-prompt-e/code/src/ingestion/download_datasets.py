"""
Dataset Ingestion Module for PROJ-230.

Fetches code translation pairs from HuggingFace datasets,
caches raw data to data/raw/, and extracts python_code/javascript_code columns.
"""
import os
import sys
import logging
import traceback
from pathlib import Path

# Add project root to path to allow imports from src/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from datasets import load_dataset
from src.utils.logging import get_logger, log_raw_output

# Configure logging
logger = get_logger(__name__)

# Constants
DATASET_NAMES = [
    "codeparrot/code-trans-py-js",
    "bigcode/evaluation"
]
OUTPUT_DIR = Path(project_root) / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "raw_code_corpus.parquet"

def ensure_dirs():
    """Ensure output directories exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {OUTPUT_DIR}")

def fetch_dataset(dataset_name: str):
    """
    Fetch a dataset from HuggingFace.
    
    Args:
        dataset_name: Name of the dataset on HuggingFace.
        
    Returns:
        Dataset object or None if failed.
    """
    logger.info(f"Fetching dataset: {dataset_name}")
    try:
        # Load dataset with streaming to manage memory
        ds = load_dataset(dataset_name, split="train", streaming=False)
        logger.info(f"Successfully loaded {dataset_name}: {len(ds)} rows")
        return ds
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        logger.error(traceback.format_exc())
        return None

def extract_code_columns(dataset, source_col: str, target_col: str):
    """
    Extract and validate code columns from a dataset.
    
    Args:
        dataset: The loaded dataset.
        source_col: Name of the source code column (e.g., python_code).
        target_col: Name of the target code column (e.g., javascript_code).
        
    Returns:
        List of dicts with extracted code, or empty list if failed.
    """
    extracted = []
    logger.info(f"Extracting columns '{source_col}' and '{target_col}'")
    
    for i, row in enumerate(dataset):
        # Check if columns exist
        if source_col not in row or target_col not in row:
            if i < 5:  # Log only first few missing
                logger.warning(f"Row {i} missing required columns")
            continue
        
        src_code = row[source_col]
        tgt_code = row[target_col]
        
        # Validate types and content
        if not isinstance(src_code, str) or not isinstance(tgt_code, str):
            if i < 5:
                logger.warning(f"Row {i} has non-string code")
            continue
        
        if not src_code.strip() or not tgt_code.strip():
            if i < 5:
                logger.warning(f"Row {i} has empty code")
            continue
        
        extracted.append({
            "source_language": "python",
            "target_language": "javascript",
            "python_code": src_code,
            "javascript_code": tgt_code
        })
        
        # Log progress every 1000 rows
        if (i + 1) % 1000 == 0:
            logger.info(f"Processed {i + 1} rows, extracted {len(extracted)} valid pairs")

    return extracted

def main():
    """Main entry point for dataset ingestion."""
    logger.info("Starting dataset ingestion pipeline")
    ensure_dirs()

    all_records = []

    for ds_name in DATASET_NAMES:
        ds = fetch_dataset(ds_name)
        if ds is None:
            logger.warning(f"Skipping {ds_name} due to fetch failure")
            continue

        # Attempt to extract standard columns first
        # Different datasets may have different column names
        # We try common patterns
        possible_source_cols = ["python_code", "source_code", "code", "python"]
        possible_target_cols = ["javascript_code", "target_code", "translation", "javascript"]

        extracted = []
        for src_col in possible_source_cols:
            for tgt_col in possible_target_cols:
                if src_col in ds.column_names and tgt_col in ds.column_names:
                    logger.info(f"Found columns: {src_col} -> {tgt_col}")
                    extracted = extract_code_columns(ds, src_col, tgt_col)
                    if extracted:
                        break
            if extracted:
                break
        
        if not extracted:
            logger.warning(f"No valid code pairs found in {ds_name} with standard column names")
            logger.info(f"Available columns in {ds_name}: {ds.column_names}")
            continue

        all_records.extend(extracted)
        logger.info(f"Extracted {len(extracted)} pairs from {ds_name}")

    if not all_records:
        logger.error("No valid code pairs extracted from any dataset")
        sys.exit(1)

    logger.info(f"Total valid pairs collected: {len(all_records)}")

    # Convert to pandas DataFrame for easy saving
    import pandas as pd
    df = pd.DataFrame(all_records)

    # Save to parquet (efficient storage)
    logger.info(f"Saving {len(df)} rows to {OUTPUT_FILE}")
    df.to_parquet(OUTPUT_FILE, index=False)
    
    # Also save a CSV for quick inspection
    csv_path = OUTPUT_DIR / "raw_code_corpus.csv"
    df.to_csv(csv_path, index=False)
    
    logger.info(f"Saved raw corpus to {OUTPUT_FILE} and {csv_path}")
    logger.info("Dataset ingestion completed successfully")

    # Log a sample for audit
    if len(df) > 0:
        sample = df.iloc[0].to_dict()
        log_raw_output("ingestion_sample", sample)

if __name__ == "__main__":
    main()