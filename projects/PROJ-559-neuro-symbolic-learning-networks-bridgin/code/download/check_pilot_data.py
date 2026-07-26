"""
check_pilot_data.py

Checks for the existence and validity of the human pilot dataset.

Deliverable:
  - Exits with code 0.
  - Prints a JSON status flag to stdout:
    {"has_human_data": true} if the file exists and has >= 50 records.
    {"has_human_data": false} if the file is missing, invalid, or has < 50 records.
  - Does NOT exit with code 1 if data is missing (allows T031c to proceed).
"""
import os
import sys
import json
import logging
import argparse
import pandas as pd

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

DEFAULT_DATA_PATH = "data/pilot/raw_pilot_data.csv"
MIN_RECORDS_THRESHOLD = 50

def check_pilot_data(data_path: str) -> bool:
    """
    Checks if the pilot data file exists and contains at least MIN_RECORDS_THRESHOLD records.

    Args:
        data_path: Path to the CSV file.

    Returns:
        True if valid (exists and >= 50 records), False otherwise.
    """
    if not os.path.exists(data_path):
        logger.warning(f"Pilot data file not found at: {data_path}")
        return False

    try:
        # Attempt to load the CSV
        # We assume the file is a standard CSV. If it's empty or malformed, this will raise.
        df = pd.read_csv(data_path)
        
        record_count = len(df)
        logger.info(f"Loaded pilot data: {record_count} records found.")

        if record_count < MIN_RECORDS_THRESHOLD:
            logger.warning(
                f"Pilot data has {record_count} records, which is less than the "
                f"minimum required threshold of {MIN_RECORDS_THRESHOLD}."
            )
            return False

        # Basic validation: check if it's not just a header with no data
        if df.empty:
            logger.warning("Pilot data file is empty or contains only headers.")
            return False

        return True

    except pd.errors.EmptyDataError:
        logger.error(f"Pilot data file at {data_path} is empty.")
        return False
    except pd.errors.ParserError as e:
        logger.error(f"Failed to parse pilot data file at {data_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while validating pilot data: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Check for existence and validity of the human pilot dataset."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=DEFAULT_DATA_PATH,
        help=f"Path to the pilot data CSV file (default: {DEFAULT_DATA_PATH})"
    )
    args = parser.parse_args()

    is_valid = check_pilot_data(args.data_path)

    # Construct the result JSON
    result = {
        "has_human_data": is_valid
    }

    # Output JSON to stdout for downstream parsing
    print(json.dumps(result))

    # Always exit 0 to allow the pipeline to continue to T031c if needed
    sys.exit(0)

if __name__ == "__main__":
    main()
