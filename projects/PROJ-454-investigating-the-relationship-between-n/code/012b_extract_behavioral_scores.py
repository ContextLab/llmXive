import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import setup_data_flow_logger, get_logger

# Required configuration keys from config.py
# We import the config module to ensure we use the same definitions
from config import get_wcst_variable_name, get_min_age, get_dataset_ids

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger for this module."""
    return get_logger(name)

def load_raw_parquet_files(raw_dir: Path) -> list:
    """
    Load all parquet files from the raw data directory.
    Returns a list of DataFrames.
    """
    parquet_files = list(raw_dir.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {raw_dir}")
    
    dataframes = []
    for file_path in parquet_files:
        try:
            df = pd.read_parquet(file_path)
            dataframes.append(df)
            logging.info(f"Loaded {file_path.name}, shape: {df.shape}")
        except Exception as e:
            logging.error(f"Failed to load {file_path}: {e}")
            raise
    
    return dataframes

def verify_variable_fit(df: pd.DataFrame, wcst_col: str, min_age: int) -> bool:
    """
    Verify that the dataset contains the required WCST column and age data.
    Returns True if valid, False otherwise.
    """
    if wcst_col not in df.columns:
        logging.error(f"Required variable '{wcst_col}' not found in columns: {df.columns.tolist()}")
        return False
    
    if 'age' not in df.columns:
        logging.error("Required variable 'age' not found in columns")
        return False
    
    # Check if any rows meet the age criteria (though we don't filter yet, just verify existence)
    valid_age_rows = df[df['age'] >= min_age]
    if len(valid_age_rows) == 0:
        logging.warning(f"No participants found with age >= {min_age}")
        # We do not return False here, as the dataset might be valid but just have no matching subjects
        # The downstream process will handle empty results.
    
    return True

def extract_behavioral_scores(df: pd.DataFrame, wcst_col: str) -> pd.DataFrame:
    """
    Extract relevant behavioral scores from the dataframe.
    Returns a cleaned DataFrame with participant ID, age, and WCST errors.
    """
    # Ensure participant ID column exists (commonly 'participant_id' or 'sub_id')
    id_col = None
    potential_id_cols = ['participant_id', 'sub_id', 'subject_id', 'id']
    for col in potential_id_cols:
        if col in df.columns:
            id_col = col
            break
    
    if not id_col:
        raise ValueError("Could not identify participant ID column in dataset")
    
    # Select required columns
    required_cols = [id_col, 'age', wcst_col]
    
    # Check for additional covariates if they exist (optional)
    optional_cols = ['education', 'task_accuracy', 'neurological_condition', 'medication']
    available_optional = [c for c in optional_cols if c in df.columns]
    
    cols_to_select = required_cols + available_optional
    
    extracted_df = df[cols_to_select].copy()
    
    # Rename columns for consistency
    rename_map = {id_col: 'participant_id'}
    extracted_df.rename(columns=rename_map, inplace=True)
    
    # Drop rows with NaN in critical columns
    critical_cols = ['participant_id', 'age', wcst_col]
    extracted_df.dropna(subset=critical_cols, inplace=True)
    
    # Ensure age is integer
    extracted_df['age'] = extracted_df['age'].astype(int)
    
    return extracted_df

def extract_and_verify_behavioral_scores():
    """
    Main function to extract behavioral scores from raw parquet files.
    Verifies WCST column existence before extraction.
    Halts with 'DATASET_VARIABLE_MISMATCH' error if WCST column is missing.
    """
    logger = setup_logger("extract_behavioral_scores")
    logger.info("Starting behavioral score extraction")
    
    # Define paths
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    
    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Get configuration
    wcst_var_name = get_wcst_variable_name()
    min_age = get_min_age()
    dataset_ids = get_dataset_ids()
    
    logger.info(f"Expected WCST variable: {wcst_var_name}")
    logger.info(f"Minimum age filter: {min_age}")
    
    # Load raw data
    try:
        dataframes = load_raw_parquet_files(raw_dir)
    except FileNotFoundError as e:
        logger.error(f"Raw data not found: {e}")
        # Check if T012 completed successfully
        raise RuntimeError("Raw data files missing. Ensure T012 (download_data) has completed successfully.") from e
    
    # Concatenate all dataframes
    combined_df = pd.concat(dataframes, ignore_index=True)
    logger.info(f"Combined dataset shape: {combined_df.shape}")
    
    # CRITICAL: Verify WCST column existence (T012b requirement)
    if not verify_variable_fit(combined_df, wcst_var_name, min_age):
        error_msg = f"DATASET_VARIABLE_MISMATCH: Column '{wcst_var_name}' is missing."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Filter by age (as per T012 variable-fit check logic)
    filtered_df = combined_df[combined_df['age'] >= min_age]
    logger.info(f"Participants after age filter (>= {min_age}): {len(filtered_df)}")
    
    # Extract behavioral scores
    try:
        behavioral_df = extract_behavioral_scores(filtered_df, wcst_var_name)
    except ValueError as e:
        logger.error(f"Extraction failed: {e}")
        raise
    
    if behavioral_df.empty:
        logger.warning("No valid behavioral data extracted after filtering.")
    
    # Save to CSV
    output_path = processed_dir / "behavioral_scores.csv"
    behavioral_df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully saved behavioral scores to {output_path}")
    logger.info(f"Output shape: {behavioral_df.shape}")
    logger.info(f"Columns: {behavioral_df.columns.tolist()}")
    
    return output_path

def main():
    """Entry point for the script."""
    try:
        extract_and_verify_behavioral_scores()
        print("Extraction completed successfully.")
    except Exception as e:
        print(f"Extraction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
