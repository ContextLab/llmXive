import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from logging_config import get_logger, info, warning, error, debug

# Constants
DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "processed"
OUTPUT_FILE = RAW_DIR / "learners_raw_filtered.csv"
INPUT_FILE = RAW_DIR / "learners_raw.csv"

def load_raw_learner_data(input_path: Path) -> pd.DataFrame:
    """
    Load the raw learner data from the specified path.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        DataFrame containing the raw learner data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or contains no data.
    """
    if not input_path.exists():
        error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    df = pd.read_csv(input_path)
    
    if df.empty:
        error(f"Input file {input_path} is empty.")
        raise ValueError(f"Input file {input_path} is empty.")
        
    info(f"Loaded {len(df):,} records from {input_path}")
    return df

def filter_no_forum_interactions(df: pd.DataFrame, log_path: Path | None = None) -> tuple[pd.DataFrame, int]:
    """
    Filter out learners who have no recorded forum interactions.
    
    This function identifies learners without forum events (cannot compute interval)
    and excludes them from the dataset. It logs the exclusion count.
    
    Args:
        df: DataFrame containing learner records with 'event_type' column.
        log_path: Optional path to write a detailed exclusion log.
        
    Returns:
        A tuple containing:
            - Filtered DataFrame (learners with at least one forum interaction)
            - Count of excluded learners
    """
    initial_count = len(df)
    info(f"Starting forum interaction filter. Initial records: {initial_count:,}")
    
    # Identify learners with at least one forum interaction
    # Assuming 'event_type' column exists and contains 'forum' or similar
    # We need to check if there are any rows where event_type indicates a forum event
    # and group by learner_id to find those with at least one such event.
    
    # First, check if required columns exist
    required_cols = ['learner_id', 'event_type']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        error(f"Missing required columns for forum filtering: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Filter for forum events
    forum_events = df[df['event_type'].str.lower().str.contains('forum', na=False)]
    
    # Get unique learner IDs that have forum interactions
    learners_with_forum = forum_events['learner_id'].unique()
    
    # Filter the main dataframe to keep only learners with forum interactions
    filtered_df = df[df['learner_id'].isin(learners_with_forum)].copy()
    
    excluded_count = initial_count - len(filtered_df)
    excluded_learners = initial_count - len(learners_with_forum) # Count unique learners excluded
    
    info(f"Forum interaction filter complete.")
    info(f"  - Learners with forum interactions: {len(learners_with_forum):,}")
    info(f"  - Learners excluded (no forum): {excluded_learners:,}")
    info(f"  - Total records excluded: {excluded_count:,}")
    info(f"  - Remaining records: {len(filtered_df):,}")
    
    # Log detailed exclusion info if requested
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'w') as f:
            f.write(f"Forum Interaction Exclusion Report\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Initial records: {initial_count:,}\n")
            f.write(f"Final records: {len(filtered_df):,}\n")
            f.write(f"Total records excluded: {excluded_count:,}\n")
            f.write(f"Unique learners excluded: {excluded_learners:,}\n")
            f.write(f"\nExcluded Learner IDs (first 100):\n")
            excluded_ids = set(df['learner_id']) - set(learners_with_forum)
            for i, lid in enumerate(sorted(excluded_ids)[:100]):
                f.write(f"  {lid}\n")
            if len(excluded_ids) > 100:
                f.write(f"  ... and {len(excluded_ids) - 100} more\n")
        info(f"Exclusion log written to: {log_path}")
        
    return filtered_df, excluded_learners

def save_filtered_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the filtered DataFrame to a CSV file.
    
    Args:
        df: DataFrame to save.
        output_path: Path where the CSV file will be saved.
        
    Raises:
        IOError: If the file cannot be written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        df.to_csv(output_path, index=False)
        info(f"Filtered data saved to: {output_path}")
        info(f"  - Records saved: {len(df):,}")
        info(f"  - Columns: {list(df.columns)}")
    except Exception as e:
        error(f"Failed to save filtered data to {output_path}: {e}")
        raise IOError(f"Failed to save filtered data: {e}")

def main():
    """
    Main entry point for the apply_exclusions script.
    
    This script:
    1. Loads the raw learner data from data/processed/learners_raw.csv
    2. Filters out learners with no recorded forum interactions
    3. Logs the exclusion count and details
    4. Saves the filtered data to data/processed/learners_raw_filtered.csv
    """
    # Setup logger
    logger = get_logger(__name__)
    logger.info("Starting apply_exclusions script")
    
    # Define paths
    input_path = INPUT_FILE
    output_path = OUTPUT_FILE
    exclusion_log_path = DATA_DIR / "cache" / "forum_exclusion_log.txt"
    
    # Ensure directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        df = load_raw_learner_data(input_path)
        
        # Apply filter
        filtered_df, excluded_count = filter_no_forum_interactions(df, exclusion_log_path)
        
        # Save results
        save_filtered_data(filtered_df, output_path)
        
        logger.info("apply_exclusions script completed successfully")
        return 0
        
    except FileNotFoundError as e:
        error(f"File not found: {e}")
        return 1
    except ValueError as e:
        error(f"Value error: {e}")
        return 1
    except Exception as e:
        error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
