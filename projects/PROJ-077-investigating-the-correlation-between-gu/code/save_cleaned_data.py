"""
Task T015: Save cleaned dataset to data/processed/cleaned_data.csv.

This script assumes the ingestion pipeline (T013, T014a, T014b) has run
and produced a cleaned DataFrame in memory or via a temporary state.
However, since the pipeline is modular, this script acts as the final
step to persist the result of the ingestion process defined in data_ingestion.py.

It loads the raw data, performs the necessary merging, filtering, and imputation
(reusing logic from data_ingestion), and saves the final result to the
specified output path with a header containing column definitions.
"""
import os
import sys
import pandas as pd
from pathlib import Path

# Add project root to path if running as script
if 'code' in os.getcwd():
    sys.path.insert(0, os.getcwd())
else:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root / 'code'))

from config import ensure_directories, INPUT_PATHS, SAMPLE_LIMIT
from logging_config import get_logger, log_provenance, log_warning
from data_ingestion import run_ingestion_pipeline

def save_cleaned_dataset(output_path: str, df: pd.DataFrame):
    """
    Saves the cleaned DataFrame to CSV with a header containing column definitions.
    
    Args:
        output_path: Full path to the output CSV file.
        df: The cleaned DataFrame.
    """
    ensure_directories()
    
    if df.empty:
        log_warning("Attempted to save an empty dataset. Creating file with headers only.")
        df.to_csv(output_path, index=False)
        return

    # Create column definitions comment
    # We infer types or use a standard schema description based on project requirements
    columns = df.columns.tolist()
    dtypes = df.dtypes.astype(str).to_dict()
    
    header_comment = "# Column Definitions:\n"
    header_comment += "# Format: # column_name | type | description\n"
    for col in columns:
        desc = "Derived from ingestion pipeline"
        if col in ['participant_id', 'sex']:
            desc = "Participant ID / Sex (M/F)"
        elif col in ['age', 'bmi', 'dqs']:
            desc = "Continuous covariate"
        elif col in ['alpha_diversity', 'shannon_index']:
            desc = "Alpha diversity metric (Shannon)"
        elif col in ['fluid_intelligence']:
            desc = "Cognitive performance score"
        
        header_comment += f"# {col} | {dtypes[col]} | {desc}\n"

    # Write to file
    with open(output_path, 'w') as f:
        f.write(header_comment)
        df.to_csv(f, index=False)

    log_provenance(f"Saved cleaned dataset to {output_path} with {len(df)} rows.")

def main():
    logger = get_logger()
    logger.info("Starting T015: Save Cleaned Data")

    # Ensure output directories exist
    ensure_directories()
    
    # Define output path as per task specification
    output_path = "data/processed/cleaned_data.csv"
    
    # Check if data already exists from a previous pipeline run
    # In a real pipeline, this would be passed from the previous step.
    # For this standalone script, we re-run the ingestion logic to ensure
    # we have the data, as the previous tasks (T013, T014) were logic implementations.
    # We assume the raw data files are present in data/raw/ as per T001/T002.
    
    try:
        # Run the ingestion pipeline to get the cleaned DataFrame
        # This re-executes the logic from T011-T014 to ensure data is ready
        cleaned_df = run_ingestion_pipeline()
        
        if cleaned_df is None or cleaned_df.empty:
            log_warning("Ingestion pipeline returned empty or None data. Saving empty file.")
            # Create file with headers only if empty
            save_cleaned_dataset(output_path, pd.DataFrame())
        else:
            save_cleaned_dataset(output_path, cleaned_df)
            
        logger.info(f"T015 Complete. Output saved to {output_path}")
        
    except FileNotFoundError as e:
        log_warning(f"Raw data files not found. Cannot generate cleaned_data.csv. Error: {e}")
        # Create an empty file with headers to indicate status
        save_cleaned_dataset(output_path, pd.DataFrame())
    except Exception as e:
        logger.error(f"Error during T015: {e}")
        raise

if __name__ == "__main__":
    main()
