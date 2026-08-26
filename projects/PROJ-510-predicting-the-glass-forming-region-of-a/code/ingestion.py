"""
Data ingestion for glass-forming alloys.
Downloads and filters the matsci/glass-forming-ability dataset.
"""
import logging
import os
import sys
from typing import List, Dict, Any, Optional
import pandas as pd
from datasets import load_dataset

# Add project root to path
if os.path.basename(os.path.dirname(__file__)) == 'code':
    sys.path.insert(0, os.path.dirname(__file__))
else:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils import get_logger, ensure_dir

logger = get_logger(__name__)

DATASET_NAME = "matsci/glass-forming-ability"
TARGET_COLUMNS = [
    'composition',
    'critical_cooling_rate',
    'mixing_enthalpy',
    'atomic_size_mismatch',
    'electronegativity_variance'
]

def load_glass_data() -> pd.DataFrame:
    """
    Load the glass-forming-ability dataset.

    Returns:
        DataFrame with glass-forming alloy data.

    Raises:
        ValueError: If dataset is unavailable or missing required columns.
    """
    logger.info(f"Loading dataset: {DATASET_NAME}")

    try:
        # Load dataset
        dataset = load_dataset(DATASET_NAME, split="train")
        df = dataset.to_pandas()
    except Exception as e:
        logger.error(f"Failed to load dataset {DATASET_NAME}: {e}")
        raise ValueError(f"Data fetch failed: {DATASET_NAME} unavailable - {e}")

    logger.info(f"Loaded {len(df)} records from {DATASET_NAME}")

    # Verify required columns
    required_cols = ['composition', 'critical_cooling_rate']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}")

    return df

def filter_ternary_alloys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataset for ternary alloys (3 elements).

    Args:
        df: Input DataFrame.

    Returns:
        Filtered DataFrame with only ternary alloys.
    """
    logger.info(f"Filtering for ternary alloys (original: {len(df)} records)")

    def count_elements(composition_str):
        """Count unique elements in composition string."""
        import re
        if not isinstance(composition_str, str):
            return 0
        # Match element symbols (uppercase + optional lowercase)
        elements = re.findall(r'[A-Z][a-z]?', composition_str.replace('_', ''))
        return len(set(elements))

    # Count elements for each row
    df['_element_count'] = df['composition'].apply(count_elements)

    # Filter for ternary (3 elements)
    ternary_df = df[df['_element_count'] == 3].copy()
    ternary_df = ternary_df.drop(columns=['_element_count'])

    logger.info(f"Filtered to {len(ternary_df)} ternary alloys")

    # Log exclusion reasons
    excluded = len(df) - len(ternary_df)
    logger.info(f"Excluded {excluded} non-ternary alloys")

    return ternary_df

def validate_data_quality(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean data quality.

    - Exclude rows with missing elemental data
    - Exclude rows with unknown glass-forming labels
    - Log exclusion counts

    Args:
        df: Input DataFrame.

    Returns:
        Cleaned DataFrame.
    """
    logger.info(f"Validating data quality (original: {len(df)} records)")

    initial_count = len(df)

    # Check for missing critical_cooling_rate
    missing_ccr = df['critical_cooling_rate'].isna().sum()
    if missing_ccr > 0:
        logger.warning(f"Found {missing_ccr} rows with missing critical_cooling_rate")
        df = df.dropna(subset=['critical_cooling_rate'])

    # Check for missing composition
    missing_comp = df['composition'].isna().sum()
    if missing_comp > 0:
        logger.warning(f"Found {missing_comp} rows with missing composition")
        df = df.dropna(subset=['composition'])

    # Filter out rows where composition cannot be parsed (invalid elements)
    valid_compositions = []
    invalid_count = 0
    for comp in df['composition']:
        if pd.isna(comp) or not isinstance(comp, str):
            invalid_count += 1
            continue
        try:
            # Try to parse to validate
            import re
            elements = re.findall(r'[A-Z][a-z]?', comp.replace('_', ''))
            if not elements:
                invalid_count += 1
                continue
            valid_compositions.append(True)
        except Exception:
            invalid_count += 1
            valid_compositions.append(False)

    if invalid_count > 0:
        logger.warning(f"Found {invalid_count} rows with invalid composition format")
        df = df[valid_compositions].copy()

    excluded = initial_count - len(df)
    logger.info(f"Data validation excluded {excluded} rows. Remaining: {len(df)}")

    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform final data cleaning.

    Args:
        df: Input DataFrame.

    Returns:
        Cleaned DataFrame.
    """
    logger.info("Performing final data cleaning")

    df_clean = df.copy()

    # Normalize composition strings
    df_clean['composition'] = df_clean['composition'].str.replace('_', '')

    # Ensure critical_cooling_rate is numeric
    df_clean['critical_cooling_rate'] = pd.to_numeric(
        df_clean['critical_cooling_rate'], errors='coerce'
    )

    # Drop any remaining NaN in critical columns
    df_clean = df_clean.dropna(subset=['critical_cooling_rate', 'composition'])

    logger.info(f"Final dataset size: {len(df_clean)}")

    return df_clean

def validate_critical_cooling_rate(df: pd.DataFrame) -> bool:
    """
    Validate that critical_cooling_rate has non-zero variance and >= 500 entries.

    Args:
        df: DataFrame to validate.

    Returns:
        True if validation passes.

    Raises:
        ValueError: If validation fails.
    """
    if len(df) < 500:
        raise ValueError(f"Data availability error: {len(df)} valid entries (< 500)")

    ccr_variance = df['critical_cooling_rate'].var()
    if ccr_variance == 0:
        raise ValueError("Data availability error: zero variance in critical_cooling_rate")

    logger.info(f"CCR validation passed: {len(df)} entries, variance={ccr_variance:.4f}")
    return True

def run_ingestion(output_path: str) -> pd.DataFrame:
    """
    Run the full ingestion pipeline.

    Args:
        output_path: Path to save filtered data.

    Returns:
        Processed DataFrame.
    """
    # Load data
    df = load_glass_data()

    # Filter for ternary alloys
    df = filter_ternary_alloys(df)

    # Validate and clean
    df = validate_data_quality(df)
    df = clean_data(df)

    # Validate critical_cooling_rate
    validate_critical_cooling_rate(df)

    # Ensure output directory exists
    ensure_dir(output_path)

    # Save intermediate filtered data (for features.py to pick up)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to {output_path}")

    return df

if __name__ == "__main__":
    # Default paths
    output_file = "data/processed/filtered_alloys.csv"

    # Allow override from command line
    if len(sys.argv) > 1:
        output_file = sys.argv[1]

    run_ingestion(output_file)