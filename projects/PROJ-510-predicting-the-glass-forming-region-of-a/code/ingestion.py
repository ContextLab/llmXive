"""
Ingestion module for loading and processing glass-forming alloy data.

This module handles:
1. Loading the `matsci/glass-forming-ability` dataset from Hugging Face.
2. Filtering for valid ternary alloys with critical cooling rate (CCR) data.
3. Enforcing "fail loudly" policy: No synthetic fallbacks.
"""
import logging
import os
import sys
from typing import List, Dict, Any, Optional
import pandas as pd
from datasets import load_dataset
import itertools
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), '..', 'logs', 'ingestion.log'))
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATASET_NAME = "matsci/glass-forming-ability"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
RAW_DIR = os.path.join(DATA_DIR, 'raw')

# Ensure directories exist
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)

# Seed for reproducibility
RANDOM_STATE = 42
random.seed(RANDOM_STATE)

def load_glass_data() -> pd.DataFrame:
    """
    Load the glass-forming ability dataset from Hugging Face.
    
    CRITICAL: This function MUST fail loudly if the dataset is unavailable.
    No synthetic fallbacks are permitted.
    
    Returns:
        pd.DataFrame: The loaded dataset.
        
    Raises:
        ValueError: If the dataset cannot be fetched.
    """
    logger.info(f"Attempting to load dataset: {DATASET_NAME}")
    try:
        # Use streaming to handle large datasets and prevent memory overflow
        dataset = load_dataset(DATASET_NAME, streaming=True)
        
        # Convert to pandas DataFrame (taking the first split if multiple exist)
        # We iterate to get the data into memory for processing, but stream the fetch
        df_list = []
        split_name = list(dataset.keys())[0]
        
        logger.info(f"Processing split: {split_name}")
        
        # Stream the data
        for batch in dataset[split_name]:
            df_list.append(batch)
        
        if not df_list:
            raise ValueError("Dataset is empty.")
        
        df = pd.DataFrame(df_list)
        logger.info(f"Successfully loaded {len(df)} rows from {DATASET_NAME}")
        return df
        
    except Exception as e:
        # CRITICAL: Fail loudly. Do not catch and return synthetic data.
        error_msg = f"Data fetch failed: {DATASET_NAME} unavailable. Error: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

