import logging
import os
import sys
from typing import List, Dict, Any, Optional
import pandas as pd
from datasets import load_dataset
import numpy as np

from utils import get_logger, ensure_dir

logger = get_logger(__name__)

# Minimum required rows and variance threshold
MIN_ROWS = 500
MIN_VARIANCE_THRESHOLD = 1e-6

def load_glass_data() -> pd.DataFrame:
    """
    Download the glass-forming-ability dataset from matsci.
    Strictly fails if the dataset or required columns are missing.
    """
    logger.info("Loading glass-forming-ability dataset...")
    try:
        # Using streaming=False as per spec for datasets < 7GB
        dataset = load_dataset("matsci/glass-forming-ability", split="train")
        df = dataset.to_pandas()
    except Exception as e:
        logger.error(f"Failed to load dataset from matsci/glass-forming-ability: {e}")
        raise RuntimeError(f"Data fetch failed: {e}")

    required_cols = ["composition", "critical_cooling_rate"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        raise ValueError(f"Dataset missing required columns: {missing}")

    return df

def filter_ternary_alloys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataset for ternary alloys (exactly 3 elements).
    """
    logger.info(f"Filtering for ternary alloys. Initial rows: {len(df)}")
    
    def count_elements(composition_str: str) -> int:
        if pd.isna(composition_str) or not isinstance(composition_str, str):
            return 0
        # Simple heuristic: split by space or comma, filter empty
        parts = [p.strip() for p in composition_str.replace(',', ' ').split()]
        # Assuming format like "Fe50Ni30P20" or "Fe Ni P"
        # If it's a single string like "Fe50Ni30P20", we need to parse elements
        # For now, assume standard space/comma separation or simple counting logic
        # A robust parser is in features.py, but for filtering we can do a quick check
        # If the string contains numbers, it might be "Fe50Ni30P20"
        # Let's rely on a simple regex or split if spaces exist.
        if ' ' in composition_str or ',' in composition_str:
            return len(parts)
        else:
            # Attempt to count capital letters as element starts (simple heuristic)
            # This is a rough filter; precise parsing happens in features
            count = 0
            for char in composition_str:
                if char.isupper():
                    count += 1
            return count

    df['element_count'] = df['composition'].apply(count_elements)
    ternary_df = df[df['element_count'] == 3].copy()
    
    logger.info(f"Filtered to ternary alloys: {len(ternary_df)} rows")
    return ternary_df

def validate_data_quality(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows with missing critical_cooling_rate or elemental data issues.
    """
    logger.info("Validating data quality...")
    initial_count = len(df)
    
    # Drop rows where critical_cooling_rate is missing or non-numeric
    df = df.dropna(subset=['critical_cooling_rate'])
    df['critical_cooling_rate'] = pd.to_numeric(df['critical_cooling_rate'], errors='coerce')
    df = df.dropna(subset=['critical_cooling_rate'])
    
    # Drop rows with empty composition
    df = df[df['composition'].notna() & (df['composition'].str.strip() != '')]
    
    logger.info(f"Data quality validation removed {initial_count - len(df)} rows.")
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Final cleaning step: standardize columns and types.
    """
    logger.info("Cleaning data...")
    df = df.copy()
    if 'critical_cooling_rate' in df.columns:
        df['critical_cooling_rate'] = df['critical_cooling_rate'].astype(float)
    return df

def validate_critical_cooling_rate(df: pd.DataFrame) -> None:
    """
    T017 Implementation: Validate that critical_cooling_rate has non-zero variance
    and at least MIN_ROWS entries.
    Raises ValueError with specific message if checks fail.
    """
    col = 'critical_cooling_rate'
    if col not in df.columns:
        raise ValueError(f"Validation failed: Column '{col}' not found in dataset.")
    
    count = len(df)
    if count < MIN_ROWS:
        raise ValueError(
            f"Validation failed: Dataset has {count} entries, "
            f"but requires at least {MIN_ROWS} for {col}."
        )
    
    variance = df[col].var()
    if pd.isna(variance) or variance < MIN_VARIANCE_THRESHOLD:
        raise ValueError(
            f"Validation failed: 'critical_cooling_rate' has near-zero variance ({variance}). "
            f"Requires non-zero variance to proceed with training."
        )
    
    logger.info(f"Validation passed: {col} has {count} entries and variance {variance:.6f}.")

def run_ingestion(output_path: str = "data/processed/processed_alloys.csv") -> pd.DataFrame:
    """
    Main entry point for the ingestion pipeline.
    """
    ensure_dir(os.path.dirname(output_path))
    
    df = load_glass_data()
    df = filter_ternary_alloys(df)
    df = validate_data_quality(df)
    df = clean_data(df)
    
    # T017: Run validation on the target column
    validate_critical_cooling_rate(df)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed alloys to {output_path}")
    return df

if __name__ == "__main__":
    run_ingestion()
