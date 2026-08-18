import os
import sys
import logging
from typing import Dict, Any, Optional
import pandas as pd
from datasets import load_dataset

# Ensure sibling imports work in the project context
try:
    from utils.logging_config import get_logger, log_info_with_context, log_warning_with_context, log_error_with_context
except ImportError:
    # Fallback for direct execution if path not set up
    import code.utils.logging_config as lc
    get_logger = lc.get_logger
    log_info_with_context = lc.log_info_with_context
    log_warning_with_context = lc.log_warning_with_context
    log_error_with_context = lc.log_error_with_context

logger = get_logger(__name__)

def load_oqmd_data(dataset_name: str = "OQMD/elastic_properties", streaming: bool = False) -> pd.DataFrame:
    """
    Fetches OQMD elastic properties data from HuggingFace.
    
    Args:
        dataset_name: The HuggingFace dataset identifier.
        streaming: If True, streams the dataset to save memory.
        
    Returns:
        A pandas DataFrame containing the raw dataset.
    """
    log_info_with_context(f"Loading dataset: {dataset_name}", logger)
    try:
        if streaming:
            dataset = load_dataset(dataset_name, split="train", streaming=True)
            # Convert streaming to DF by iterating (efficient for large data)
            # Note: For very large datasets, this might be slow, but ensures real data fetch.
            # We will load a reasonable chunk or all if feasible. 
            # To ensure robustness, we load into DF. If memory is an issue, 
            # the caller should handle chunking logic or use streaming directly in filter.
            # For this implementation, we assume the dataset fits in memory or we stream row-by-row.
            # Given the constraint "Large dataset? Stream the real data", we iterate.
            records = []
            for item in dataset:
                records.append(item)
                if len(records) % 10000 == 0:
                    log_info_with_context(f"Fetched {len(records)} rows...", logger)
            df = pd.DataFrame(records)
        else:
            dataset = load_dataset(dataset_name, split="train")
            df = dataset.to_pandas()
        
        log_info_with_context(f"Successfully loaded {len(df)} rows from {dataset_name}", logger)
        return df
    except Exception as e:
        log_error_with_context(f"Failed to load dataset: {e}", logger)
        raise

def filter_valid_entries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters the dataframe for entries with valid Bulk and Shear Moduli.
    Specifically: bulk_modulus > 0 and shear_modulus > 0.
    Excludes rows with missing data in these columns.
    
    Args:
        df: The raw DataFrame.
        
    Returns:
        Filtered DataFrame.
    """
    log_info_with_context("Filtering for valid Bulk and Shear Moduli entries...", logger)
    
    required_cols = ['bulk_modulus', 'shear_modulus']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}")
    
    initial_count = len(df)
    
    # Filter for non-null and positive values
    mask = (df['bulk_modulus'].notna()) & (df['shear_modulus'].notna()) & \
           (df['bulk_modulus'] > 0) & (df['shear_modulus'] > 0)
    
    filtered_df = df[mask].copy()
    final_count = len(filtered_df)
    
    log_info_with_context(f"Initial rows: {initial_count}, Valid rows: {final_count}", logger)
    log_info_with_context(f"Filtered out {initial_count - final_count} invalid or missing entries.", logger)
    
    return filtered_df

def save_processed_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Saves the processed DataFrame to a CSV file.
    
    Args:
        df: The DataFrame to save.
        output_path: The destination path.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    log_info_with_context(f"Saved processed data to {output_path} ({len(df)} rows)", logger)

def main():
    """
    Main entry point for data ingestion.
    Orchestrates loading, filtering, and logging counts.
    """
    # Configuration
    dataset_name = "OQMD/elastic_properties"
    output_path = "data/processed/encoded_alloys.csv" # Placeholder path, actual encoding happens later
    # Note: T012/T013 produce the final CSV. T017 adds logging to T012's logic.
    # We will output to a temporary processed file for this step or the final one if combined.
    # Per tasks.md, T015 creates the final CSV. T012 produces intermediate.
    # Let's save to data/processed/ingested_raw.csv for this step.
    intermediate_output = "data/processed/ingested_raw.csv"
    
    log_info_with_context("Starting Data Ingestion Pipeline", logger)
    
    try:
        # 1. Load
        # Stream if necessary to handle large datasets without OOM
        raw_df = load_oqmd_data(dataset_name, streaming=True)
        total_fetched = len(raw_df)
        
        # 2. Filter
        valid_df = filter_valid_entries(raw_df)
        valid_count = len(valid_df)
        
        # 3. Save (Intermediate step before encoding)
        save_processed_data(valid_df, intermediate_output)
        encoded_count = valid_count # In this step, encoding is separate, but we count valid entries as "to be encoded"
        
        # 4. Log Counts (T017 Requirement)
        log_info_with_context(f"--- Data Ingestion Summary ---", logger)
        log_info_with_context(f"Total Fetched: {total_fetched}", logger)
        log_info_with_context(f"Filtered (Valid): {valid_count}", logger)
        log_info_with_context(f"Encoded (Ready for encoding): {encoded_count}", logger)
        log_info_with_context(f"-----------------------------", logger)
        
        # Check for minimum data requirement (T014 logic integration)
        if encoded_count < 500:
            log_warning_with_context(f"Insufficient data for statistical analysis (N < 500). Found: {encoded_count}", logger)
            # Exit with 0 as per T014 spec (graceful exit with warning)
            sys.exit(0)
        
        log_info_with_context("Data ingestion completed successfully.", logger)
        
    except Exception as e:
        log_error_with_context(f"Pipeline failed: {e}", logger)
        sys.exit(1)

if __name__ == "__main__":
    main()