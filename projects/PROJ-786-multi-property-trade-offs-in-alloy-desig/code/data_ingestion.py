import os
import sys
import logging
from typing import Dict, Any, Optional
import pandas as pd
from datasets import load_dataset

from utils.logging_config import log_info_with_context, log_warning_with_context, log_error_with_context

logger = logging.getLogger(__name__)

def load_oqmd_data(dataset_name: str = "OQMD/elastic_properties") -> Optional[pd.DataFrame]:
    """
    Fetches OQMD data via HuggingFace datasets.
    """
    log_info_with_context(f"Loading dataset: {dataset_name}", context="ingestion")
    try:
        # Load the dataset
        dataset = load_dataset(dataset_name, split="train")
        df = dataset.to_pandas()
        log_info_with_context(f"Loaded {len(df)} records from {dataset_name}", context="ingestion")
        return df
    except Exception as e:
        log_error_with_context(f"Failed to load dataset: {e}", context="ingestion")
        # Fail loudly as per constraints
        raise RuntimeError(f"Failed to load real data from {dataset_name}: {e}")

def filter_valid_entries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters entries for valid Bulk and Shear Moduli (> 0) and no missing data in key columns.
    """
    log_info_with_context("Filtering valid entries", context="ingestion")
    
    key_cols = ['composition', 'bulk_modulus', 'shear_modulus']
    
    # Check for missing columns
    missing_cols = [c for c in key_cols if c not in df.columns]
    if missing_cols:
        log_error_with_context(f"Missing required columns: {missing_cols}", context="ingestion")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Filter for non-null and positive values
    mask = (
        df['bulk_modulus'].notna() & 
        df['shear_modulus'].notna() & 
        df['bulk_modulus'] > 0 & 
        df['shear_modulus'] > 0
    )
    
    df_filtered = df[mask].reset_index(drop=True)
    
    total_fetched = len(df)
    filtered_count = len(df_filtered)
    
    log_info_with_context(f"Filtered data: {total_fetched} -> {filtered_count}", context="ingestion")
    
    return df_filtered

def save_processed_data(df: pd.DataFrame, output_path: str):
    """Saves the processed dataframe to CSV."""
    df.to_csv(output_path, index=False)
    log_info_with_context(f"Saved processed data to {output_path}", context="ingestion")

def main():
    # Standalone execution
    pass
