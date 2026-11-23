"""
Task T028d: Derive Time-of-Day from timestamps.

Extracts the hour of the day from the 'timestamp' column of the input data,
categorizes it into time-of-day bins (Morning, Afternoon, Evening, Night),
and saves the result to a CSV file.

Dependencies: T017-run (filtered moral machine data).
"""
import os
import sys
import logging
import argparse
from pathlib import Path
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/logs/derive_time_of_day.log')
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='Derive time-of-day from timestamps.')
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to the input Parquet file (merged dataset).'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Path to the output CSV file.'
    )
    return parser.parse_args()

def ensure_directories(file_path: Path):
    """Ensure the directory for the given file path exists."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

def categorize_hour(hour: int) -> str:
    """
    Categorize an hour of the day into a time-of-day bin.
    
    Args:
        hour (int): Hour of the day (0-23).
    
    Returns:
        str: Category string ('Morning', 'Afternoon', 'Evening', 'Night').
    """
    if 5 <= hour < 12:
        return 'Morning'
    elif 12 <= hour < 17:
        return 'Afternoon'
    elif 17 <= hour < 21:
        return 'Evening'
    else:
        return 'Night'

def derive_time_of_day(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive time-of-day categories from the timestamp column.
    
    Args:
        df (pd.DataFrame): Input DataFrame with a 'timestamp' column.
    
    Returns:
        pd.DataFrame: DataFrame with an added 'time_of_day' column.
    """
    if 'timestamp' not in df.columns:
        raise ValueError("Input DataFrame must contain a 'timestamp' column.")
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Extract hour
    df['hour'] = df['timestamp'].dt.hour
    
    # Categorize hour
    df['time_of_day'] = df['hour'].apply(categorize_hour)
    
    # Select relevant columns for output
    # Assuming we want to keep participant_id to link back, plus the new field
    output_cols = ['participant_id', 'timestamp', 'hour', 'time_of_day']
    # Check if participant_id exists, otherwise just output the derived columns
    if 'participant_id' in df.columns:
        return df[output_cols]
    else:
        # Fallback if participant_id is missing (unlikely given task deps)
        return df[['timestamp', 'hour', 'time_of_day']]

def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    ensure_directories(output_path)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} records.")
    logger.info(f"Columns: {list(df.columns)}")

    if df.empty:
        logger.warning("Input DataFrame is empty. Creating empty output.")
        df_result = pd.DataFrame(columns=['participant_id', 'timestamp', 'hour', 'time_of_day'])
    else:
        logger.info("Deriving time-of-day categories...")
        df_result = derive_time_of_day(df)

    logger.info(f"Saving derived time-of-day data to {output_path}")
    df_result.to_csv(output_path, index=False)

    logger.info("Time-of-day derivation complete.")
    print(f"Success: Output written to {output_path}")

if __name__ == '__main__':
    main()
