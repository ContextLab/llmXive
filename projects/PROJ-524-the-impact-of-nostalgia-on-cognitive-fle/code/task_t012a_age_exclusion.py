"""
Task T012a: Age Exclusion
Filters the raw dataset for participants aged 65 and older.
Writes filtered data to data/processed/cleaned_age_filtered.csv.
Updates data/processed/exclusion_counts.json with ERR_MISSING_AGE_FIELD count.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "raw_dataset.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_CSV_PATH = PROCESSED_DIR / "cleaned_age_filtered.csv"
EXCLUSION_COUNTS_PATH = PROCESSED_DIR / "exclusion_counts.json"

MIN_AGE = 65

def load_raw_dataset(path: Path) -> pd.DataFrame:
    """Loads the raw dataset from CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {path}. "
                                "Ensure T010b (Ingestion) has been executed successfully.")
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded raw dataset with {len(df)} records from {path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load raw dataset: {e}")
        raise

def filter_by_age(df: pd.DataFrame, min_age: int = MIN_AGE) -> pd.DataFrame:
    """Filters dataframe for age >= min_age."""
    if 'age' not in df.columns:
        raise KeyError("Column 'age' not found in dataset. Cannot perform age filtering.")
    
    # Count records before filtering
    total_records = len(df)
    
    # Filter
    filtered_df = df[df['age'] >= min_age].copy()
    
    # Calculate exclusions
    excluded_count = total_records - len(filtered_df)
    
    logger.info(f"Age filtering: {excluded_count} records excluded (age < {min_age}). "
                f"Remaining: {len(filtered_df)} records.")
    
    return filtered_df, excluded_count

def save_filtered_dataset(df: pd.DataFrame, path: Path):
    """Saves the filtered dataframe to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved filtered dataset to {path}")

def save_exclusion_count(count: int, path: Path):
    """Updates the exclusion_counts.json file with ERR_MISSING_AGE_FIELD."""
    counts = {}
    if path.exists():
        try:
            with open(path, 'r') as f:
                counts = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Existing exclusion_counts.json is invalid JSON. Overwriting.")
            counts = {}
    
    counts['ERR_MISSING_AGE_FIELD'] = count
    
    with open(path, 'w') as f:
        json.dump(counts, f, indent=2)
    
    logger.info(f"Updated exclusion counts in {path}: ERR_MISSING_AGE_FIELD = {count}")

def main():
    """Main execution function for T012a."""
    try:
        # 1. Load Raw Data
        logger.info("Starting T012a: Age Exclusion")
        df = load_raw_dataset(RAW_DATA_PATH)
        
        # 2. Filter by Age
        filtered_df, excluded_count = filter_by_age(df, MIN_AGE)
        
        if filtered_df.empty:
            logger.warning("No records passed the age filter (>= 65). Output will be empty.")
        
        # 3. Save Filtered Data
        save_filtered_dataset(filtered_df, OUTPUT_CSV_PATH)
        
        # 4. Update Exclusion Counts
        save_exclusion_count(excluded_count, EXCLUSION_COUNTS_PATH)
        
        logger.info("T012a completed successfully.")
        
    except FileNotFoundError as e:
        logger.critical(f"Data file missing: {e}")
        raise
    except KeyError as e:
        logger.critical(f"Schema error: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during T012a execution: {e}")
        raise

if __name__ == "__main__":
    main()
