"""
Module to save the cleaned dataset to disk.

This script takes the processed DataFrame from the data ingestion pipeline
and writes it to `data/processed/cleaned_data.csv` with a header containing
column definitions.

Dependencies:
- code/config.py: ensure_directories, INPUT_PATHS
- code/logging_config.py: get_logger, log_provenance, log_warning
- code/data_ingestion.py: run_ingestion_pipeline (to get the cleaned data)
"""
import os
import sys
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from config import ensure_directories, INPUT_PATHS, SAMPLE_LIMIT
from logging_config import get_logger, log_provenance, log_warning
from data_ingestion import run_ingestion_pipeline

logger = get_logger(__name__)

def save_cleaned_dataset(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the cleaned DataFrame to a CSV file with column definitions in the header.
    
    Args:
        df: The cleaned DataFrame to save.
        output_path: The path where the CSV file will be saved.
        
    Raises:
        ValueError: If the DataFrame is empty.
        IOError: If the file cannot be written.
    """
    if df.empty:
        msg = "Cannot save cleaned dataset: DataFrame is empty."
        logger.error(msg)
        raise ValueError(msg)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        ensure_directories([output_dir])
    
    # Create a header with column definitions
    # We will prepend a comment line with column info
    header_info = [
        "# Column Definitions:",
        f"# - Total rows: {len(df)}",
        f"# - Total columns: {len(df.columns)}",
        "# Columns:"
    ]
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null = df[col].notna().sum()
        null_count = len(df) - non_null
        header_info.append(f"#   - {col} (dtype: {dtype}, non-null: {non_null}, null: {null_count})")
    
    # Write the file
    try:
        # Write header comments first
        with open(output_path, 'w') as f:
            for line in header_info:
                f.write(line + '\n')
        
        # Append the CSV data without the index
        df.to_csv(output_path, mode='a', index=False)
        
        logger.info(f"Successfully saved cleaned dataset to {output_path}")
        log_provenance(f"Saved cleaned dataset to {output_path} with {len(df)} rows and {len(df.columns)} columns.")
        
    except Exception as e:
        msg = f"Failed to save cleaned dataset to {output_path}: {str(e)}"
        logger.error(msg)
        raise IOError(msg) from e

def main():
    """
    Main entry point for the save cleaned data pipeline.
    
    This function:
    1. Runs the data ingestion pipeline to get the cleaned DataFrame.
    2. Saves the cleaned DataFrame to `data/processed/cleaned_data.csv`.
    """
    logger.info("Starting save_cleaned_data pipeline.")
    
    # Define output path
    output_path = "data/processed/cleaned_data.csv"
    
    try:
        # Run the ingestion pipeline to get the cleaned data
        # This assumes T011, T012, T013, T014a, T014b, T014c are complete
        cleaned_df = run_ingestion_pipeline()
        
        if cleaned_df is None:
            msg = "Data ingestion pipeline returned None. Cannot save cleaned dataset."
            logger.error(msg)
            raise RuntimeError(msg)
        
        # Save the cleaned dataset
        save_cleaned_dataset(cleaned_df, output_path)
        
        logger.info("Save cleaned data pipeline completed successfully.")
        
    except Exception as e:
        msg = f"Error in save_cleaned_data pipeline: {str(e)}"
        logger.error(msg)
        log_warning(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()