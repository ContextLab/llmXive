"""
T012a: Age Exclusion Logic
Filters raw dataset for participants age >= 65.
Writes filtered data to data/processed/cleaned_age_filtered.csv.
Writes exclusion counts to data/processed/exclusion_counts.json.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Setup logging (consistent with project utils pattern)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_config_paths() -> Dict[str, Path]:
    """Returns project paths based on standard conventions."""
    root = Path(__file__).resolve().parent.parent
    return {
        'raw_input': root / 'data' / 'raw' / 'raw_dataset.csv',
        'processed_output': root / 'data' / 'processed' / 'cleaned_age_filtered.csv',
        'exclusion_counts': root / 'data' / 'processed' / 'exclusion_counts.json',
        'processed_dir': root / 'data' / 'processed'
    }

def load_raw_dataset(path: Path) -> pd.DataFrame:
    """Loads the raw dataset from CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded raw dataset: {len(df)} records from {path}")
    return df

def filter_by_age(df: pd.DataFrame, min_age: int = 65) -> tuple[pd.DataFrame, int]:
    """
    Filters dataframe for age >= min_age.
    Returns (filtered_df, count_excluded).
    """
    if 'age' not in df.columns:
        raise ValueError("Dataset missing required 'age' column.")
    
    total_before = len(df)
    # Filter for age >= 65
    filtered_df = df[df['age'] >= min_age].copy()
    count_excluded = total_before - len(filtered_df)
    
    logger.info(f"Age filter (>= {min_age}): {total_before} -> {len(filtered_df)} records. Excluded: {count_excluded}")
    return filtered_df, count_excluded

def save_filtered_dataset(df: pd.DataFrame, path: Path) -> None:
    """Saves the filtered dataframe to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved filtered dataset to: {path}")

def save_exclusion_count(count: int, path: Path) -> None:
    """
    Appends or creates the exclusion_counts.json file with the key ERR_MISSING_AGE_FIELD.
    """
    data = {}
    if path.exists():
        with open(path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                logger.warning("Existing exclusion_counts.json is invalid JSON. Overwriting.")
    
    data['ERR_MISSING_AGE_FIELD'] = count
    
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Updated exclusion counts at: {path}")

def main():
    """Main entry point for T012a."""
    paths = get_config_paths()
    
    try:
        # 1. Load Raw Data
        logger.info("Starting T012a: Age Exclusion")
        raw_df = load_raw_dataset(paths['raw_input'])
        
        # 2. Filter by Age
        cleaned_df, excluded_count = filter_by_age(raw_df, min_age=65)
        
        # 3. Save Filtered Data
        save_filtered_dataset(cleaned_df, paths['processed_output'])
        
        # 4. Save Exclusion Count
        save_exclusion_count(excluded_count, paths['exclusion_counts'])
        
        logger.info("T012a completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during T012a execution: {e}")
        raise

if __name__ == '__main__':
    main()
