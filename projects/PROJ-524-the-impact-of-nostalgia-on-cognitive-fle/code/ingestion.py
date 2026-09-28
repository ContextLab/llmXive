import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd

from utils import setup_logging, log_info, log_warning, log_error, compute_sha256
from config import get_config, ensure_dirs
from ingestion.fetcher import fetch_data, save_metadata
from ingestion.validator import clean_data, save_exclusion_log, calculate_validity_metrics, save_validity_metrics

logger = logging.getLogger(__name__)

def main():
    """Main entry point for data ingestion pipeline."""
    setup_logging()
    config = get_config()
    ensure_dirs()
    
    # Fetch data
    log_info("Starting data ingestion pipeline...")
    df, source, simulation_mode = fetch_data()
    
    if df is None or df.empty:
        log_error("No data fetched. Aborting.")
        return
    
    # Save raw dataset
    raw_path = Path(config['data_raw_dir']) / 'raw_dataset.csv'
    df.to_csv(raw_path, index=False)
    log_info(f"Raw dataset saved to {raw_path}")
    
    # T011: Data Validation Logic
    # Filter for age >= 65
    if 'age' not in df.columns:
        log_error("ERR_MISSING_AGE_FIELD: 'age' column not found in dataset.")
        raise ValueError("Missing required 'age' column")
    
    initial_count = len(df)
    
    # Filter age >= 65
    age_filtered = df[df['age'] >= 65]
    age_excluded_count = initial_count - len(age_filtered)
    
    if age_excluded_count > 0:
        log_warning(f"Excluded {age_excluded_count} records due to age < 65.")
    else:
        log_info("No records excluded due to age < 65.")
    
    # Exclude missing stimulus_type
    if 'stimulus_type' not in age_filtered.columns:
        log_error("ERR_MISSING_STIMULUS_TYPE: 'stimulus_type' column not found.")
        raise ValueError("Missing required 'stimulus_type' column")
    
    valid_stimulus = age_filtered.dropna(subset=['stimulus_type'])
    stimulus_excluded_count = len(age_filtered) - len(valid_stimulus)
    
    if stimulus_excluded_count > 0:
        log_warning(f"Excluded {stimulus_excluded_count} records due to missing 'stimulus_type'.")
    else:
        log_info("No records excluded due to missing 'stimulus_type'.")
    
    # Update df for subsequent steps
    df = valid_stimulus
    
    # Log validation summary
    log_info(f"Validation complete. Started with {initial_count} records, ended with {len(df)} valid records.")
    
    # Clean data
    try:
        cleaned_df, exclusion_counts = clean_data(df, simulation_mode)
    except Exception as e:
        log_error(f"Data cleaning failed: {e}")
        return
    
    # Save exclusion log
    exclusion_log_path = Path(config['data_processed_dir']) / 'exclusion_log.json'
    save_exclusion_log(exclusion_counts, str(exclusion_log_path))
    
    # Calculate and save validity metrics
    raw_count = len(df)
    valid_count = len(cleaned_df)
    metrics = calculate_validity_metrics(raw_count, valid_count)
    metrics_path = Path(config['data_processed_dir']) / 'validity_metrics.json'
    save_validity_metrics(metrics, str(metrics_path))
    
    # Save intermediate cleaned dataset
    intermediate_path = Path(config['data_processed_dir']) / 'cleaned_dataset_intermediate.csv'
    cleaned_df.to_csv(intermediate_path, index=False)
    log_info(f"Intermediate cleaned dataset saved to {intermediate_path}")
    
    # Save metadata
    metadata = {
        "dataset_source": source,
        "simulation_mode": simulation_mode,
        "raw_record_count": raw_count,
        "valid_record_count": valid_count,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Check for MMSE column
    has_mmse = 'MMSE' in df.columns
    metadata['has_mmse'] = has_mmse
    
    metadata_path = Path(config['data_raw_dir']) / 'metadata.json'
    save_metadata(metadata, str(metadata_path))
    
    # Save MMSE flag
    mmse_flag_path = Path(config['data_processed_dir']) / 'mmse_flag.json'
    with open(mmse_flag_path, 'w') as f:
        json.dump({"has_mmse": has_mmse}, f)
    log_info(f"MMSE flag saved to {mmse_flag_path}")
    
    log_info("Data ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()