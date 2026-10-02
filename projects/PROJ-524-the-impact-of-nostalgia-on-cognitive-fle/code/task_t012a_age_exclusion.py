"""
Task T012a: Age Exclusion
Filters data/raw/raw_dataset.csv for age >= 65.
Writes filtered data to data/processed/cleaned_age_filtered.csv.
Writes exclusion count to data/processed/exclusion_counts.json with key ERR_MISSING_AGE_FIELD.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_dataset(raw_path: Path) -> pd.DataFrame:
    """Load the raw dataset from CSV."""
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {raw_path}")
    
    df = pd.read_csv(raw_path)
    logger.info(f"Loaded raw dataset with {len(df)} rows and columns: {list(df.columns)}")
    
    if 'age' not in df.columns:
        raise ValueError(f"Required column 'age' not found in {raw_path}")
    
    return df

def filter_by_age(df: pd.DataFrame, min_age: int = 65) -> pd.DataFrame:
    """Filter dataframe for participants with age >= min_age."""
    total_count = len(df)
    filtered_df = df[df['age'] >= min_age].copy()
    excluded_count = total_count - len(filtered_df)
    
    logger.info(f"Filtered by age >= {min_age}: {total_count} -> {len(filtered_df)} rows")
    logger.info(f"Excluded {excluded_count} rows due to age < {min_age}")
    
    return filtered_df, excluded_count

def save_filtered_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Save the filtered dataset to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered dataset to {output_path}")

def save_exclusion_count(exclusion_count: int, counts_path: Path) -> None:
    """Update exclusion_counts.json with the age exclusion count."""
    counts_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing counts if file exists
    if counts_path.exists():
        with open(counts_path, 'r') as f:
            counts = json.load(f)
    else:
        counts = {
            "ERR_MISSING_AGE_FIELD": 0,
            "ERR_MISSING_SCORE": 0,
            "ERR_MMSE_IMPAIRED": 0
        }
    
    # Update the specific key
    counts["ERR_MISSING_AGE_FIELD"] = exclusion_count
    
    # Save updated counts
    with open(counts_path, 'w') as f:
        json.dump(counts, f, indent=2)
    
    logger.info(f"Updated exclusion count for ERR_MISSING_AGE_FIELD: {exclusion_count}")

def main():
    """Main entry point for T012a."""
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    raw_path = base_dir / "data" / "raw" / "raw_dataset.csv"
    output_path = base_dir / "data" / "processed" / "cleaned_age_filtered.csv"
    counts_path = base_dir / "data" / "processed" / "exclusion_counts.json"
    
    try:
        # Load raw dataset
        df = load_raw_dataset(raw_path)
        
        # Filter by age
        filtered_df, exclusion_count = filter_by_age(df)
        
        # Save filtered dataset
        save_filtered_dataset(filtered_df, output_path)
        
        # Save exclusion count
        save_exclusion_count(exclusion_count, counts_path)
        
        logger.info("T012a completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
