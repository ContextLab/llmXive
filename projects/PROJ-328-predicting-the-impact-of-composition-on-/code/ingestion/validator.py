"""
Validation logic for the cleaned solder hardness dataset (T014).
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import (
    get_composition_sum_threshold,
    get_data_processed_dir,
    get_max_elements
)
from utils.error_handlers import DataValidationError

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def validate_and_write_status():
    """
    Validate the cleaned data and write the ingestion status.
    
    This task (T014) reads the output of T013 (.ingestion_status.json and solder_hardness_cleaned.csv)
    and performs additional validation checks.
    """
    processed_dir = get_data_processed_dir()
    status_file = processed_dir / '.ingestion_status.json'
    cleaned_file = processed_dir / 'solder_hardness_cleaned.csv'
    excluded_file = processed_dir / 'excluded_records.csv'
    
    # Check if status file exists (produced by T013)
    if not status_file.exists():
        raise FileNotFoundError(f"Status file not found: {status_file}. T013 may not have run successfully.")
    
    # Load status from T013
    with open(status_file, 'r') as f:
        status = json.load(f)
    
    # Load cleaned data
    if not cleaned_file.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {cleaned_file}")
    
    cleaned_df = pd.read_csv(cleaned_file)
    
    # Load excluded records
    excluded_count = 0
    if excluded_file.exists():
        excluded_df = pd.read_csv(excluded_file)
        excluded_count = len(excluded_df)
    
    # Validation checks
    # 1. Check for non-null hardness
    non_null_hardness = cleaned_df['hardness_hv'].notna().sum()
    null_hardness = len(cleaned_df) - non_null_hardness
    
    # 2. Check composition sums
    composition_sum_threshold = get_composition_sum_threshold()
    
    # Identify element columns (numeric, non-metadata)
    metadata_cols = ['alloy_id', 'hardness_hv', 'measurement_temp_c', 'composition_sum', 'element_count', 'source_file']
    element_cols = [col for col in cleaned_df.columns if col not in metadata_cols and pd.api.types.is_numeric_dtype(cleaned_df[col])]
    
    if element_cols:
        # Recalculate composition sum to verify
        calculated_sums = cleaned_df[element_cols].sum(axis=1)
        low_sum_count = (calculated_sums < composition_sum_threshold).sum()
        
        if low_sum_count > 0:
            logger.warning(f"Found {low_sum_count} records with composition sum < {composition_sum_threshold}% in cleaned data!")
            # This should not happen if T013 worked correctly
            raise DataValidationError(f"Validation failed: {low_sum_count} records have low composition sum")
    else:
        logger.warning("No element columns found to validate composition sum.")
    
    # 3. Count non-null hardness
    logger.info(f"Non-null hardness count: {non_null_hardness}/{len(cleaned_df)}")
    
    # 4. Determine threshold status
    exact_n = len(cleaned_df)
    if exact_n >= 100:
        threshold_status = 'N>=100'
        power_warning = None
    elif exact_n >= 50:
        threshold_status = '50<=N<100'
        power_warning = '50 <= N < 100'
    else:
        threshold_status = 'N<50'
        power_warning = 'N < 50'
    
    # Update status
    status['threshold_status'] = threshold_status
    status['exact_N'] = exact_n
    status['excluded_count'] = excluded_count
    status['non_null_hardness'] = non_null_hardness
    if power_warning:
        status['power_limitation_warning'] = power_warning
    
    # Write updated status
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    logger.info(f"Validation complete. Status: {status}")
    return status

def main():
    """Main entry point."""
    logger.info("Starting data validation (T014)")
    try:
        validate_and_write_status()
        logger.info("Validation completed successfully")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

if __name__ == "__main__":
    main()