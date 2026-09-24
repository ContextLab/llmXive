import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
import yaml

logger = logging.getLogger(__name__)

def log_setup():
    """Configure logging to stdout."""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        stream=sys.stdout
    )

def load_schema_contract() -> Dict[str, Any]:
    """Load the dataset schema contract."""
    schema_path = Path("contracts/dataset.schema.yaml")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema contract not found at {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_structure(schema: Dict[str, Any]) -> bool:
    """Validate schema structure."""
    required = ['switching_index', 'cognitive_flexibility_score', 'age', 'total_screen_time', 'num_platforms', 'switching_frequency']
    return all(col in schema.get('columns', []) for col in required)

def load_all_raw_data() -> List[pd.DataFrame]:
    """Load all raw CSV files from data/raw/."""
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        raise FileNotFoundError("data/raw directory not found")
    
    dfs = []
    for csv_file in raw_dir.glob("*_raw.csv"):
        logger.info(f"Loading {csv_file}")
        df = pd.read_csv(csv_file)
        dfs.append(df)
    
    if not dfs:
        raise FileNotFoundError("No raw CSV files found in data/raw/")
    
    return dfs

def engineer_switching_index(df: pd.DataFrame) -> pd.DataFrame:
    """Compute switching_index = num_platforms * switching_frequency."""
    df['switching_index'] = df['num_platforms'] * df['switching_frequency']
    logger.info(f"Computed switching_index for {len(df)} rows")
    return df

def handle_missing_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing outcomes by excluding rows and logging exclusion count."""
    initial_count = len(df)
    # Drop rows where cognitive_flexibility_score is missing
    df = df.dropna(subset=['cognitive_flexibility_score'])
    excluded = initial_count - len(df)
    if excluded > 0:
        logger.info(f"Excluded {excluded} rows due to missing cognitive_flexibility_score")
    return df

def validate_and_save(df: pd.DataFrame, output_path: Path):
    """Validate and save the final cleaned dataset."""
    schema = load_schema_contract()
    required_cols = schema.get('columns', [])
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in final output: {missing}")
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")

def main():
    """Main entry point for variable engineering."""
    log_setup()
    logger.info("Starting variable engineering pipeline.")

    # Load all raw data
    dfs = load_all_raw_data()
    
    # Combine datasets
    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined {len(dfs)} datasets into {len(combined_df)} rows")

    # Engineer variables
    combined_df = engineer_switching_index(combined_df)

    # Handle missing outcomes
    combined_df = handle_missing_outcomes(combined_df)

    # Ensure output directory exists
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    output_path = Path("data/processed/participants_cleaned.csv")

    # Validate and save
    validate_and_save(combined_df, output_path)

    logger.info("Variable engineering complete.")

if __name__ == "__main__":
    main()
