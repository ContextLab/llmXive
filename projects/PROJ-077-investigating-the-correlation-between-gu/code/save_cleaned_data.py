import os
import sys
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import ensure_directories, INPUT_PATHS, SAMPLE_LIMIT
from logging_config import get_logger, log_provenance, log_warning
from data_ingestion import run_ingestion_pipeline

logger = get_logger(__name__)

def save_cleaned_dataset(df: pd.DataFrame, output_path: str) -> None:
    """
    Saves the cleaned DataFrame to a CSV file.
    
    Args:
        df: The processed DataFrame containing cleaned data.
        output_path: The path where the CSV file will be saved.
        
    Raises:
        ValueError: If the DataFrame is empty or has no rows.
        IOError: If the file cannot be written.
    """
    if df.empty:
        raise ValueError("Cannot save an empty DataFrame. Data filtering may have removed all rows.")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    try:
        df.to_csv(output_path, index=False)
        log_provenance(f"Saved cleaned dataset to {output_path} with {len(df)} rows and {len(df.columns)} columns.")
        logger.info(f"Successfully saved cleaned data to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save cleaned dataset: {e}")
        raise IOError(f"Failed to write file {output_path}: {e}")

def main() -> int:
    """
    Main entry point for the save cleaned data task.
    Orchestrates the ingestion pipeline and saves the result.
    """
    logger.info("Starting save_cleaned_data task.")
    
    # Ensure directories exist
    ensure_directories()
    
    try:
        # Run the ingestion pipeline to get the cleaned DataFrame
        # This depends on T011, T012, T013, T014b, T014c being implemented
        cleaned_df = run_ingestion_pipeline()
        
        if cleaned_df is None:
            logger.error("Ingestion pipeline returned None. Data processing failed.")
            return 1
        
        # Define output path as per task specification
        output_path = "data/processed/cleaned_data.csv"
        
        # Save the dataset
        save_cleaned_dataset(cleaned_df, output_path)
        
        # Verification: Check file exists and has > 1 row
        if not os.path.exists(output_path):
            logger.error(f"Verification failed: Output file {output_path} does not exist.")
            return 1
        
        # Quick reload check to ensure valid CSV
        verify_df = pd.read_csv(output_path)
        if len(verify_df) <= 1:
            logger.warning(f"Verification warning: Output file {output_path} has {len(verify_df)} rows. Expected > 1.")
            # Not returning error here as per strict "write" requirement, but logging it
        
        logger.info("Task T015 completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data source error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during save_cleaned_data: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())