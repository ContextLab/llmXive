import os
import json
import logging
import pandas as pd
from pathlib import Path
from utils import setup_logging, log_info, log_warning, log_error

# Configure logging
logger = setup_logging()

def load_age_filtered_dataset(file_path: str) -> pd.DataFrame:
    """
    Load the age-filtered dataset from the specified CSV file.
    
    Args:
        file_path: Path to the CSV file containing age-filtered data.
        
    Returns:
        pandas DataFrame containing the loaded data.
        
    Raises:
        FileNotFoundError: If the specified file does not exist.
        pd.errors.ParserError: If the CSV file cannot be parsed.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Age filtered dataset not found at {file_path}")
    
    logger.info(f"Loading age filtered dataset from {file_path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} records from age filtered dataset")
    return df

def filter_by_score(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    Filter the dataset to keep only records with non-null 
    perseverative_errors and categories_completed.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Tuple of (filtered DataFrame, count of excluded records).
    """
    original_count = len(df)
    
    # Check for required columns
    required_cols = ['perseverative_errors', 'categories_completed']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in score filtering: {missing_cols}")
    
    # Filter for non-null values in both score columns
    mask = df['perseverative_errors'].notna() & df['categories_completed'].notna()
    filtered_df = df[mask]
    
    excluded_count = original_count - len(filtered_df)
    
    logger.info(f"Score filtering: {original_count} -> {len(filtered_df)} records")
    logger.info(f"Excluded {excluded_count} records due to missing scores")
    
    return filtered_df, excluded_count

def save_filtered_dataset(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the filtered dataset to a CSV file.
    
    Args:
        df: DataFrame to save.
        output_path: Path where the CSV file will be written.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(path, index=False)
    logger.info(f"Saved filtered dataset to {output_path}")

def update_exclusion_counts(exclusion_key: str, count: int, counts_file_path: str) -> None:
    """
    Update the exclusion counts JSON file with the new exclusion count.
    
    Args:
        exclusion_key: Key to use in the JSON object (e.g., 'ERR_MISSING_SCORE').
        count: Number of excluded records.
        counts_file_path: Path to the exclusion counts JSON file.
    """
    counts_file = Path(counts_file_path)
    
    # Load existing counts or create new dict
    if counts_file.exists():
        with open(counts_file, 'r') as f:
            counts = json.load(f)
    else:
        counts = {}
    
    # Update with new count
    counts[exclusion_key] = count
    
    # Ensure parent directory exists
    counts_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write updated counts
    with open(counts_file, 'w') as f:
        json.dump(counts, f, indent=2)
    
    logger.info(f"Updated exclusion counts: {exclusion_key} = {count}")

def main():
    """
    Main function to execute the score exclusion task (T012b).
    
    Reads the age-filtered dataset, filters out records with missing scores,
    saves the filtered dataset, and updates the exclusion counts.
    """
    # Define paths
    config = {
        'age_filtered_input': 'data/processed/cleaned_age_filtered.csv',
        'score_filtered_output': 'data/processed/cleaned_score_filtered.csv',
        'exclusion_counts_file': 'data/processed/exclusion_counts.json',
        'exclusion_key': 'ERR_MISSING_SCORE'
    }
    
    try:
        # Load the age-filtered dataset
        df = load_age_filtered_dataset(config['age_filtered_input'])
        
        # Filter by score (non-null perseverative_errors and categories_completed)
        filtered_df, excluded_count = filter_by_score(df)
        
        # Save the filtered dataset
        save_filtered_dataset(filtered_df, config['score_filtered_output'])
        
        # Update exclusion counts
        update_exclusion_counts(
            config['exclusion_key'], 
            excluded_count, 
            config['exclusion_counts_file']
        )
        
        logger.info(f"T012b Score Exclusion completed successfully. "
                   f"Excluded {excluded_count} records.")
        
    except FileNotFoundError as e:
        log_error(f"File not found: {e}")
        raise
    except ValueError as e:
        log_error(f"Validation error: {e}")
        raise
    except Exception as e:
        log_error(f"Unexpected error during score exclusion: {e}")
        raise

if __name__ == '__main__':
    main()
