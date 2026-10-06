"""
T012a: Age Exclusion Logic

Filters the raw dataset for participants aged 65 and above.
Writes the filtered dataset to data/processed/cleaned_age_filtered.csv.
Writes the exclusion count to data/processed/exclusion_counts.json.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Import config utilities from the existing project structure
from config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("T012a_AgeExclusion")

def get_config_paths() -> Dict[str, Path]:
    """
    Retrieves project paths from configuration.
    """
    config = get_config()
    return {
        'raw': Path(config['paths']['raw']),
        'processed': Path(config['paths']['processed']),
        'root': Path(config['paths']['root'])
    }

def load_raw_dataset(paths: Dict[str, Path]) -> pd.DataFrame:
    """
    Loads the raw dataset from data/raw/raw_dataset.csv.
    Raises FileNotFoundError if the file does not exist.
    """
    input_path = paths['raw'] / 'raw_dataset.csv'
    if not input_path.exists():
        logger.error(f"Raw dataset not found at {input_path}")
        raise FileNotFoundError(f"Raw dataset not found at {input_path}")
    
    logger.info(f"Loading raw dataset from {input_path}")
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} records from raw dataset")
        return df
    except Exception as e:
        logger.error(f"Failed to load raw dataset: {e}")
        raise

def filter_by_age(df: pd.DataFrame, min_age: int = 65) -> tuple[pd.DataFrame, int]:
    """
    Filters the dataframe for records where age >= min_age.
    Returns the filtered dataframe and the count of excluded records.
    """
    if 'age' not in df.columns:
        logger.error("Column 'age' not found in dataset")
        raise KeyError("Column 'age' not found in dataset")

    # Ensure age is numeric, coercing errors to NaN
    df['age'] = pd.to_numeric(df['age'], errors='coerce')
    
    # Drop rows where age is NaN (missing) before filtering, counting them as excluded
    valid_age_mask = df['age'].notna()
    missing_age_count = (~valid_age_mask).sum()
    df_valid_age = df[valid_age_mask]

    # Apply the age filter
    filtered_df = df_valid_age[df_valid_age['age'] >= min_age]
    excluded_count = len(df_valid_age) - len(filtered_df)
    
    total_excluded = missing_age_count + excluded_count
    
    logger.info(f"Age filtering: {missing_age_count} missing, {excluded_count} below {min_age}. Total excluded: {total_excluded}")
    logger.info(f"Retained {len(filtered_df)} records with age >= {min_age}")
    
    return filtered_df, total_excluded

def save_filtered_dataset(df: pd.DataFrame, paths: Dict[str, Path]) -> Path:
    """
    Saves the filtered dataframe to data/processed/cleaned_age_filtered.csv.
    """
    output_path = paths['processed'] / 'cleaned_age_filtered.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving filtered dataset to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info("Successfully saved filtered dataset")
    return output_path

def save_exclusion_count(count: int, paths: Dict[str, Path]) -> Path:
    """
    Updates data/processed/exclusion_counts.json with the age exclusion count.
    Key: 'ERR_MISSING_AGE_FIELD' (covers both missing and <65 per task spec interpretation).
    """
    output_path = paths['processed'] / 'exclusion_counts.json'
    
    # Load existing counts if present, otherwise start fresh
    counts = {}
    if output_path.exists():
        try:
            with open(output_path, 'r') as f:
                counts = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Existing exclusion_counts.json is invalid, overwriting.")
            counts = {}

    # Update the count for age exclusion
    # The task asks for key 'ERR_MISSING_AGE_FIELD'. 
    # We interpret this as the count of records removed due to age issues (missing or <65).
    counts['ERR_MISSING_AGE_FIELD'] = count
    
    with open(output_path, 'w') as f:
        json.dump(counts, f, indent=2)
    
    logger.info(f"Updated exclusion counts at {output_path}")
    return output_path

def main():
    """
    Main entry point for T012a.
    """
    logger.info("Starting T012a: Age Exclusion")
    
    try:
        paths = get_config_paths()
        
        # Load raw data
        df_raw = load_raw_dataset(paths)
        
        # Filter by age
        df_filtered, excluded_count = filter_by_age(df_raw, min_age=65)
        
        # Save outputs
        save_filtered_dataset(df_filtered, paths)
        save_exclusion_count(excluded_count, paths)
        
        logger.info("T012a completed successfully.")
        
    except FileNotFoundError as fnf:
        logger.error(f"Data file missing: {fnf}")
        raise
    except KeyError as ke:
        logger.error(f"Data schema error: {ke}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during T012a: {e}")
        raise

if __name__ == "__main__":
    main()
