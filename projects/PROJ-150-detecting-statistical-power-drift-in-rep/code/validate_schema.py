import pandas as pd
import json
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ['year', 'effect_size', 'sample_size', 'field']

DEFAULT_INPUT_PATH = "data/raw/data.csv"
DEFAULT_OUTPUT_PATH = "data/derived/schema_validation.json"


class SchemaValidationError(Exception):
    """Raised when the downloaded data is missing required columns."""
    pass


def _ensure_raw_data(input_path):
    """
    Ensure the raw data file exists. If it does not, invoke the real
    data fetcher (code/download_data.py, T006) to obtain it from the
    verified HuggingFace source. No synthetic fallback is ever used;
    if the real fetch fails it raises DataFetchError / exits non-zero.
    """
    if os.path.exists(input_path):
        return
    logger.info(f"Raw data file {input_path} not found. Running real data fetcher (download_data.py).")
    from download_data import main as download_main
    download_main()
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Real data fetch completed but {input_path} still does not exist."
    )


def validate_schema(input_path=DEFAULT_INPUT_PATH, output_path=DEFAULT_OUTPUT_PATH):
    """
    Validate that the downloaded CSV contains the required columns.

    Writes a JSON report to output_path with keys:
      status, columns_found, and (if invalid) missing_columns.

    Raises:
        SchemaValidationError: if any required column is missing.
        FileNotFoundError: if the input file cannot be obtained.
    """
    _ensure_raw_data(input_path)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file {input_path} not found")

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV: {e}")

    columns_found = [str(c) for c in df.columns]
    missing = [col for col in REQUIRED_COLUMNS if col not in columns_found]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if missing:
        error_msg = f"Missing required columns: {missing}"
        logger.error(error_msg)
        with open(output_path, 'w') as f:
            json.dump({
                "status": "invalid",
                "columns_found": columns_found,
                "missing_columns": missing
            }, f, indent=2)
        raise SchemaValidationError(error_msg)

    logger.info(f"Schema validation passed. Columns found: {columns_found}")
    with open(output_path, 'w') as f:
        json.dump({
            "status": "valid",
            "columns_found": columns_found
        }, f, indent=2)
    logger.info(f"Schema validation report written to {output_path}")
    return {"status": "valid", "columns_found": columns_found}


if __name__ == "__main__":
    validate_schema(DEFAULT_INPUT_PATH, DEFAULT_OUTPUT_PATH)
