"""
Save cleaned dataset to data/processed/analysis_data.csv

This script reads the cleaned data from the temporary location (after T012),
validates the required columns, and saves it to the final processed location.
"""
import pandas as pd
import logging
from pathlib import Path
import sys

# Add project root to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config, ensure_directories, get_dataset_url
from logging_config import setup_logging
from exceptions import DataValidationError

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'news_exposure_freq',
    'anxiety_score',
    'baseline_anxiety',
    'age',
    'gender'
]

def load_cleaned_data(input_path: Path) -> pd.DataFrame:
    """
    Load the cleaned data from the intermediate location.
    T012 (clean.py) is expected to have written the cleaned data here.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {input_path}. "
                                "Ensure T012 (clean.py) has been run successfully.")
    
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded cleaned data with {len(df)} rows and {len(df.columns)} columns.")
        return df
    except Exception as e:
        logger.error(f"Failed to load cleaned data from {input_path}: {e}")
        raise

def validate_cleaned_data(df: pd.DataFrame) -> None:
    """
    Validate that the cleaned data contains all required columns
    and that primary predictor/outcome variables are not null.
    """
    # Check required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise DataValidationError(f"Missing required columns: {missing_cols}")
    
    # Check for null values in primary predictor and outcome
    primary_vars = ['news_exposure_freq', 'anxiety_score']
    for var in primary_vars:
        null_count = df[var].isnull().sum()
        if null_count > 0:
            raise DataValidationError(f"Primary variable '{var}' has {null_count} null values. "
                                      "Listwise deletion may have been incomplete.")
    
    logger.info("Cleaned data validation passed.")

def save_cleaned_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the validated cleaned data to the final processed location.
    """
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved cleaned data to {output_path} "
                    f"({len(df)} rows, {len(df.columns)} columns).")
    except Exception as e:
        logger.error(f"Failed to save cleaned data to {output_path}: {e}")
        raise

def main():
    """
    Main entry point for saving the cleaned dataset.
    """
    config = load_config()
    ensure_directories()
    setup_logging()
    
    # Define paths
    # T012 (clean.py) writes to a temporary location or modifies the raw file in place.
    # Based on standard pipeline flow, we assume the cleaned data is available at:
    # data/processed/analysis_data_temp.csv (or similar intermediate step)
    # However, looking at T012 description: "Implement listwise deletion... HALT with PowerLimitationError"
    # It implies the cleaning happens in memory or writes to a temp file before final save.
    # Let's assume T012 writes to 'data/processed/analysis_data_temp.csv' or we read from 'data/raw/' if T012 modified it.
    # To be robust, we check for the most likely intermediate file or the raw file if T012 did in-place.
    # But T013 says "Save cleaned dataset", implying the data is ready to be saved.
    # Let's assume the previous step (T012) left the data in memory or a temp file.
    # Since we are implementing a script, we need a source.
    # Assumption: T012 writes to data/processed/analysis_data_temp.csv
    # If not, we might need to re-run the cleaning logic here or assume the user runs T012 then T013.
    # Given the task flow, T012 likely produces the cleaned dataframe.
    # Let's assume the standard pattern: T012 writes to a temp file, T013 moves/validates/saves to final.
    
    raw_data_path = Path("data/raw")
    processed_dir = Path("data/processed")
    
    # Check for intermediate file created by T012
    # If T012 writes directly to the final path, this script acts as a validator/finalizer.
    # If T012 writes to a temp file, we read from there.
    # Let's assume T012 writes to 'data/processed/analysis_data_cleaned.csv' as an intermediate.
    # Or, more likely, T012 is a script that *should* have run and we are just saving the result.
    # Since T012 is "Implement listwise deletion", it likely outputs to a file.
    # Let's assume the output of T012 is 'data/processed/analysis_data_cleaned.csv'
    # and T013 renames/moves it to 'analysis_data.csv'.
    
    # Alternative: T012 writes to 'data/processed/analysis_data.csv' directly?
    # No, T013 is "Save cleaned dataset", implying T012 did the work but maybe not the final save.
    # Let's assume T012 saves to 'data/processed/analysis_data_temp.csv'
    temp_input_path = processed_dir / "analysis_data_temp.csv"
    final_output_path = processed_dir / "analysis_data.csv"
    
    # Fallback: if temp file doesn't exist, maybe T012 saved directly to final?
    # In that case, we just validate.
    if not temp_input_path.exists():
        if final_output_path.exists():
            logger.warning("Intermediate temp file not found. Assuming T012 already saved to final location. Validating...")
            input_path = final_output_path
        else:
            raise FileNotFoundError("No cleaned data found. Ensure T012 (clean.py) has been run and produced output.")
    else:
        input_path = temp_input_path

    logger.info(f"Loading cleaned data from: {input_path}")
    df = load_cleaned_data(input_path)
    
    logger.info("Validating cleaned data...")
    validate_cleaned_data(df)
    
    logger.info(f"Saving cleaned data to: {final_output_path}")
    save_cleaned_data(df, final_output_path)
    
    # Clean up temp file if it was used
    if input_path == temp_input_path and temp_input_path.exists():
        temp_input_path.unlink()
        logger.info(f"Removed temporary file: {temp_input_path}")

    logger.info("T013 completed successfully.")

if __name__ == "__main__":
    main()