def filter_ternary_alloys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataset to keep only ternary alloys (3 elements).
    
    Args:
        df (pd.DataFrame): The raw dataset.
        
    Returns:
        pd.DataFrame: Filtered dataset containing only ternary alloys.
    """
    logger.info("Filtering for ternary alloys...")
    
    # Assuming 'composition' column exists and is formatted like "Fe_Cr_Ni" or "Fe0.33Cr0.33Ni0.34"
    # We need to count the number of elements.
    # Strategy: Split by common delimiters or parse chemical formula.
    # For HuggingFace matsci datasets, composition is often a string of element symbols.
    
    def count_elements(composition_str: str) -> int:
        if pd.isna(composition_str) or not isinstance(composition_str, str):
            return 0
        # Simple heuristic: Split by '_' or count capital letters followed by optional lowercase/digits
        # This is a rough heuristic; specific dataset format may vary.
        # If format is "Fe_Cr_Ni", split by '_'
        if '_' in composition_str:
            parts = composition_str.split('_')
            return len([p for p in parts if p])
        # If format is "FeCrNi", count capital letters
        count = 0
        for char in composition_str:
            if char.isupper():
                count += 1
        return count

    # Apply filter
    # We assume the column is named 'composition' based on standard schemas
    if 'composition' not in df.columns:
        # Fallback or error if column name differs
        logger.warning("Column 'composition' not found. Checking for alternatives...")
        # If no composition column, we cannot filter by element count. 
        # We might assume all are valid or raise an error.
        # For this implementation, we raise an error if we can't verify.
        raise ValueError("Column 'composition' not found in dataset.")
    
    df['element_count'] = df['composition'].apply(count_elements)
    ternary_df = df[df['element_count'] == 3].copy()
    
    logger.info(f"Filtered from {len(df)} to {len(ternary_df)} ternary alloys.")
    return ternary_df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the data: remove missing values in critical columns.
    
    Args:
        df (pd.DataFrame): The filtered dataset.
        
    Returns:
        pd.DataFrame: Cleaned dataset.
    """
    logger.info("Cleaning data...")
    
    # Define critical columns that must be present
    critical_columns = ['composition', 'critical_cooling_rate']
    
    # Check if critical columns exist
    missing_cols = [col for col in critical_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing critical columns in dataset: {missing_cols}")
    
    # Filter out rows where critical_cooling_rate is missing
    # The task specifies: "Filter for ternary alloys, missing data, AND entries where critical_cooling_rate is present."
    initial_count = len(df)
    df = df.dropna(subset=['critical_cooling_rate'])
    df = df[df['critical_cooling_rate'].notna()]
    
    # Also ensure composition is not null
    df = df.dropna(subset=['composition'])
    
    final_count = len(df)
    logger.info(f"Cleaned data: {initial_count} -> {final_count} rows (removed missing CCR).")
    
    return df

def validate_critical_cooling_rate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate that critical_cooling_rate has non-zero variance and sufficient entries.
    
    Args:
        df (pd.DataFrame): The cleaned dataset.
        
    Returns:
        pd.DataFrame: The validated dataset.
        
    Raises:
        ValueError: If validation fails.
    """
    logger.info("Validating critical_cooling_rate...")
    
    if len(df) < 500:
        raise ValueError(f"Data availability error: {len(df)} valid entries, expected >= 500")
    
    variance = df['critical_cooling_rate'].var()
    if variance == 0 or pd.isna(variance):
        raise ValueError("Data availability error: Zero variance in critical_cooling_rate")
    
    logger.info(f"Validation passed. Variance: {variance}, Count: {len(df)}")
    return df

def log_sampling_info(final_count: int, sampled: bool = False, sample_size: Optional[int] = None):
    """
    Log sampling information to a file.
    
    Args:
        final_count (int): The final number of rows.
        sampled (bool): Whether sampling was performed.
        sample_size (int, optional): The size of the sample if sampled.
    """
    log_path = os.path.join(PROCESSED_DIR, 'sampling_log.txt')
    with open(log_path, 'w') as f:
        f.write(f"Total valid rows: {final_count}\n")
        f.write(f"Sampling performed: {sampled}\n")
        if sampled:
            f.write(f"Sample size: {sample_size}\n")
        if final_count < 1000 and final_count >= 500:
            f.write("Status: TARGET_NOT_MET (Target N >= 1000 not met)\n")
        elif final_count >= 1000:
            f.write("Status: TARGET_MET\n")
        else:
            f.write("Status: FAILED (< 500 rows)\n")
    logger.info(f"Sampling log written to {log_path}")

def run_ingestion():
    """
    Main function to run the ingestion pipeline.
    """
    logger.info("Starting Ingestion Pipeline")
    
    # 1. Load Data
    try:
        df = load_glass_data()
    except ValueError as e:
        logger.error(f"CRITICAL: {e}")
        sys.exit(1)
    
    # 2. Filter Ternary
    df = filter_ternary_alloys(df)
    
    # 3. Clean Data
    df = clean_data(df)
    
    # 4. Validate
    try:
        df = validate_critical_cooling_rate(df)
    except ValueError as e:
        logger.error(f"CRITICAL: {e}")
        sys.exit(1)
    
    # 5. Sampling Logic (if > 10k rows)
    sampled = False
    sample_size = None
    if len(df) > 10000:
        logger.info("Dataset > 10k rows. Sampling to 10k.")
        df = df.sample(n=10000, random_state=RANDOM_STATE)
        sampled = True
        sample_size = 10000
    
    # 6. Save to CSV
    output_path = os.path.join(PROCESSED_DIR, 'processed_alloys.csv')
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path} ({len(df)} rows)")
    
    # 7. Log Sampling Info
    log_sampling_info(len(df), sampled, sample_size)
    
    logger.info("Ingestion Pipeline Completed Successfully")
    return df

if __name__ == "__main__":
    run_ingestion()
