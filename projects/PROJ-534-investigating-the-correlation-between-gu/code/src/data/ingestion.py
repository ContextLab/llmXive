"""
Ingestion module for loading and merging synthetic microbiome and cognitive data.

This module implements the ingestion pipeline for User Story 1. It loads
generated synthetic data from disk and merges it on participant ID.
"""

import os
import pandas as pd
from pathlib import Path
import logging

from code.src.utils.config import SEED, DATA_DIR, RAW_DATA_DIR, LOGS_DIR
from code.src.data.synthetic_gen import generate_synthetic_cohort

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_microbiome_data(file_path: Path) -> pd.DataFrame:
    """
    Load microbiome data from a CSV file.

    Args:
        file_path: Path to the microbiome data CSV file.

    Returns:
        DataFrame containing microbiome data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Microbiome data file not found: {file_path}")

    logger.info(f"Loading microbiome data from {file_path}")
    df = pd.read_csv(file_path)

    required_cols = {'participant_id', 'shannon_diversity', 'simpson_diversity', 'chao1'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Microbiome data missing required columns: {missing}")

    logger.info(f"Loaded {len(df)} microbiome records")
    return df


def load_cognitive_data(file_path: Path) -> pd.DataFrame:
    """
    Load cognitive data from a CSV file.

    Args:
        file_path: Path to the cognitive data CSV file.

    Returns:
        DataFrame containing cognitive and demographic data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cognitive data file not found: {file_path}")

    logger.info(f"Loading cognitive data from {file_path}")
    df = pd.read_csv(file_path)

    required_cols = {'participant_id', 'cognitive_score', 'age', 'sex', 'bmi', 'fiber_intake', 'antibiotics_use'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Cognitive data missing required columns: {missing}")

    logger.info(f"Loaded {len(df)} cognitive records")
    return df


def merge_datasets(microbiome_df: pd.DataFrame, cognitive_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge microbiome and cognitive datasets on participant_id.

    Args:
        microbiome_df: DataFrame containing microbiome data.
        cognitive_df: DataFrame containing cognitive data.

    Returns:
        Merged DataFrame containing combined data.

    Raises:
        ValueError: If merge results in no rows or duplicate participant IDs.
    """
    logger.info("Merging datasets on participant_id")

    # Check for duplicates in participant IDs before merge
    if microbiome_df['participant_id'].duplicated().any():
        logger.warning("Duplicate participant IDs found in microbiome data, dropping duplicates")
        microbiome_df = microbiome_df.drop_duplicates(subset=['participant_id'])

    if cognitive_df['participant_id'].duplicated().any():
        logger.warning("Duplicate participant IDs found in cognitive data, dropping duplicates")
        cognitive_df = cognitive_df.drop_duplicates(subset=['participant_id'])

    merged_df = pd.merge(
        microbiome_df,
        cognitive_df,
        on='participant_id',
        how='inner'
    )

    if len(merged_df) == 0:
        raise ValueError("Merge resulted in no rows. Check that participant IDs match between datasets.")

    logger.info(f"Successfully merged {len(merged_df)} records")
    return merged_df


def ingest_synthetic_cohort() -> pd.DataFrame:
    """
    Generate synthetic cohort data and ingest it into DataFrames.

    This function calls the synthetic generator to create the data files,
    then loads them using the load functions.

    Returns:
        Merged DataFrame containing the synthetic cohort.
    """
    logger.info("Starting synthetic cohort generation")
    
    # Generate the synthetic data files
    generate_synthetic_cohort()

    # Define file paths based on config
    microbiome_path = RAW_DATA_DIR / 'microbiome_data.csv'
    cognitive_path = RAW_DATA_DIR / 'cognitive_data.csv'

    # Load the data
    microbiome_df = load_microbiome_data(microbiome_path)
    cognitive_df = load_cognitive_data(cognitive_path)

    # Merge
    merged_df = merge_datasets(microbiome_df, cognitive_df)

    logger.info("Synthetic cohort ingestion complete")
    return merged_df


def save_merged_cohort(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the merged cohort to a CSV file.

    Args:
        df: DataFrame to save.
        output_path: Path where the CSV file will be written.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving merged cohort to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} records to {output_path}")


def main():
    """
    Main entry point for the ingestion script.
    Generates synthetic data, merges it, and saves the result.
    """
    logger.info("Starting ingestion pipeline")
    
    try:
        # Ingest and merge data
        merged_df = ingest_synthetic_cohort()
        
        # Define output path
        output_path = RAW_DATA_DIR / 'merged_cohort.csv'
        
        # Save results
        save_merged_cohort(merged_df, output_path)
        
        logger.info("Ingestion pipeline completed successfully")
        return merged_df
        
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
