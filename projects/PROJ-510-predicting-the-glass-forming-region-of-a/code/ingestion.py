"""
Data ingestion module for the Glass Forming Region Prediction project.
Handles downloading, filtering, and cleaning of alloy datasets.
"""
import logging
import os
import sys
from typing import List, Dict, Any, Optional
import pandas as pd
from datasets import load_dataset

logger = logging.getLogger(__name__)

# Verified real data source
DATASET_NAME = "matsci/glass-forming-ability"

def load_glass_data() -> pd.DataFrame:
    """
    Load the glass forming ability dataset from Hugging Face.
    
    Returns:
        DataFrame containing the raw alloy data
        
    Raises:
        ValueError: If the dataset cannot be fetched
    """
    logger.info(f"Loading dataset: {DATASET_NAME}")
    try:
        dataset = load_dataset(DATASET_NAME, split="train")
        df = dataset.to_pandas()
        
        # Verify critical column exists
        if 'critical_cooling_rate' not in df.columns:
            raise ValueError(f"Dataset missing required column 'critical_cooling_rate'. Columns: {df.columns.tolist()}")
        
        logger.info(f"Loaded {len(df)} rows from {DATASET_NAME}")
        return df
    except Exception as e:
        raise ValueError(f"Data fetch failed: {DATASET_NAME} unavailable. Error: {str(e)}")

def log_sampling_info(df: pd.DataFrame, n: int, method: str) -> None:
    """Log information about data sampling if applied."""
    logger.info(f"Sampling info: {n} rows selected using {method}")

def filter_ternary_alloys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataset to keep only ternary alloys (3 elements).
    
    Args:
        df: Input DataFrame
        
    Returns:
        Filtered DataFrame
    """
    logger.info("Filtering for ternary alloys...")
    
    def count_elements(composition: str) -> int:
        if not isinstance(composition, str):
            return 0
        # Assume format is "El1_El2_El3" or similar
        parts = composition.replace('_', ' ').split()
        return len(parts)
    
    # Count elements in composition string
    df['_elem_count'] = df['composition'].apply(count_elements)
    ternary_df = df[df['_elem_count'] == 3].copy()
    ternary_df = ternary_df.drop(columns=['_elem_count'])
    
    logger.info(f"Filtered from {len(df)} to {len(ternary_df)} ternary alloys")
    return ternary_df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the dataset by removing rows with missing critical data.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Cleaned DataFrame
    """
    logger.info("Cleaning data...")
    initial_count = len(df)
    
    # Drop rows with missing composition or critical_cooling_rate
    df = df.dropna(subset=['composition', 'critical_cooling_rate'])
    
    # Drop rows where glass forming label is unknown (if column exists)
    if 'glass_forming_label' in df.columns:
        df = df[df['glass_forming_label'].notna()]
        
    logger.info(f"Cleaned data: {initial_count} -> {len(df)} rows")
    return df

def validate_critical_cooling_rate(df: pd.DataFrame) -> None:
    """
    Validate that critical_cooling_rate has non-zero variance and sufficient entries.
    
    Args:
        df: DataFrame to validate
        
    Raises:
        ValueError: If validation fails
    """
    if len(df) < 500:
        raise ValueError(f"Data availability error: <500 valid entries ({len(df)} found)")
    
    if df['critical_cooling_rate'].var() == 0:
        raise ValueError("Data availability error: zero variance in critical_cooling_rate")
    
    logger.info("Critical cooling rate validation passed")

def validate_data_quality(df: pd.DataFrame) -> None:
    """
    Perform general data quality checks.
    
    Args:
        df: DataFrame to validate
        
    Raises:
        ValueError: If data quality checks fail
    """
    # Check for NaN in target columns
    target_cols = ['critical_cooling_rate', 'mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
    for col in target_cols:
        if col in df.columns and df[col].isna().any():
            raise ValueError(f"Data quality error: NaN found in column {col}")
    
    logger.info("Data quality validation passed")

def run_ingestion() -> pd.DataFrame:
    """
    Run the full ingestion pipeline.
    
    Returns:
        Processed DataFrame ready for feature engineering
    """
    logger.info("Starting data ingestion pipeline...")
    
    # Load data
    df = load_glass_data()
    
    # Filter for ternary alloys
    df = filter_ternary_alloys(df)
    
    # Clean data
    df = clean_data(df)
    
    # Validate critical cooling rate
    validate_critical_cooling_rate(df)
    
    logger.info("Ingestion pipeline completed successfully")
    return df

if __name__ == "__main__":
    # Ensure output directory exists
    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    
    # Run ingestion
    df = run_ingestion()
    
    # Save processed data
    output_path = os.path.join(output_dir, "processed_alloys.csv")
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")
