import os
import sys
import logging
from typing import Dict, Any, Optional
import pandas as pd
from datasets import load_dataset

from utils.logging_config import get_logger, log_info_with_context, log_warning_with_context, log_error_with_context

logger = get_logger(__name__)

def load_oqmd_data() -> pd.DataFrame:
    """
    Fetches OQMD elastic properties data from HuggingFace.
    Returns a DataFrame containing the raw dataset.
    """
    log_info_with_context(logger, "Loading OQMD dataset from HuggingFace", {"dataset": "OQMD/elastic_properties"})
    try:
        # Using streaming to handle potential large size, though we filter immediately
        dataset = load_dataset('OQMD/elastic_properties', split='train', streaming=True)
        
        # Convert to pandas to allow filtering and column access
        # We iterate to ensure we have the data structure we expect
        rows = []
        for item in dataset:
            rows.append(item)
            # Stop early if we have enough to verify structure, but for full ingestion
            # we would iterate all. For this task, we load all available to count.
        
        df = pd.DataFrame(rows)
        log_info_with_context(logger, f"Successfully loaded OQMD data", {"total_rows": len(df)})
        return df
    except Exception as e:
        log_error_with_context(logger, f"Failed to load OQMD dataset: {str(e)}", {"error_type": type(e).__name__})
        raise

def filter_valid_entries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters the DataFrame to keep only entries with valid Bulk and Shear Moduli.
    Criteria: bulk_modulus > 0 AND shear_modulus > 0.
    Also drops rows with any missing values in key columns.
    """
    log_info_with_context(logger, "Filtering valid entries", {"initial_count": len(df)})
    
    key_columns = ['bulk_modulus', 'shear_modulus']
    
    # Ensure columns exist
    missing_cols = [col for col in key_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")
    
    # Filter for positive values
    valid_mask = (df['bulk_modulus'] > 0) & (df['shear_modulus'] > 0)
    filtered_df = df[valid_mask].copy()
    
    # Drop rows with any NaN in key columns (safety check)
    filtered_df = filtered_df.dropna(subset=key_columns)
    
    filtered_count = len(filtered_df)
    log_info_with_context(logger, "Filtering complete", {
        "initial_count": len(df),
        "filtered_count": filtered_count,
        "removed_count": len(df) - filtered_count
    })
    
    return filtered_df

def save_processed_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Saves the processed DataFrame to a CSV file.
    """
    log_info_with_context(logger, "Saving processed data", {"path": output_path})
    df.to_csv(output_path, index=False)
    log_info_with_context(logger, "Data saved successfully", {"path": output_path, "rows": len(df)})

def main() -> int:
    """
    Main entry point for data ingestion.
    Orchestrates loading, filtering, and saving.
    Implements T017: Logging for data ingestion counts.
    """
    try:
        # 1. Load Data
        raw_df = load_oqmd_data()
        total_fetched = len(raw_df)
        
        # 2. Filter Data
        valid_df = filter_valid_entries(raw_df)
        filtered_count = len(valid_df)
        
        # 3. Prepare for Encoding (Select columns needed for encoding)
        # Assuming composition column exists; if not, we might need to adjust based on dataset schema
        # For OQMD elastic, typically 'composition' or similar string exists.
        # We prepare the dataframe for the next step.
        encoded_count = filtered_count # In this pipeline, encoding is a separate step, so count passes through
        
        # 4. Log Counts (T017 Requirement)
        log_info_with_context(logger, "Data Ingestion Summary", {
            "total_fetched": total_fetched,
            "filtered_valid": filtered_count,
            "ready_for_encoding": encoded_count
        })
        
        # 5. Check minimum threshold (US-1 Acceptance 1)
        if filtered_count < 500:
            log_warning_with_context(logger, "Insufficient data for statistical analysis (N < 500)", {
                "current_count": filtered_count,
                "required_minimum": 500
            })
            # Exit gracefully as per task description
            return 0
        
        # 6. Save Processed Data
        output_dir = "data/processed"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "raw_validated.csv") # Intermediate step before encoding
        
        # Note: The task T015 mentions saving to encoded_alloys.csv, but that requires the encoder.
        # We save the validated raw data here, which the encoder will consume.
        save_processed_data(valid_df, output_path)
        
        return 0
        
    except Exception as e:
        log_error_with_context(logger, f"Ingestion pipeline failed: {str(e)}", {"error_type": type(e).__name__})
        return 1

if __name__ == "__main__":
    sys.exit(main())