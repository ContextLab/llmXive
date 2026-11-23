import os
import sys
import argparse
import json
import glob
from pathlib import Path

import pandas as pd

# Import from sibling modules as per API surface
from utils.logger import get_logger
from analysis.data_cleaner import DataCleaner

logger = get_logger(__name__)

def load_raw_sessions(raw_dir: str = "data/raw") -> pd.DataFrame:
    """
    Load all JSON session files from the raw directory into a single DataFrame.
    """
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        logger.error(f"Raw data directory {raw_dir} does not exist.")
        return pd.DataFrame()

    json_files = list(raw_path.glob("*.json"))
    if not json_files:
        logger.warning(f"No JSON files found in {raw_dir}.")
        return pd.DataFrame()

    records = []
    for f in json_files:
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                # Ensure consistent keys even if missing in some files
                records.append(data)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to read {f}: {e}")
            continue

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    logger.info(f"Loaded {len(df)} session records from {raw_dir}")
    return df

def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce strict data types for the analysis pipeline.
    - participant_id: str
    - interface_type: str (traditional|explainable)
    - completion_time_seconds: float (>= 0)
    - error_count: int (>= 0)
    - sus_score: int (0-100)
    - explanation_engagement_time_seconds: float (>= 0)
    - status: str
    """
    logger.info("Coercing data types...")
    
    # Ensure string columns are strings
    str_cols = ['participant_id', 'interface_type', 'status']
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)

    # Numeric coercions with validation
    float_cols = ['completion_time_seconds', 'explanation_engagement_time_seconds']
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            # Ensure non-negative
            df.loc[df[col] < 0, col] = 0.0

    int_cols = ['error_count', 'sus_score']
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            df[col] = df[col].astype(int)
            # Ensure non-negative
            df.loc[df[col] < 0, col] = 0
            # Ensure SUS max 100
            if col == 'sus_score':
                df.loc[df[col] > 100, col] = 100

    return df

def main():
    parser = argparse.ArgumentParser(description="Run the data cleaning pipeline.")
    parser.add_argument("--input", type=str, default="data/raw", help="Directory containing raw JSON session files.")
    parser.add_argument("--output", type=str, default="data/processed/cleaned_sessions.csv", help="Output path for the cleaned CSV.")
    parser.add_argument("--exclude-incomplete", action="store_true", default=True, help="Exclude sessions with status='incomplete'.")
    parser.add_argument("--impute-sus", action="store_true", default=True, help="Impute SUS scores if <= 1 item missing.")
    
    args = parser.parse_args()

    logger.info(f"Starting cleaning pipeline. Input: {args.input}, Output: {args.output}")

    # 1. Load Raw Data
    df = load_raw_sessions(args.input)
    if df.empty:
        logger.error("No data loaded. Aborting.")
        sys.exit(1)

    # 2. Apply Exclusion Logic (T021a)
    if args.exclude_incomplete:
        initial_count = len(df)
        df = df[df['status'] != 'incomplete']
        logger.info(f"Excluded {initial_count - len(df)} incomplete sessions.")

    # 3. Apply Imputation Logic (T021b)
    # Note: The DataCleaner class handles the specific imputation logic per task description
    cleaner = DataCleaner()
    if args.impute_sus:
        df = cleaner.impute_sus_scores(df)

    # 4. Coerce Types
    df = coerce_types(df)

    # 5. Ensure Output Directory Exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 6. Write Output
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df)} cleaned records to {args.output}")

if __name__ == "__main__":
    main()
