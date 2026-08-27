import os
import sys
import logging
from pathlib import Path
import pandas as pd
from analysis.merge_metadata import ensure_dirs, load_burden_data, load_haplogroup_data, load_metadata_panel, merge_datasets

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform final cleaning steps on the merged dataset.
    Ensures consistent dtypes and handles any remaining minor inconsistencies.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting dataset cleaning...")

    # Ensure numeric columns are float
    numeric_cols = ['heteroplasmy_burden', 'age', 'sequencing_depth', 'PC1', 'PC2', 'PC3', 'PC4', 'PC5']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows with critical missing values if any remain (should be handled by exclusion logic)
    critical_cols = ['sample_id', 'age', 'heteroplasmy_burden']
    df = df.dropna(subset=critical_cols)

    logger.info(f"Dataset cleaned. Shape: {df.shape}")
    return df

def main():
    """
    Main entry point for cleaning the dataset.
    Loads the processed dataset, cleans it, and saves the result.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        # Load the processed dataset
        processed_path = Path("code/data/processed/mito_aging_dataset.csv")
        if not processed_path.exists():
            logger.error(f"Processed dataset not found at {processed_path}")
            sys.exit(1)

        df = pd.read_csv(processed_path)
        logger.info(f"Loaded dataset with {len(df)} samples")

        # Clean the dataset
        cleaned_df = clean_dataset(df)

        # Save the cleaned dataset
        cleaned_path = Path("code/data/processed/mito_aging_dataset_cleaned.csv")
        cleaned_df.to_csv(cleaned_path, index=False)
        logger.info(f"Cleaned dataset saved to {cleaned_path}")

    except Exception as e:
        logger.error(f"Error during dataset cleaning: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
