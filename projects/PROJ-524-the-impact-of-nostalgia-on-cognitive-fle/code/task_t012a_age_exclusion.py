import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning, log_error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_raw_dataset() -> pd.DataFrame:
    """
    Loads the raw dataset from the specified path.
    Returns a pandas DataFrame.
    """
    config = get_config()
    raw_path = config.get('raw_dataset_path')
    
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw dataset not found at {raw_path}. "
                                "Ensure T010b has been executed successfully.")
    
    log_info(f"Loading raw dataset from {raw_path}")
    df = pd.read_csv(raw_path)
    return df

def filter_by_age(df: pd.DataFrame, min_age: int = 65) -> tuple[pd.DataFrame, int]:
    """
    Filters the dataframe to keep only records where age >= min_age.
    
    Args:
        df: Input dataframe
        min_age: Minimum age threshold (default 65)
        
    Returns:
        Tuple of (filtered_dataframe, count_of_excluded_records)
    """
    if 'age' not in df.columns:
        log_error("ERR_MISSING_AGE_FIELD: Column 'age' not found in dataset.")
        raise ValueError("Column 'age' not found in dataset.")
    
    total_count = len(df)
    filtered_df = df[df['age'] >= min_age].copy()
    excluded_count = total_count - len(filtered_df)
    
    log_info(f"Age filtering: Kept {len(filtered_df)} records, Excluded {excluded_count} records.")
    return filtered_df, excluded_count

def save_filtered_dataset(df: pd.DataFrame, output_path: str) -> None:
    """
    Saves the filtered dataframe to a CSV file.
    """
    ensure_dirs(output_path)
    df.to_csv(output_path, index=False)
    log_info(f"Saved filtered dataset to {output_path}")

def save_exclusion_count(exclusion_counts: Dict[str, Any], output_path: str) -> None:
    """
    Updates and saves the exclusion counts JSON file.
    """
    ensure_dirs(output_path)
    
    # Load existing counts if file exists, otherwise start fresh
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            counts = json.load(f)
    else:
        counts = {}
    
    counts['ERR_MISSING_AGE_FIELD'] = exclusion_counts['ERR_MISSING_AGE_FIELD']
    
    with open(output_path, 'w') as f:
        json.dump(counts, f, indent=2)
    
    log_info(f"Updated exclusion counts at {output_path}")

def main():
    """
    Main execution function for T012a: Age Exclusion.
    """
    config = get_config()
    
    # Paths
    output_csv_path = config.get('processed_age_filtered_path')
    exclusion_counts_path = config.get('exclusion_counts_path')
    
    log_info("Starting T012a: Age Exclusion")
    
    try:
        # Load raw data
        df = load_raw_dataset()
        
        # Filter by age
        filtered_df, excluded_count = filter_by_age(df, min_age=65)
        
        # Save filtered dataset
        save_filtered_dataset(filtered_df, output_csv_path)
        
        # Save exclusion count
        exclusion_data = {'ERR_MISSING_AGE_FIELD': excluded_count}
        save_exclusion_count(exclusion_data, exclusion_counts_path)
        
        log_info("T012a completed successfully.")
        
    except FileNotFoundError as e:
        log_error(str(e))
        raise
    except Exception as e:
        log_error(f"Unexpected error during T012a: {str(e)}")
        raise

if __name__ == "__main__":
    main()
