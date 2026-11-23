"""
Task T012b: Score Exclusion
Filters the age-filtered dataset for non-null 'perseverative_errors' and 'categories_completed'.
Writes filtered data to data/processed/cleaned_score_filtered.csv.
Updates data/processed/exclusion_counts.json with key 'ERR_MISSING_SCORE'.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_config_paths() -> Dict[str, Path]:
    """
    Returns the paths for input and output files based on the project structure.
    """
    base_dir = Path(__file__).parent.parent
    processed_dir = base_dir / "data" / "processed"
    
    return {
        "input_file": processed_dir / "cleaned_age_filtered.csv",
        "output_file": processed_dir / "cleaned_score_filtered.csv",
        "exclusion_counts_file": processed_dir / "exclusion_counts.json"
    }

def load_age_filtered_dataset(input_path: Path) -> pd.DataFrame:
    """
    Loads the age-filtered dataset.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading age-filtered dataset from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records")
    return df

def filter_by_score(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Filters the dataframe for non-null 'perseverative_errors' and 'categories_completed'.
    Returns the filtered dataframe and the count of excluded records.
    """
    initial_count = len(df)
    
    # Filter for non-null values in required columns
    mask = df['perseverative_errors'].notna() & df['categories_completed'].notna()
    filtered_df = df[mask]
    
    excluded_count = initial_count - len(filtered_df)
    
    logger.info(f"Filtered by score: {excluded_count} records excluded due to missing scores.")
    
    return filtered_df, excluded_count

def save_filtered_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """
    Saves the filtered dataframe to a CSV file.
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered dataset to {output_path} with {len(df)} records")

def update_exclusion_counts(excluded_count: int, counts_file: Path) -> None:
    """
    Updates the exclusion_counts.json file with the new exclusion count.
    """
    if not counts_file.exists():
        counts = {}
    else:
        with open(counts_file, 'r') as f:
            counts = json.load(f)
    
    key = "ERR_MISSING_SCORE"
    current_count = counts.get(key, 0)
    counts[key] = current_count + excluded_count
    
    with open(counts_file, 'w') as f:
        json.dump(counts, f, indent=2)
    
    logger.info(f"Updated exclusion counts: {key} = {counts[key]}")

def main() -> int:
    """
    Main entry point for Task T012b.
    """
    try:
        paths = get_config_paths()
        
        # Load input data
        df = load_age_filtered_dataset(paths["input_file"])
        
        # Filter by score
        filtered_df, excluded_count = filter_by_score(df)
        
        # Save filtered data
        save_filtered_dataset(filtered_df, paths["output_file"])
        
        # Update exclusion counts
        update_exclusion_counts(excluded_count, paths["exclusion_counts_file"])
        
        logger.info("Task T012b completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
