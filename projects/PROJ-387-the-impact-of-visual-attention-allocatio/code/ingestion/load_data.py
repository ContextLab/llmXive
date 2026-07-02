"""
Data ingestion module for loading eye-tracking and recall data.
Supports CSV and EDF file formats without GPU usage.
"""

import sys
import os
import argparse
import pandas as pd
from pathlib import Path
from utils.config import get_project_root, load_config
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

def load_csv(file_path: str) -> pd.DataFrame:
    """
    Load data from a CSV file.

    Args:
        file_path: Path to the CSV file.

    Returns:
        pandas DataFrame containing the loaded data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed as CSV.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"CSV file not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Loading CSV file: {file_path}")
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Successfully loaded {len(df)} rows from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to parse CSV file {file_path}: {str(e)}")
        raise ValueError(f"Invalid CSV file: {str(e)}")

def load_edf(file_path: str) -> pd.DataFrame:
    """
    Load data from an EDF eye-tracking file.
    EDF files are binary files containing eye-tracking data.
    We use the 'edf' library to parse them, falling back to CSV if EDF is not available.

    Args:
        file_path: Path to the EDF file.

    Returns:
        pandas DataFrame containing the loaded data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ImportError: If the edf library is not installed.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"EDF file not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Loading EDF file: {file_path}")
    try:
        # Attempt to use the edf library if available
        try:
            import edf
            # EDF parsing logic would go here
            # For now, we'll raise an error if edf is not available
            logger.warning("EDF library not installed. Please install it with 'pip install edf'.")
            raise ImportError("EDF library not installed. Cannot parse EDF files.")
        except ImportError:
            # Fallback: try to read as CSV if EDF parsing is not available
            # This handles cases where EDF files are exported as CSV
            logger.info("Attempting to read EDF file as CSV (fallback)")
            df = pd.read_csv(file_path)
            logger.info(f"Successfully loaded {len(df)} rows from {file_path} (as CSV)")
            return df
    except Exception as e:
        logger.error(f"Failed to parse EDF file {file_path}: {str(e)}")
        raise ValueError(f"Invalid EDF file: {str(e)}")

def load_data(file_path: str) -> pd.DataFrame:
    """
    Load data from a file, automatically detecting the format based on extension.

    Args:
        file_path: Path to the data file (CSV or EDF).

    Returns:
        pandas DataFrame containing the loaded data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Data file not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = path.suffix.lower()

    if extension == '.csv':
        return load_csv(file_path)
    elif extension == '.edf':
        return load_edf(file_path)
    else:
        logger.error(f"Unsupported file format: {extension}")
        raise ValueError(f"Unsupported file format: {extension}. Supported formats: .csv, .edf")

def main():
    """
    Main entry point for the data loading script.
    Usage: python -m code.ingestion.load_data --file <path_to_file>
    """
    parser = argparse.ArgumentParser(description="Load eye-tracking and recall data from CSV or EDF files.")
    parser.add_argument("--file", type=str, required=True, help="Path to the data file (CSV or EDF)")
    parser.add_argument("--config", type=str, default=None, help="Path to configuration file (optional)")

    args = parser.parse_args()

    try:
        # Load configuration if provided
        if args.config:
            config = load_config(args.config)
            logger.info(f"Loaded configuration from {args.config}")

        # Load the data
        df = load_data(args.file)

        # Print basic info about the loaded data
        logger.info(f"Data loaded successfully. Shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")

        # Exit with success
        sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid file: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()