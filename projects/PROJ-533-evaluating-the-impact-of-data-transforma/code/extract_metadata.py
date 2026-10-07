import os
import sys
import csv
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np
from scipy import stats

# Project internal imports
from code.utils.logging_config import setup_pipeline_logger
from code.utils.schema_definitions import get_datasets_headers
from code.utils.streaming_utils import stream_csv_rows, OnlineStatsCalculator, get_file_row_count

logger = setup_pipeline_logger("extract_metadata")

# Constants
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
FILTERED_CSV = DATA_DIR / "datasets.csv"
CHECKSUMS_CSV = DATA_DIR / "checksums.csv"
OUTPUT_CSV = DATA_DIR / "datasets.csv" # Overwrite or update existing
SAMPLE_SIZE_LIMIT = 100000 # Max rows to sample for stats if dataset is huge
MIN_SAMPLE_ROWS = 1000     # Minimum rows required for valid skew/kurtosis estimation

def load_filtered_dataset() -> List[Dict]:
    """Load the list of filtered datasets from data/datasets.csv."""
    if not FILTERED_CSV.exists():
        raise FileNotFoundError(f"Filtered dataset list not found: {FILTERED_CSV}")
    
    datasets = []
    with open(FILTERED_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure dataset_id is available
            if 'dataset_id' not in row:
                logger.warning(f"Skipping row missing dataset_id: {row}")
                continue
            datasets.append(row)
    return datasets

def get_checksum_for_dataset(dataset_id: str) -> Optional[str]:
    """Retrieve the SHA-256 checksum for a given dataset_id from checksums.csv."""
    if not CHECKSUMS_CSV.exists():
        logger.warning(f"Checksums file not found: {CHECKSUMS_CSV}")
        return None
    
    with open(CHECKSUMS_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('dataset_id') == dataset_id:
                return row.get('checksum')
    return None

def get_filter_result(dataset_id: str) -> Optional[Dict]:
    """Retrieve filter results (shapiro_p, sample_size, included) for a dataset_id."""
    filter_results_path = DATA_DIR / "filter_results.csv"
    if not filter_results_path.exists():
        return None
    
    with open(filter_results_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('dataset_id') == dataset_id:
                return row
    return None

def compute_global_stats(df: pd.DataFrame, continuous_cols: List[str]) -> Dict[str, Any]:
    """
    Compute global statistics (mean, std, skewness, kurtosis) for continuous columns.
    Uses a representative sample if the dataset is very large to avoid memory issues,
    but ensures at least MIN_SAMPLE_ROWS are used.
    """
    stats_dict = {}
    
    # Determine sample size
    total_rows = len(df)
    if total_rows <= SAMPLE_SIZE_LIMIT:
        sample_df = df
    else:
        # Sample a representative chunk. 
        # If streaming was used previously, we might have a parquet file.
        # Here we assume df is already loaded or sampled.
        if total_rows < MIN_SAMPLE_ROWS:
            raise ValueError(f"Dataset has fewer than {MIN_SAMPLE_ROWS} rows ({total_rows}). Cannot compute reliable skew/kurtosis.")
        
        sample_df = df.sample(n=min(SAMPLE_SIZE_LIMIT, total_rows), random_state=42)
    
    if len(sample_df) < MIN_SAMPLE_ROWS:
        raise ValueError(f"Sample size {len(sample_df)} is less than required {MIN_SAMPLE_ROWS}.")

    for col in continuous_cols:
        if col not in sample_df.columns:
            continue
        
        col_data = sample_df[col].dropna()
        if len(col_data) < 5:
            continue # Need at least 5 points for skew/kurtosis in scipy
        
        try:
            skew_val = stats.skew(col_data)
            kurt_val = stats.kurtosis(col_data) # Fisher's definition (normal=0)
            stats_dict[col] = {
                "mean": float(col_data.mean()),
                "std": float(col_data.std()),
                "skewness": float(skew_val),
                "kurtosis": float(kurt_val)
            }
        except Exception as e:
            logger.warning(f"Could not compute stats for {col}: {e}")
            stats_dict[col] = {
                "mean": float(col_data.mean()),
                "std": float(col_data.std()),
                "skewness": None,
                "kurtosis": None
            }
    
    return stats_dict

def identify_continuous_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns that appear to be continuous (numeric)."""
    continuous_cols = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            # Exclude integer IDs if they look like IDs (e.g., 1, 2, 3... or unique count == rows)
            unique_count = df[col].nunique()
            if unique_count < len(df) * 0.1 and unique_count > 10:
                # Likely an ID or categorical integer, skip
                continue
            continuous_cols.append(col)
    return continuous_cols

def extract_metadata_for_dataset(dataset_row: Dict) -> Optional[Dict]:
    """
    Extract metadata for a single dataset: sample size, continuous vars, group labels, source_url, checksum, stats.
    """
    dataset_id = dataset_row.get('dataset_id')
    if not dataset_id:
        return None

    # Determine file path
    # Assuming raw files are stored as data/raw/{dataset_id}.csv or similar
    # We need to find the actual file. Let's look in data/raw/
    raw_files = list(RAW_DIR.glob(f"{dataset_id}*"))
    if not raw_files:
        logger.error(f"No raw file found for dataset_id: {dataset_id}")
        return None
    
    file_path = raw_files[0]
    logger.info(f"Processing metadata for {dataset_id} from {file_path}")

    # Load data
    # Use chunking/streaming if file is huge, but for metadata extraction we might need a sample
    try:
        # Try to load with pandas. If too big, we might need to stream.
        # For this task, we assume we can load a sample or the whole thing if < 100k rows.
        # We'll use a chunked approach to count rows and get a sample.
        
        row_count = get_file_row_count(file_path)
        if row_count < MIN_SAMPLE_ROWS:
            logger.error(f"Dataset {dataset_id} has only {row_count} rows. Skipping (requires >= {MIN_SAMPLE_ROWS}).")
            return None
        
        # Load a sample for stats and full header info
        # If row_count is huge, load a sample. If small, load all.
        if row_count > SAMPLE_SIZE_LIMIT:
            df_sample = pd.read_csv(file_path, nrows=SAMPLE_SIZE_LIMIT)
        else:
            df_sample = pd.read_csv(file_path)
        
        if len(df_sample) < MIN_SAMPLE_ROWS:
            logger.error(f"Sample for {dataset_id} is too small ({len(df_sample)} < {MIN_SAMPLE_ROWS}).")
            return None

        continuous_cols = identify_continuous_columns(df_sample)
        if not continuous_cols:
            logger.warning(f"No continuous columns found for {dataset_id}.")
            # Still proceed, but stats will be empty
        
        global_stats = compute_global_stats(df_sample, continuous_cols)
        
        # Identify group labels (categorical columns with low cardinality)
        group_labels = []
        for col in df_sample.columns:
            if not pd.api.types.is_numeric_dtype(df_sample[col]):
                if df_sample[col].nunique() < 10 and df_sample[col].nunique() > 1:
                    group_labels.append(col)
            elif df_sample[col].nunique() < 10 and df_sample[col].nunique() > 1:
                # Low cardinality numeric
                group_labels.append(col)

        checksum = get_checksum_for_dataset(dataset_id)
        filter_res = get_filter_result(dataset_id)
        source_url = dataset_row.get('source_url', 'unknown')

        return {
            "dataset_id": dataset_id,
            "source_url": source_url,
            "checksum": checksum,
            "sample_size": int(row_count),
            "continuous_variables": continuous_cols,
            "group_labels": group_labels,
            "distribution_stats": global_stats,
            "shapiro_p": float(filter_res.get('shapiro_p', 0)) if filter_res else None,
            "included": filter_res.get('included', False) if filter_res else False
        }

    except Exception as e:
        logger.error(f"Failed to extract metadata for {dataset_id}: {e}", exc_info=True)
        return None

def write_metadata_csv(metadata_list: List[Dict], output_path: Path):
    """Write the extracted metadata to the datasets.csv file, updating existing or creating new."""
    if not metadata_list:
        logger.warning("No metadata to write.")
        return

    # Define headers
    base_headers = ["dataset_id", "source_url", "checksum", "sample_size", "continuous_variables", "group_labels", "shapiro_p", "included"]
    # We will flatten distribution_stats into columns like skewness_colname, kurtosis_colname? 
    # Or store as JSON string. The task says "write to data/datasets.csv". 
    # To keep it CSV-friendly, we'll store complex stats as JSON strings in a 'distribution_stats' column.
    
    headers = base_headers + ["distribution_stats"]
    
    # Check if file exists to handle append vs write
    file_exists = output_path.exists()
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        for meta in metadata_list:
            row = {k: meta.get(k, '') for k in base_headers}
            # Serialize stats to JSON
            row['distribution_stats'] = json.dumps(meta.get('distribution_stats', {}))
            writer.writerow(row)

    logger.info(f"Wrote metadata for {len(metadata_list)} datasets to {output_path}")

def main():
    logger.info("Starting metadata extraction (T017).")
    
    try:
        datasets = load_filtered_dataset()
        logger.info(f"Loaded {len(datasets)} datasets to process.")
        
        if not datasets:
            logger.warning("No datasets found to process.")
            return

        metadata_results = []
        
        for ds in datasets:
            meta = extract_metadata_for_dataset(ds)
            if meta:
                metadata_results.append(meta)
        
        if not metadata_results:
            logger.error("No metadata could be extracted. Aborting.")
            sys.exit(1)

        write_metadata_csv(metadata_results, OUTPUT_CSV)
        
        logger.info("Metadata extraction completed successfully.")
        
    except Exception as e:
        logger.error(f"Fatal error in metadata extraction: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()