"""
T012b: Score Exclusion Logic
Filters the age-filtered dataset for non-null cognitive metrics (perseverative_errors, categories_completed).
Writes filtered data and updates exclusion counts.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from utils import setup_logging, log_info, log_warning, log_error

# Configure logging
logger = setup_logging("T012b")

def get_config_paths() -> Dict[str, Path]:
    """Retrieve standard project paths."""
    base = Path(__file__).resolve().parent.parent
    return {
        "input": base / "data" / "processed" / "cleaned_age_filtered.csv",
        "output": base / "data" / "processed" / "cleaned_score_filtered.csv",
        "counts": base / "data" / "processed" / "exclusion_counts.json",
    }

def load_age_filtered_dataset(input_path: Path) -> pd.DataFrame:
    """Load the age-filtered dataset."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading age-filtered dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    required_cols = ["perseverative_errors", "categories_completed"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input: {missing_cols}")
    
    return df

def filter_by_score(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Filter rows where both 'perseverative_errors' and 'categories_completed' are non-null.
    Returns (filtered_df, count_excluded).
    """
    initial_count = len(df)
    
    # Filter for non-null values in both score columns
    mask = df["perseverative_errors"].notna() & df["categories_completed"].notna()
    filtered_df = df[mask]
    
    excluded_count = initial_count - len(filtered_df)
    
    if excluded_count > 0:
        log_warning(f"Excluded {excluded_count} records due to missing score data (ERR_MISSING_SCORE)")
    else:
        log_info("No records excluded due to missing score data.")
        
    return filtered_df, excluded_count

def save_filtered_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Save the filtered dataframe to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log_info(f"Saved filtered dataset to {output_path}")

def update_exclusion_counts(excluded_count: int, counts_path: Path) -> None:
    """Update the exclusion_counts.json file with the new exclusion count."""
    counts_path.parent.mkdir(parents=True, exist_ok=True)
    
    if counts_path.exists():
        with open(counts_path, "r") as f:
            counts = json.load(f)
    else:
        counts = {}
    
    key = "ERR_MISSING_SCORE"
    current = counts.get(key, 0)
    counts[key] = current + excluded_count
    
    with open(counts_path, "w") as f:
        json.dump(counts, f, indent=2)
    
    log_info(f"Updated exclusion counts: {key} = {counts[key]}")

def main() -> None:
    """Main entry point for T012b."""
    paths = get_config_paths()
    
    try:
        df = load_age_filtered_dataset(paths["input"])
        filtered_df, excluded_count = filter_by_score(df)
        save_filtered_dataset(filtered_df, paths["output"])
        update_exclusion_counts(excluded_count, paths["counts"])
        
        log_info("T012b completed successfully.")
        
    except FileNotFoundError as e:
        log_error(f"File not found: {e}")
        raise
    except ValueError as e:
        log_error(f"Data validation error: {e}")
        raise
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()