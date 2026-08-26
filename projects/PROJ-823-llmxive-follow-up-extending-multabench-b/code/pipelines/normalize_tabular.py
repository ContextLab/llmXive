import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import pyarrow.parquet as pq
import numpy as np

from config import ensure_directories
from utils.logging import get_logger, log_info, log_warning, log_error
from utils.feature_engineering import normalize_features, save_normalization_metadata
from analysis.metadata_stats import load_dataset_list

logger = get_logger(__name__)

# Output paths as per spec
OUTPUT_PARQUET_PATH = PROJECT_ROOT / "data" / "processed" / "normalized_tabular_features.parquet"
METADATA_JSON_PATH = PROJECT_ROOT / "data" / "processed" / "normalization_metadata.json"
SUMMARY_CSV_PATH = PROJECT_ROOT / "data" / "processed" / "metadata_stats_summary.csv"

def load_raw_tabular_data(dataset_id: str) -> pd.DataFrame:
    """
    Loads raw tabular data for a specific dataset from the data/raw directory.
    Assumes the data is in CSV format named {dataset_id}.csv or similar pattern.
    """
    raw_data_dir = PROJECT_ROOT / "data" / "raw"
    possible_files = list(raw_data_dir.glob(f"{dataset_id}*"))
    
    if not possible_files:
        log_error(f"No raw data file found for dataset_id: {dataset_id} in {raw_data_dir}")
        return None

    # Prefer CSV, then parquet
    csv_files = [f for f in possible_files if f.suffix == '.csv']
    if csv_files:
        target_file = csv_files[0]
    else:
        target_file = possible_files[0]

    log_info(f"Loading raw tabular data from {target_file}")
    try:
        df = pd.read_csv(target_file)
        # Ensure dataset_id column exists for aggregation
        if 'dataset_id' not in df.columns:
            df['dataset_id'] = dataset_id
        return df
    except Exception as e:
        log_error(f"Failed to load {target_file}: {e}")
        return None

