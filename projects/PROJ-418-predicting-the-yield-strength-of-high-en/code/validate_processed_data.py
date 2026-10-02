"""
Validation script for the processed descriptor artefact
``data/processed/hea_descriptors.csv``.

The contract file ``contracts/processed_data.schema.yaml`` defines the
required columns, types and any additional constraints.  This script loads
the schema, reads the CSV with pandas, converts each row to a plain
``dict`` and validates it against the JSON‑Schema using ``jsonschema``.

If validation succeeds the script exits with status 0; otherwise a
``jsonschema.ValidationError`` (or ``FileNotFoundError``) is raised,
causing a non‑zero exit code.
"""

import json
import pathlib
import sys

import pandas as pd
import yaml
from jsonschema import Draft7Validator, ValidationError

from utils.logging import get_logger


SCHEMA_PATH = pathlib.Path("contracts/processed_data.schema.yaml")
DATA_PATH = pathlib.Path("data/processed/hea_descriptors.csv")


def load_schema(schema_path: pathlib.Path) -> dict:
    """Load a YAML JSON‑Schema file."""
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_dataframe(df: pd.DataFrame, schema: dict) -> None:
    """
    Validate each record of ``df`` against ``schema``.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to validate.
    schema : dict
        JSON‑Schema dictionary.

    Raises
    ------
    jsonschema.ValidationError
        If any row does not conform to the schema.
    """
    validator = Draft7Validator(schema)
    # Convert DataFrame rows to plain dicts – ``to_dict(orient="records")``
    # yields a list of row dictionaries.
    records = df.to_dict(orient="records")
    errors = sorted(validator.iter_errors(records), key=lambda e: e.path)
    if errors:
        # Report the first error for brevity; the caller can inspect the
        # full list if needed.
        raise errors[0]


def main() -> None:
    logger = get_logger(__name__)

    if not SCHEMA_PATH.is_file():
        logger.error("Schema file not found: %s", SCHEMA_PATH)
        raise FileNotFoundError(f"Schema file missing: {SCHEMA_PATH}")

    if not DATA_PATH.is_file():
        logger.error("Processed descriptor file not found: %s", DATA_PATH)
        raise FileNotFoundError(f"Processed data missing: {DATA_PATH}")

    logger.info("Loading schema from %s", SCHEMA_PATH)
    schema = load_schema(SCHEMA_PATH)

    logger.info("Reading processed data from %s", DATA_PATH)
    df = pd.read_csv(DATA_PATH)

    logger.info("Validating %d records against the schema", len(df))
    try:
        validate_dataframe(df, schema)
    except ValidationError as ve:
        logger.error("Schema validation failed: %s", ve.message)
        raise

    logger.info("Validation successful – all records conform to the schema.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # pragma: no cover – ensures non‑zero exit.
        sys.exit(1)