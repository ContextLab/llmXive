"""
T019: Implement exclusion logic for samples with missing age or failed haplogroup assignment.

This module loads the merged dataset, removes rows where:
- 'age' is missing (NaN) or non-positive.
- 'haplogroup' is missing (NaN) or marked as 'FAILED'/'Unknown'.
It then saves the cleaned dataset to the processed directory.
"""
import os
import sys
import logging
from pathlib import Path

import pandas as pd

# Ensure the analysis package can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.merge_metadata import ensure_dirs, load_burden_data, load_haplogroup_data, load_metadata_panel, merge_datasets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_dataset(
    input_path: Path,
    output_path: Path,
    age_column: str = 'age',
    haplogroup_column: str = 'haplogroup',
    min_age: float = 0.0
) -> pd.DataFrame:
    """
    Load the merged dataset, exclude samples with missing/invalid age or haplogroup,
    and return the cleaned DataFrame.

    Args:
        input_path: Path to the merged dataset CSV.
        output_path: Path where the cleaned CSV will be saved.
        age_column: Name of the age column.
        haplogroup_column: Name of the haplogroup column.
        min_age: Minimum valid age (samples below this are excluded).

    Returns:
        Cleaned DataFrame.
    """
    logger.info(f"Loading dataset from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_path}")

    df = pd.read_csv(input_path)
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} rows")

    # Ensure columns exist
    if age_column not in df.columns:
        raise ValueError(f"Age column '{age_column}' not found in dataset. Columns: {df.columns.tolist()}")
    if haplogroup_column not in df.columns:
        raise ValueError(f"Haplogroup column '{haplogroup_column}' not found in dataset. Columns: {df.columns.tolist()}")

    # Filter out missing or invalid age
    # Convert to numeric, coercing errors to NaN
    df[age_column] = pd.to_numeric(df[age_column], errors='coerce')
    valid_age_mask = df[age_column].notna() & (df[age_column] >= min_age)
    df = df[valid_age_mask]
    logger.info(f"After age filtering: {len(df)} rows (removed {initial_count - len(df)})")

    # Filter out missing or invalid haplogroup
    # Standardize to string for comparison, handle NaNs
    df[haplogroup_column] = df[haplogroup_column].astype(str)
    invalid_hg_values = ['nan', 'nan', 'FAILED', 'Unknown', 'unknown', '']
    valid_hg_mask = ~df[haplogroup_column].isin(invalid_hg_values)
    df = df[valid_hg_mask]
    logger.info(f"After haplogroup filtering: {len(df)} rows (removed {initial_count - len(df)} total)")

    # Save to output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned dataset saved to {output_path}")

    return df

def main():
    """
    Main entry point for T019.
    Expects the merged dataset at code/data/processed/merged_dataset.csv
    and outputs to code/data/processed/mito_aging_dataset.csv
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "processed" / "merged_dataset.csv"
    output_path = project_root / "data" / "processed" / "mito_aging_dataset.csv"

    try:
        cleaned_df = clean_dataset(input_path, output_path)
        print(f"Task T019 completed successfully. {len(cleaned_df)} samples retained.")
    except Exception as e:
        logger.error(f"Task T019 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()