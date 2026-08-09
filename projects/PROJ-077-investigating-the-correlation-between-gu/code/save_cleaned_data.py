import os
import sys
import pandas as pd
from pathlib import Path
from config import ensure_directories, INPUT_PATHS, SAMPLE_LIMIT
from logging_config import get_logger, log_provenance, log_warning

logger = get_logger(__name__)

def save_cleaned_dataset(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the cleaned dataset to a CSV file with a header containing column definitions.
    
    Args:
        df: The cleaned pandas DataFrame to save.
        output_path: The path where the cleaned CSV should be saved.
        
    Raises:
        ValueError: If the DataFrame is empty.
        FileNotFoundError: If the output directory does not exist.
    """
    if df.empty:
        msg = "Cannot save cleaned dataset: DataFrame is empty."
        logger.error(msg)
        raise ValueError(msg)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        msg = f"Output directory {output_dir} does not exist. Creating it."
        logger.warning(msg)
        os.makedirs(output_dir, exist_ok=True)

    # Construct header with column definitions
    # Format: # Column Definitions:
    # # <column_name>: <dtype>
    header_lines = ["# Column Definitions:"]
    for col in df.columns:
        dtype = str(df[col].dtype)
        header_lines.append(f"# {col}: {dtype}")
    
    header_text = "\n".join(header_lines)

    # Write the file with the custom header
    # We use a temporary approach: write header, then data without header
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header_text + "\n")
        df.to_csv(f, index=False)

    log_provenance(f"Saved cleaned dataset to {output_path}")
    logger.info(f"Successfully saved cleaned dataset to {output_path} with {len(df)} rows.")

def main() -> None:
    """
    Main entry point for the save_cleaned_data script.
    Expects the cleaned data to be available in memory or a temporary location
    (in a real pipeline, this would be passed from the ingestion pipeline).
    
    For this implementation, we assume the cleaned data is the output of the 
    data ingestion pipeline. Since T012-T014 are marked as completed but their 
    implementation details might vary, we simulate the pipeline execution flow
    by calling the ingestion functions directly if available, or loading from 
    a known intermediate state if the pipeline has already run.
    
    In a full pipeline, this script would be called after data_ingestion.py 
    completes its processing.
    """
    ensure_directories()
    
    logger.info("Starting save_cleaned_data pipeline.")
    
    # Import ingestion functions to get the cleaned data
    # This assumes T011-T014 have been executed and the data is ready
    try:
        from data_ingestion import run_ingestion_pipeline
        logger.info("Running data ingestion pipeline to obtain cleaned data.")
        cleaned_df = run_ingestion_pipeline()
    except Exception as e:
        # Fallback: try to load from a standard intermediate path if ingestion failed
        # This handles cases where ingestion was run separately
        intermediate_path = INPUT_PATHS.get('processed', {}).get('intermediate', 'data/processed/intermediate_cleaned.csv')
        if os.path.exists(intermediate_path):
            logger.warning(f"Ingestion pipeline failed ({e}). Loading from intermediate file: {intermediate_path}")
            cleaned_df = pd.read_csv(intermediate_path)
        else:
            logger.error("Could not obtain cleaned data. Neither ingestion pipeline nor intermediate file available.")
            sys.exit(1)

    if cleaned_df is None or cleaned_df.empty:
        logger.error("Cleaned data is empty. Cannot proceed with saving.")
        sys.exit(1)

    output_path = INPUT_PATHS.get('processed', {}).get('cleaned', 'data/processed/cleaned_data.csv')
    
    try:
        save_cleaned_dataset(cleaned_df, output_path)
    except Exception as e:
        logger.error(f"Failed to save cleaned dataset: {e}")
        sys.exit(1)

    logger.info("save_cleaned_data pipeline completed successfully.")

if __name__ == "__main__":
    main()
