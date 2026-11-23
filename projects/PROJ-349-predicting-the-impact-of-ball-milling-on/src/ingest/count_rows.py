"""
T015b: Calculate Aggregated Count
Computes the row count of the merged dataframe (output of T015) and writes it
to data/processed/row_count.json with key 'count'.
"""
import json
import logging
import sys
from pathlib import Path

import pandas as pd

# Add project root to path if running as script
if "code" in sys.path[0]:
    sys.path.insert(0, str(Path(sys.path[0]).parent))
elif "" in sys.path:
    sys.path.insert(0, "")

from src.utils.logger import get_module_logger

# Ensure output directory exists
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "row_count.json"
INPUT_FILE = Path("data/raw/merged_dataset.parquet")

logger = get_module_logger(__name__)

def calculate_row_count(input_path: Path, output_path: Path) -> int:
    """
    Reads a Parquet file, counts rows, and writes the count to a JSON file.

    Args:
        input_path: Path to the input Parquet file.
        output_path: Path to the output JSON file.

    Returns:
        The number of rows in the dataset.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is not a valid Parquet or cannot be read.
    """
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Reading merged dataset from {input_path}...")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to read Parquet file: {e}")
        raise ValueError(f"Failed to read Parquet file: {e}")

    count = len(df)
    logger.info(f"Merged dataset contains {count} rows.")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing row count to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"count": count}, f, indent=2)

    logger.info(f"Successfully wrote row count ({count}) to {output_path}")
    return count

def main():
    """Main entry point for the row counting script."""
    try:
        calculate_row_count(INPUT_FILE, OUTPUT_FILE)
        logger.info("T015b completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during row counting: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()