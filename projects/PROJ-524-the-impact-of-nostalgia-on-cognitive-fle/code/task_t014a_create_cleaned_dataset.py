"""
Task T014a: Generate Cleaned Dataset

Reads the intermediate cleaned dataset (produced by T012e) and creates
the final cleaned dataset by selecting specific columns and saving to
the designated output path.

Columns to include:
- participant_id
- stimulus_type (nostalgia/control)
- perseverative_errors
- categories_completed
- age

Output: data/processed/final_cleaned_dataset.csv
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_dataset.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "final_cleaned_dataset.csv"
EXCLUSION_LOG_PATH = PROJECT_ROOT / "data" / "processed" / "exclusion_log.json"
MMSE_FLAG_PATH = PROJECT_ROOT / "data" / "processed" / "mmse_flag.json"

# Required columns for the final dataset
REQUIRED_COLUMNS = [
    'participant_id',
    'stimulus_type',
    'perseverative_errors',
    'categories_completed',
    'age'
]

def load_exclusion_log() -> Optional[Dict[str, Any]]:
    """Load the exclusion log if it exists."""
    if not EXCLUSION_LOG_PATH.exists():
        logger.warning(f"Exclusion log not found at {EXCLUSION_LOG_PATH}. Proceeding without it.")
        return None
    
    try:
        with open(EXCLUSION_LOG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load exclusion log: {e}")
        return None

def load_mmse_flag() -> bool:
    """Load the MMSE flag to determine if MMSE data was present."""
    if not MMSE_FLAG_PATH.exists():
        logger.warning(f"MMSE flag not found at {MMSE_FLAG_PATH}. Assuming MMSE was not present.")
        return False
    
    try:
        with open(MMSE_FLAG_PATH, 'r') as f:
            data = json.load(f)
            return data.get('has_mmse', False)
    except Exception as e:
        logger.error(f"Failed to load MMSE flag: {e}")
        return False

def load_intermediate_dataset() -> pd.DataFrame:
    """Load the intermediate cleaned dataset."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Ensure T012e has been completed successfully."
        )
    
    logger.info(f"Loading intermediate dataset from {INPUT_PATH}")
    df = pd.read_csv(INPUT_PATH)
    logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
    return df

def create_cleaned_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create the final cleaned dataset by selecting required columns.
    
    Args:
        df: The intermediate cleaned dataset
        
    Returns:
        DataFrame with only the required columns
    """
    # Check if all required columns exist
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in input dataset: {missing_cols}. "
            f"Available columns: {list(df.columns)}"
        )
    
    # Select only the required columns
    final_df = df[REQUIRED_COLUMNS].copy()
    
    # Log data types for verification
    logger.info(f"Final dataset dtypes:\n{final_df.dtypes}")
    
    # Log basic statistics
    logger.info(f"Final dataset shape: {final_df.shape}")
    logger.info(f"Stimulus type distribution:\n{final_df['stimulus_type'].value_counts()}")
    
    return final_df

def save_cleaned_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Save the final cleaned dataset to CSV."""
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Saved final cleaned dataset to {output_path}")
        logger.info(f"Output file size: {output_path.stat().st_size} bytes")
        
    except Exception as e:
        logger.error(f"Failed to save cleaned dataset: {e}")
        raise

def main():
    """Main entry point for T014a."""
    logger.info("Starting T014a: Generate Cleaned Dataset")
    
    try:
        # Load intermediate dataset
        df = load_intermediate_dataset()
        
        # Create final cleaned dataset
        final_df = create_cleaned_dataset(df)
        
        # Save the final dataset
        save_cleaned_dataset(final_df, OUTPUT_PATH)
        
        # Verify the output
        if OUTPUT_PATH.exists():
            final_df_verify = pd.read_csv(OUTPUT_PATH)
            logger.info(f"Verification: Output contains {len(final_df_verify)} records")
            logger.info(f"Verification: Columns = {list(final_df_verify.columns)}")
            
            # Check for nulls in critical columns
            null_counts = final_df_verify[REQUIRED_COLUMNS].isnull().sum()
            if null_counts.any():
                logger.warning(f"Null values found in output:\n{null_counts[null_counts > 0]}")
            else:
                logger.info("Verification: No null values in required columns")
            
            logger.info("T014a completed successfully!")
            return 0
        else:
            logger.error("Output file was not created despite no exceptions")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
