import os
import sys
import logging
from pathlib import Path
import pandas as pd
from analysis.merge_metadata import ensure_dirs, load_burden_data, load_haplogroup_data, load_metadata_panel, merge_datasets

logger = logging.getLogger(__name__)

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the merged dataset by dropping rows with missing critical values
    and standardizing column types.
    """
    logger.info(f"Cleaning dataset with {len(df)} rows...")
    
    # Drop rows with missing age (critical for analysis)
    initial_count = len(df)
    df = df.dropna(subset=['age'])
    logger.info(f"Dropped {initial_count - len(df)} rows with missing age.")

    # Drop rows with missing haplogroup if we are doing haplogroup-specific analysis
    # (Note: T019 logic handles conditional exclusion; this is a general clean pass)
    # We retain rows with missing haplogroup for burden-only analysis if age is present.
    
    # Ensure numeric types for critical columns
    numeric_cols = ['heteroplasmy_burden', 'age', 'sequencing_depth', 'PC1', 'PC2', 'PC3', 'PC4', 'PC5']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows where numeric conversion resulted in NaN for critical columns
    df = df.dropna(subset=['heteroplasmy_burden', 'age', 'sequencing_depth'])
    
    logger.info(f"Final clean dataset size: {len(df)} rows.")
    return df

def main():
    """Main entry point for cleaning the dataset."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    paths = {
        'input': Path('code/data/processed/mito_aging_dataset.csv'),
        'output': Path('code/data/processed/mito_aging_dataset_clean.csv')
    }
    
    if not paths['input'].exists():
        logger.error(f"Input file not found: {paths['input']}")
        sys.exit(1)
    
    try:
        df = pd.read_csv(paths['input'])
        df_clean = clean_dataset(df)
        
        paths['output'].parent.mkdir(parents=True, exist_ok=True)
        df_clean.to_csv(paths['output'], index=False)
        logger.info(f"Cleaned dataset saved to {paths['output']}")
        
    except Exception as e:
        logger.error(f"Error during cleaning: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
