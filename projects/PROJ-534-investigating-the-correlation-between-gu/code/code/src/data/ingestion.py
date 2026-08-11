"""
Data ingestion module for the gut microbiome and cognitive flexibility study.

This module handles loading, merging, and saving of synthetic cohort data.
"""

import os
import pandas as pd
from pathlib import Path
import logging
import sys

from code.src.utils.config import SEED, DATA_DIR, RAW_DATA_DIR, LOGS_DIR
from code.src.data.synthetic_gen import generate_synthetic_cohort

# Configure logging
LOG_FILE = LOGS_DIR / "ingestion.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_microbiome_data(file_path: Path) -> pd.DataFrame:
    """
    Load microbiome data from a CSV file.

    Args:
        file_path: Path to the microbiome data CSV

    Returns:
        DataFrame with microbiome data
    """
    logger.info(f"Loading microbiome data from {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def load_cognitive_data(file_path: Path) -> pd.DataFrame:
    """
    Load cognitive data from a CSV file.

    Args:
        file_path: Path to the cognitive data CSV

    Returns:
        DataFrame with cognitive data
    """
    logger.info(f"Loading cognitive data from {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def merge_datasets(microbiome_df: pd.DataFrame, cognitive_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge microbiome and cognitive datasets on participant ID.

    Args:
        microbiome_df: DataFrame with microbiome data
        cognitive_df: DataFrame with cognitive data

    Returns:
        Merged DataFrame
    """
    logger.info("Merging microbiome and cognitive datasets")
    merged = pd.merge(microbiome_df, cognitive_df, on='participant_id', how='inner')
    logger.info(f"Merged dataset has {len(merged)} rows")
    return merged

def ingest_synthetic_cohort(n_participants: int = 1000) -> pd.DataFrame:
    """
    Generate and return the synthetic cohort.

    Args:
        n_participants: Number of participants to generate

    Returns:
        DataFrame with synthetic cohort data
    """
    logger.info(f"Generating synthetic cohort with {n_participants} participants")
    cohort = generate_synthetic_cohort(n_participants)
    logger.info(f"Generated {len(cohort)} rows")
    return cohort

def save_merged_cohort(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the merged cohort to a CSV file.

    Args:
        df: DataFrame to save
        output_path: Path to save the CSV file
    """
    logger.info(f"Saving merged cohort to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def main():
    """
    Main entry point for data ingestion.

    Generates the synthetic cohort, saves it to data/raw,
    then loads and saves the merged cohort to data/processed.
    """
    # Generate synthetic cohort
    cohort = ingest_synthetic_cohort(n_participants=1000)

    # Save raw data
    raw_path = RAW_DATA_DIR / "synthetic_cohort.csv"
    save_merged_cohort(cohort, raw_path)

    # Load and process (for demonstration, we'll just save the same data as merged)
    # In a real scenario, this would load separate files and merge them
    merged_cohort = load_microbiome_data(raw_path)
    processed_path = DATA_DIR / "processed" / "merged_cohort.csv"
    save_merged_cohort(merged_cohort, processed_path)

    return merged_cohort

if __name__ == "__main__":
    main()
