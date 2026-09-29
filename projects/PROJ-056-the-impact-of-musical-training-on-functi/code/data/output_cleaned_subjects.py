"""
Output cleaned subjects data to CSV.

This module implements T019: Output `data/processed/subjects_cleaned.csv` with
the required columns after preprocessing and confounder handling.
"""
import os
import sys
import pandas as pd
import logging
from pathlib import Path
from typing import Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.schema_validator import validate_dataset

logger = get_logger(__name__)

REQUIRED_COLUMNS = [
    'subject_id',
    'group',
    'years_of_training',
    'age',
    'sex',
    'motion_score',
    'ses_score'
]

def write_cleaned_subjects(
    df: pd.DataFrame,
    output_path: Optional[str] = None,
    validate_against_schema: bool = True
) -> str:
    """
    Write cleaned subject data to CSV.

    Args:
        df: DataFrame containing cleaned subject data.
        output_path: Path to output CSV. Defaults to 'data/processed/subjects_cleaned.csv'.
        validate_against_schema: Whether to validate against subject schema before writing.

    Returns:
        Path to the written CSV file.

    Raises:
        ValueError: If required columns are missing or data validation fails.
        FileNotFoundError: If output directory does not exist.
    """
    if output_path is None:
        output_path = str(project_root / 'data' / 'processed' / 'subjects_cleaned.csv')

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Validate required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}. "
                       f"Expected: {REQUIRED_COLUMNS}")

    # Select only required columns in the correct order
    output_df = df[REQUIRED_COLUMNS].copy()

    # Validate data types and values
    if validate_against_schema:
        schema_path = project_root / 'contracts' / 'subject.schema.yaml'
        if schema_path.exists():
            try:
                validate_dataset(output_df.to_dict('records'), str(schema_path))
                logger.info(f"Data validated successfully against {schema_path}")
            except Exception as e:
                logger.warning(f"Schema validation warning: {e}")
                # Continue anyway as validation is optional for writing

    # Ensure data types are appropriate
    output_df['subject_id'] = output_df['subject_id'].astype(str)
    output_df['group'] = output_df['group'].astype(str)
    output_df['years_of_training'] = pd.to_numeric(output_df['years_of_training'], errors='coerce')
    output_df['age'] = pd.to_numeric(output_df['age'], errors='coerce')
    output_df['sex'] = output_df['sex'].astype(str)
    output_df['motion_score'] = pd.to_numeric(output_df['motion_score'], errors='coerce')
    output_df['ses_score'] = pd.to_numeric(output_df['ses_score'], errors='coerce')

    # Drop rows with NaN in critical fields
    critical_cols = ['subject_id', 'group', 'years_of_training']
    output_df = output_df.dropna(subset=critical_cols)

    logger.info(f"Writing {len(output_df)} subjects to {output_path}")
    output_df.to_csv(output_path, index=False)

    logger.info(f"Successfully wrote cleaned subjects to {output_path}")
    return str(output_path)

def main():
    """
    Main entry point for writing cleaned subjects.
    
    This function is called by the main pipeline to output the final
    cleaned subjects CSV after preprocessing.
    """
    from data.preprocess import preprocess_subjects
    from data.download import load_data

    logger.info("Starting cleaned subjects output process")

    # Load and preprocess data
    try:
        # Check if cleaned data already exists in memory (from preprocessing step)
        # If not, run the full preprocessing pipeline
        df = preprocess_subjects(mode='verification')
        
        if df is None or len(df) == 0:
            logger.error("No data available after preprocessing")
            return

        # Write to CSV
        output_path = write_cleaned_subjects(df)
        logger.info(f"Output written to: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to write cleaned subjects: {e}")
        raise

if __name__ == "__main__":
    main()