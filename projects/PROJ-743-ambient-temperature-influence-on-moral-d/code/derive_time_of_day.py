"""
T028d: Derive Time-of-Day from timestamps.

Extracts the hour of day from the 'timestamp' column in the filtered Moral Machine
dataset and categorizes it into meaningful periods (Morning, Afternoon, Evening, Night).
Saves the resulting mapping to data/processed/time_of_day.csv.

Dependencies: T017-run (filtered data must exist).
"""
import os
import sys
import logging
import argparse
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add parent directory to path to allow imports if run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path_env_override

def parse_args():
    parser = argparse.ArgumentParser(description="Derive time-of-day categories from timestamps.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/filtered_moral_machine.parquet",
        help="Path to the filtered Moral Machine dataset (output of T017-run).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/time_of_day.csv",
        help="Path to save the derived time-of-day CSV.",
    )
    return parser.parse_args()

def ensure_directories(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

def categorize_hour(hour: int) -> str:
    """
    Categorize an integer hour (0-23) into a time-of-day string.
    
    Definitions:
    - Morning: 06:00 - 11:59
    - Afternoon: 12:00 - 17:59
    - Evening: 18:00 - 23:59
    - Night: 00:00 - 05:59
    """
    if 6 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 18:
        return "Afternoon"
    elif 18 <= hour < 24:
        return "Evening"
    else:
        return "Night"

def derive_time_of_day(input_path: Path, output_path: Path):
    logger = logging.getLogger("derive_time_of_day")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    try:
        # Try loading parquet first, fallback to csv if needed
        if input_path.suffix == '.parquet':
            df = pd.read_parquet(input_path)
        elif input_path.suffix == '.csv':
            df = pd.read_csv(input_path)
        else:
            # Generic load attempt
            df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        raise

    # Ensure timestamp column exists
    if 'timestamp' not in df.columns:
        raise ValueError(f"Input file missing required column 'timestamp'. Columns: {df.columns.tolist()}")

    logger.info(f"Processing {len(df)} records")

    # Parse timestamps if they are strings
    if df['timestamp'].dtype == 'object':
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Drop rows where timestamp could not be parsed
    initial_count = len(df)
    df = df.dropna(subset=['timestamp'])
    dropped_count = initial_count - len(df)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} records with invalid timestamps.")

    # Extract hour
    df['hour'] = df['timestamp'].dt.hour

    # Categorize
    df['time_of_day'] = df['hour'].apply(categorize_hour)

    # Select relevant columns for output
    # We include participant_id to allow merging back if needed, plus the derived fields
    output_cols = ['participant_id', 'timestamp', 'hour', 'time_of_day']
    # Filter to only existing columns in case participant_id was dropped in previous steps
    available_cols = [c for c in output_cols if c in df.columns]
    
    result_df = df[available_cols].copy()

    logger.info(f"Saving derived time-of-day data to {output_path}")
    ensure_directories(output_path)
    result_df.to_csv(output_path, index=False)

    logger.info(f"Successfully derived time-of-day for {len(result_df)} records.")
    return len(result_df)

def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    # Setup logging
    log_dir = Path("results/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "derive_time_of_day.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger("derive_time_of_day")

    try:
        count = derive_time_of_day(input_path, output_path)
        logger.info(f"Task completed. Output saved to {output_path}")
    except Exception as e:
        logger.error(f"Task failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
