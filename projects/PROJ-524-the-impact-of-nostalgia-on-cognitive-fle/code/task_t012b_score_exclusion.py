"""
T012b: Score Exclusion Task

Filters the age-cleaned dataset for non-null 'perseverative_errors' and 'categories_completed'.
Writes the filtered dataset to data/processed/cleaned_score_filtered.csv.
Updates data/processed/exclusion_counts.json with the count of excluded records under 'ERR_MISSING_SCORE'.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path

# Import utilities from the project's existing API surface
from utils import setup_logging, log_info, log_warning, log_error
from config import get_config, ensure_dirs

# Setup logging
logger = setup_logging()

def load_age_filtered_dataset(config: dict) -> pd.DataFrame:
    """Load the age-filtered dataset from T012a."""
    input_path = Path(config['paths']['processed_data']) / 'cleaned_age_filtered.csv'
    
    if not input_path.exists():
        log_error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    log_info(f"Loading age-filtered dataset from {input_path}")
    df = pd.read_csv(input_path)
    return df

def filter_by_score(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Filter the dataframe for non-null 'perseverative_errors' and 'categories_completed'.
    
    Returns:
        tuple: (filtered_df, exclusion_count)
    """
    required_columns = ['perseverative_errors', 'categories_completed']
    
    # Check if required columns exist
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        log_error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Count rows before filtering
    initial_count = len(df)
    
    # Filter for non-null values in both columns
    mask = df['perseverative_errors'].notna() & df['categories_completed'].notna()
    filtered_df = df[mask]
    
    # Calculate exclusion count
    exclusion_count = initial_count - len(filtered_df)
    
    if exclusion_count > 0:
        log_warning(f"Excluded {exclusion_count} records due to missing scores")
    else:
        log_info("No records excluded due to missing scores")
    
    return filtered_df, exclusion_count

def save_filtered_dataset(df: pd.DataFrame, config: dict) -> Path:
    """Save the filtered dataset to the processed directory."""
    output_path = Path(config['paths']['processed_data']) / 'cleaned_score_filtered.csv'
    
    df.to_csv(output_path, index=False)
    log_info(f"Saved filtered dataset to {output_path}")
    return output_path

def update_exclusion_counts(exclusion_count: int, config: dict) -> Path:
    """Update the exclusion_counts.json file with the new exclusion count."""
    counts_path = Path(config['paths']['processed_data']) / 'exclusion_counts.json'
    
    # Load existing counts if the file exists
    if counts_path.exists():
        with open(counts_path, 'r') as f:
            counts = json.load(f)
    else:
        counts = {}
    
    # Update the count for ERR_MISSING_SCORE
    current_count = counts.get('ERR_MISSING_SCORE', 0)
    counts['ERR_MISSING_SCORE'] = current_count + exclusion_count
    
    # Save updated counts
    with open(counts_path, 'w') as f:
        json.dump(counts, f, indent=2)
    
    log_info(f"Updated exclusion counts: ERR_MISSING_SCORE = {counts['ERR_MISSING_SCORE']}")
    return counts_path

def main():
    """Main entry point for T012b."""
    log_info("Starting T012b: Score Exclusion")
    
    # Get configuration
    config = get_config()
    ensure_dirs(config)
    
    try:
        # Load age-filtered dataset
        df = load_age_filtered_dataset(config)
        log_info(f"Loaded {len(df)} records from age-filtered dataset")
        
        # Filter by score
        filtered_df, exclusion_count = filter_by_score(df)
        log_info(f"Filtered dataset contains {len(filtered_df)} records")
        
        # Save filtered dataset
        save_filtered_dataset(filtered_df, config)
        
        # Update exclusion counts
        update_exclusion_counts(exclusion_count, config)
        
        log_info("T012b: Score Exclusion completed successfully")
        
    except Exception as e:
        log_error(f"Error during T012b execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()