def process_all_datasets():
    """
    Loads raw tabular data for ALL available datasets, normalizes them,
    aggregates them into a single DataFrame, and writes the output Parquet file.
    """
    ensure_directories()
    
    log_info("Starting normalization of tabular features for all datasets.")
    
    # Load list of datasets from metadata stats summary (T024e output)
    # If summary doesn't exist yet, fall back to loading dataset list directly
    if not SUMMARY_CSV_PATH.exists():
        log_warning(f"Summary CSV {SUMMARY_CSV_PATH} not found. Attempting to load dataset list directly.")
        dataset_ids = load_dataset_list()
    else:
        try:
            summary_df = pd.read_csv(SUMMARY_CSV_PATH)
            dataset_ids = summary_df['dataset_id'].tolist()
            log_info(f"Loaded {len(dataset_ids)} datasets from summary CSV.")
        except Exception as e:
            log_error(f"Failed to read summary CSV: {e}. Falling back to direct list.")
            dataset_ids = load_dataset_list()

    if not dataset_ids:
        log_error("No datasets found to process. Exiting.")
        return

    all_normalized_data = []
    total_rows = 0

    for ds_id in dataset_ids:
        log_info(f"Processing dataset: {ds_id}")
        raw_df = load_raw_tabular_data(ds_id)
        
        if raw_df is None or raw_df.empty:
            log_warning(f"Skipping {ds_id}: No data loaded.")
            continue

        # Normalize features using the canonical function
        # Ensure dataset_id is not treated as a numeric feature if it's string
        # The normalize_features function handles 'dataset_id' removal internally if present
        
        normalized_df, metadata = normalize_features(raw_df, method="zscore")
        
        if normalized_df is not None and not normalized_df.empty:
            all_normalized_data.append(normalized_df)
            total_rows += len(normalized_df)
            log_info(f"Processed {ds_id}: {len(normalized_df)} rows. Features normalized.")
        else:
            log_warning(f"Normalization returned empty result for {ds_id}.")

    if not all_normalized_data:
        log_error("No data was successfully normalized. Aborting write.")
        return

    # Concatenate all datasets
    final_df = pd.concat(all_normalized_data, ignore_index=True)
    log_info(f"Aggregated {len(final_df)} total rows across {len(dataset_ids)} datasets.")

    # Ensure output directory exists
    OUTPUT_PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write to Parquet
    log_info(f"Writing normalized features to {OUTPUT_PARQUET_PATH}")
    try:
        # Use pyarrow engine for better compatibility
        final_df.to_parquet(OUTPUT_PARQUET_PATH, engine='pyarrow', index=False)
        log_info("Successfully wrote normalized_tabular_features.parquet")
    except Exception as e:
        log_error(f"Failed to write Parquet file: {e}")
        raise

    # Save normalization metadata for downstream tasks (T019d, T025)
    # We aggregate metadata from all datasets; since normalization is global per feature
    # across the full dataset in this implementation, we save the combined metadata
    # Note: The current normalize_features computes stats per DataFrame. 
    # For strict global stats across ALL datasets combined, we should ideally 
    # concatenate first, then normalize. However, per task T024f logic "global mean/std 
    # calculated from the full dataset", we interpret 'full dataset' as the union of all.
    # To be safe and consistent with the 'canonical function' requirement which processes
    # per dataset in the loop above, we save the metadata from the last processed dataset 
    # or a merged version if the function was designed to be global.
    # Given the current normalize_features implementation processes per DataFrame, 
    # and we need global stats, we should technically re-implement or adjust.
    # However, to strictly follow the "canonical function" constraint and the task description
    # which says "Load raw tabular data, apply... using global mean/std", 
    # we will re-calculate global stats on the concatenated data to ensure correctness.
    
    log_info("Recalculating global normalization metadata for the full combined dataset.")
    # Re-normalize the concatenated data to get true global stats
    # This ensures T019d and T025 use the EXACT same parameters.
    final_df_re = final_df.copy()
    # Remove dataset_id from numeric calculation if present
    if 'dataset_id' in final_df_re.columns:
        final_df_re['dataset_id'] = final_df_re['dataset_id'].astype(str) # Ensure string
    
    # We need a way to get global metadata. 
    # Let's modify the approach: The task says "global mean/std calculated from the full dataset".
    # The current loop normalizes per dataset. To satisfy the requirement strictly:
    # 1. Concatenate raw data.
    # 2. Compute global mean/std.
    # 3. Normalize.
    # Since we already did per-dataset, let's re-do the normalization on the concatenated raw data
    # to get the true global metadata.
    
    # Re-load raw data for all datasets to concatenate
    raw_combined = []
    for ds_id in dataset_ids:
        raw_df = load_raw_tabular_data(ds_id)
        if raw_df is not None:
            raw_combined.append(raw_df)
    
    if raw_combined:
        combined_raw = pd.concat(raw_combined, ignore_index=True)
        final_normalized, global_metadata = normalize_features(combined_raw, method="zscore")
        
        # Overwrite the final_df with the truly globally normalized one
        final_df = final_normalized
        
        # Save the global metadata
        save_normalization_metadata(global_metadata, METADATA_JSON_PATH)
        
        # Rewrite the parquet
        final_df.to_parquet(OUTPUT_PARQUET_PATH, engine='pyarrow', index=False)
        log_info(f"Rewrote {OUTPUT_PARQUET_PATH} with global normalization.")
        log_info(f"Saved global metadata to {METADATA_JSON_PATH}")

def main():
    """
    Main entry point for the normalization pipeline.
    """
    parser = argparse.ArgumentParser(description="Normalize tabular features for all datasets.")
    parser.add_argument('--method', type=str, default='zscore', choices=['zscore', 'minmax'],
                        help='Normalization method to use.')
    args = parser.parse_args()

    # Override global method if passed via CLI (optional extension)
    # For now, we stick to zscore as per spec default, but the function supports both.
    
    try:
        process_all_datasets()
        log_info("Normalization pipeline completed successfully.")
    except Exception as e:
        log_error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
