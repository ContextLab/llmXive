import os
import sys
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import ensure_directories, INPUT_PATHS, SAMPLE_LIMIT
from logging_config import get_logger, log_provenance, log_warning

logger = get_logger(__name__)

def save_cleaned_dataset(df: pd.DataFrame, output_path: str = "data/processed/cleaned_data.csv") -> None:
    """
    Writes the processed DataFrame to a CSV file at the specified output path.
    
    Parameters
    ----------
    df : pd.DataFrame
        The cleaned and processed DataFrame to save.
    output_path : str
        The relative path where the CSV file will be written.
        
    Raises
    ------
    ValueError
        If the DataFrame is empty.
    FileNotFoundError
        If the output directory cannot be created.
    """
    if df.empty:
        logger.error("Attempted to save an empty DataFrame.")
        raise ValueError("Cannot save an empty DataFrame. Check previous ingestion steps.")
    
    # Ensure the output directory exists
    output_dir = Path(output_path).parent
    ensure_directories([str(output_dir)])
    
    # Add a header comment with column definitions as a row before the data if desired,
    # but standard CSV practice usually implies the header row IS the definitions.
    # The task asks for "a header containing column definitions". 
    # We will write the standard CSV header which defines the columns.
    # If a custom comment header is strictly required beyond standard headers, 
    # we would prepend it, but standard pandas to_csv with index=False satisfies 
    # the requirement of writing the header with column names.
    
    logger.info(f"Saving cleaned dataset to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Log provenance
    log_provenance(f"Saved cleaned dataset to {output_path} with {len(df)} rows and {len(df.columns)} columns")
    logger.info(f"Successfully saved {len(df)} rows to {output_path}")

def main():
    """
    Entry point for the script.
    Expects the cleaned data to be available in the pipeline state or passed via arguments.
    For this implementation, we assume the data is passed or loaded from a standard intermediate location
    if this script is run as a standalone step in the pipeline.
    
    However, looking at the task T015, it says "Write the processed DataFrame". 
    In a modular pipeline, this script is likely called by `code/main.py` or `code/data_ingestion.py`.
    To make it runnable as a script (as per constraint 8), we need a mechanism to get the data.
    Since T015 is part of the ingestion flow, we will assume the data is passed via a temporary file
    or we load it from the standard ingestion output if we were to chain them.
    
    Given the constraints of a standalone execution for verification, we will check if a temporary
    processed file exists or raise a clear error if data is missing, ensuring we don't fabricate.
    
    Actually, looking at the existing API, `code/data_ingestion.py` has `run_ingestion_pipeline`.
    The most robust way to satisfy "run as python code/save_cleaned_data.py" without fabricating data
    is to expect the data to be loaded from the ingestion step if we were to integrate them,
    OR to expect a specific input file.
    
    Let's assume the pipeline logic in `main.py` handles the data flow and calls this function.
    But to make this script executable and produce the output as requested:
    We will implement a simple check: if `data/processed/cleaned_data.csv` already exists, skip.
    If not, we need the source data. 
    
    Since T015 is "Save cleaned dataset", and T014c/T013 produce the data in memory in `data_ingestion.py`,
    the most realistic standalone execution for this specific task file is to assume it is called
    with the DataFrame or that the data is in a standard intermediate location.
    
    However, the prompt says: "Every artifact-producing script must... actually WRITE its declared output".
    If I run `python code/save_cleaned_data.py`, it needs data.
    The data comes from `code/data_ingestion.py`.
    I will modify this script to import and run the ingestion pipeline up to the point of saving,
    OR assume the user has run the ingestion and the data is in a temp file.
    
    Better approach for a standalone script in this context:
    Import `run_ingestion_pipeline` from `data_ingestion` and run it, then save.
    This ensures the data is real and not fabricated.
    """
    logger.info("Starting save_cleaned_data task.")
    
    # Ensure directories exist
    ensure_directories()
    
    try:
        from data_ingestion import run_ingestion_pipeline
        # Run the ingestion pipeline to get the cleaned dataframe
        cleaned_df = run_ingestion_pipeline()
        if cleaned_df is None or cleaned_df.empty:
            raise ValueError("Ingestion pipeline returned empty or None data.")
        
        save_cleaned_dataset(cleaned_df)
        print(f"Successfully saved cleaned data to data/processed/cleaned_data.csv")
        
    except ImportError as e:
        logger.error(f"Could not import ingestion pipeline: {e}")
        print("Error: Could not import data ingestion pipeline. Ensure data_ingestion.py is correct.")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"Data source file missing: {e}")
        print(f"Error: Required data file missing. {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to save cleaned dataset: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
