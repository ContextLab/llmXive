import os
import sys
import logging
from typing import Dict, Any, Optional
import pandas as pd
from datasets import load_dataset

from config import get_config, verify_config, data_source
from utils.logging_config import log_info_with_context, log_warning_with_context, log_error_with_context

logger = logging.getLogger(__name__)

def load_oqmd_data(dataset_name: Optional[str] = None) -> pd.DataFrame:
    """
    Fetches OQMD data via HuggingFace datasets.
    Falls back to the configured data source if none provided.
    """
    ds_name = dataset_name or data_source
    log_info_with_context(f"Loading dataset: {ds_name}", context="data_ingestion")
    
    try:
        # Load the dataset from HuggingFace
        dataset = load_dataset(ds_name, split="train", streaming=True)
        
        # Convert streaming dataset to DataFrame
        # Since streaming yields rows one by one, we collect them
        df_list = []
        for row in dataset:
            df_list.append(row)
        
        df = pd.DataFrame(df_list)
        log_info_with_context(f"Successfully loaded {len(df)} rows", context="data_ingestion")
        return df
    except Exception as e:
        log_error_with_context(f"Failed to load dataset {ds_name}: {str(e)}", context="data_ingestion")
        raise

def filter_valid_entries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters entries to keep only those with valid bulk_modulus and shear_modulus > 0.
    Excludes missing data.
    """
    required_cols = ["bulk_modulus", "shear_modulus", "composition"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Filter for valid moduli
    mask = (df["bulk_modulus"] > 0) & (df["shear_modulus"] > 0)
    filtered_df = df[mask].dropna(subset=required_cols)
    
    log_info_with_context(
        f"Filtered data: {len(df)} -> {len(filtered_df)} valid entries",
        context="data_ingestion"
    )
    return filtered_df

def save_processed_data(df: pd.DataFrame, output_path: str):
    """Saves the processed DataFrame to CSV."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    df.to_csv(output_path, index=False)
    log_info_with_context(f"Saved processed data to {output_path}", context="data_ingestion")

def main():
    """Main entry point for data ingestion."""
    config = get_config()
    verify_config(config)
    
    raw_data_path = config.get("raw_data_path", "data/raw/oqmd_data.csv")
    processed_dir = config.get("processed_dir", "data/processed")
    output_path = os.path.join(processed_dir, "encoded_alloys.csv")
    
    # Ensure output directory exists
    os.makedirs(processed_dir, exist_ok=True)
    
    try:
        # Load data
        df = load_oqmd_data()
        
        # Filter valid entries
        valid_df = filter_valid_entries(df)
        
        # Check minimum row count
        if len(valid_df) < 500:
            log_warning_with_context(
                f"Insufficient data for statistical analysis (N < 500). Found {len(valid_df)} rows.",
                context="data_ingestion"
            )
            # Still save what we have, but exit with code 0 as per contract
            save_processed_data(valid_df, output_path)
            return 0
        
        # Save processed data
        save_processed_data(valid_df, output_path)
        log_info_with_context("Data ingestion completed successfully", context="data_ingestion")
        return 0
        
    except Exception as e:
        log_error_with_context(f"Data ingestion failed: {str(e)}", context="data_ingestion")
        return 1

if __name__ == "__main__":
    sys.exit(main())
