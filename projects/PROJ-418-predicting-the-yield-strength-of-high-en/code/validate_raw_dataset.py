"""
T098 – Validate the raw HEA yield‑strength dataset against the
JSON‑Schema defined in ``contracts/dataset.schema.yaml``.
The script will:
  1. Ensure the raw CSV exists (download it if necessary).
  2. Load the schema.
  3. Validate every row of the CSV against the schema.
  4. Exit with status 0 on success or raise a descriptive exception on failure.
"""
import os
import logging
from typing import Any, Dict, List

import pandas as pd
import yaml
import jsonschema

from utils.logging import get_logger
from data.download import download_dataset

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def _ensure_raw_csv() -> str:
    """
    Guarantees that ``data/raw/heas_raw.csv`` exists.
    If the file is missing, the official download routine is invoked.
    Returns the absolute path to the CSV file.
    """
    raw_path = os.path.join("data", "raw", "heas_raw.csv")
    if not os.path.isfile(raw_path):
        logger = get_logger()
        logger.info("Raw dataset not found – initiating download.")
        download_dataset()  # Expected to write to the same location
        if not os.path.isfile(raw_path):
            raise FileNotFoundError(
                f"download_dataset() did not create the expected file: {raw_path}"
            )
    return raw_path

def _load_schema() -> Dict[str, Any]:
    """
    Loads the dataset schema from ``contracts/dataset.schema.yaml``.
    """
    schema_path = os.path.join("contracts", "dataset.schema.yaml")
    if not os.path.isfile(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    if not isinstance(schema, dict):
        raise ValueError("Loaded schema is not a mapping/dictionary.")
    return schema

def _validate_dataframe(df: pd.DataFrame, schema: Dict[str, Any]) -> None:
    """
    Validates each record of ``df`` against ``schema``.
    Raises ``jsonschema.ValidationError`` on the first failure,
    including row index information for easy debugging.
    """
    validator = jsonschema.Draft7Validator(schema)

    errors: List[jsonschema.ValidationError] = []
    for idx, row in df.iterrows():
        # Convert the pandas Series to a plain dict, dropping NaNs (they are
        # represented as ``null`` in JSON which the schema can handle).
        record: Dict[str, Any] = row.where(pd.notnull(row)).to_dict()
        for error in validator.iter_errors(record):
            # Attach row index to the error message for context.
            error_message = f"Row {idx}: {error.message}"
            errors.append(jsonschema.ValidationError(error_message, instance=record))

    if errors:
        # Aggregate messages into a single exception for clearer CLI output.
        combined_message = "\n".join(str(e) for e in errors)
        raise jsonschema.ValidationError(
            f"Dataset validation failed with {len(errors)} error(s):\n{combined_message}"
        )

# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Executes the validation workflow.
    """
    logger = get_logger()
    logger.info("Starting raw dataset validation (T098).")

    # 1. Ensure CSV exists
    csv_path = _ensure_raw_csv()
    logger.debug("Raw CSV located at %s", csv_path)

    # 2. Load data
    df = pd.read_csv(csv_path)
    logger.info("Loaded raw dataset with %d rows and %d columns.", df.shape[0], df.shape[1])

    # 3. Load schema
    schema = _load_schema()
    logger.debug("Schema loaded successfully.")

    # 4. Validate
    _validate_dataframe(df, schema)
    logger.info("Raw dataset validation passed – all rows conform to the schema.")

if __name__ == "__main__":
    main()
