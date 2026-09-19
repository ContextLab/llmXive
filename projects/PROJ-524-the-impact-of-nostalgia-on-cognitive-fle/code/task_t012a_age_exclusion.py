"""
T012a: Age Exclusion Filter
Filters data/raw/raw_dataset.csv for age >= 65.
Writes filtered data to data/processed/cleaned_age_filtered.csv.
Writes exclusion count to data/processed/exclusion_counts.json.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_dataset():
    """Load the raw dataset from data/raw/raw_dataset.csv."""
    raw_path = Path("data/raw/raw_dataset.csv")
    if not raw_path.exists():
        raise FileNotFoundError(f"ERR_RAW_DATA_MISSING: {raw_path} does not exist.")
    
    logger.info(f"Loading raw dataset from {raw_path}")
    df = pd.read_csv(raw_path)
    return df

def filter_by_age(df, min_age=65):
    """Filter dataframe to include only records where age >= min_age."""
    if 'age' not in df.columns:
        raise ValueError("ERR_MISSING_AGE_FIELD: 'age' column not found in dataset.")
    
    total_count = len(df)
    valid_mask = df['age'] >= min_age
    filtered_df = df[valid_mask].reset_index(drop=True)
    excluded_count = total_count - len(filtered_df)
    
    logger.info(f"Total records: {total_count}")
    logger.info(f"Records with age >= {min_age}: {len(filtered_df)}")
    logger.info(f"Excluded records (age < {min_age}): {excluded_count}")
    
    return filtered_df, excluded_count

def save_filtered_dataset(df, output_path):
    """Save the filtered dataframe to CSV."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered dataset to {output_path}")

def save_exclusion_count(exclusion_key, count, output_path):
    """Update exclusion_counts.json with the new count."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    exclusion_counts = {}
    if output_path.exists():
        with open(output_path, 'r') as f:
            exclusion_counts = json.load(f)
    
    exclusion_counts[exclusion_key] = count
    
    with open(output_path, 'w') as f:
        json.dump(exclusion_counts, f, indent=2)
    
    logger.info(f"Updated exclusion count for {exclusion_key}: {count}")

def main():
    """Main execution function for T012a."""
    logger.info("Starting T012a: Age Exclusion")
    
    try:
        # 1. Load raw dataset
        df_raw = load_raw_dataset()
        
        # 2. Filter by age
        df_filtered, excluded_count = filter_by_age(df_raw, min_age=65)
        
        # 3. Save filtered dataset
        output_csv_path = "data/processed/cleaned_age_filtered.csv"
        save_filtered_dataset(df_filtered, output_csv_path)
        
        # 4. Update exclusion counts
        exclusion_counts_path = "data/processed/exclusion_counts.json"
        save_exclusion_count("ERR_MISSING_AGE_FIELD", excluded_count, exclusion_counts_path)
        
        logger.info("T012a completed successfully.")
        
    except FileNotFoundError as e:
        logger.critical(str(e))
        raise
    except ValueError as e:
        logger.critical(str(e))
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during T012a: {e}")
        raise

if __name__ == "__main__":
    main()
