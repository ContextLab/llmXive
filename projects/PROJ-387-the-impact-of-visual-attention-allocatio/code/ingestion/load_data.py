import sys
import os
import argparse
import pandas as pd
from pathlib import Path
from utils.config import get_project_root, load_config
from utils.logger import get_logger

logger = get_logger(__name__)

def load_csv(file_path: Path) -> pd.DataFrame:
    """Load a CSV file into a DataFrame."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return pd.read_csv(file_path)

def load_edf(file_path: Path) -> pd.DataFrame:
    """
    Load an EDF file.
    Note: This is a placeholder. In a real implementation, 
    a specific library like `pyedflib` would be used.
    """
    logger.warning("EDF loading is not fully implemented. Returning empty DataFrame.")
    return pd.DataFrame()

def load_data(file_path: Path) -> pd.DataFrame:
    """Load data based on file extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return load_csv(file_path)
    elif suffix == ".edf":
        return load_edf(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

def main():
    parser = argparse.ArgumentParser(description="Load eye-tracking data")
    parser.add_argument("--input", type=str, required=True, help="Path to input file")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"File not found: {input_path}")
        sys.exit(1)

    try:
        df = load_data(input_path)
        logger.info(f"Successfully loaded {len(df)} rows from {input_path}")
        print(df.head())
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()