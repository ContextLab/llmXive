"""
Feature matrix validation script.

This module provides a function to validate the generated
``data/processed/feature_matrix.csv`` file against the JSON‑Schema
located at ``contracts/dataset.schema.yaml`` using the ``jsonschema``
library.

The validation is performed row‑wise: each CSV row is converted to a
``dict`` (column name → value) and validated against the schema.
If any row does not conform, a ``jsonschema.exceptions.ValidationError``
is raised, causing the CI test to fail.

The module can also be executed as a small CLI utility:
    python -m code.validate_feature_matrix
which will run the validation and exit with status 0 on success or
non‑zero on failure.
"""

import sys
from pathlib import Path
import yaml
import pandas as pd
from jsonschema import validate, ValidationError

# llmxive_toolkit provides convenient path helpers that create the
# required directories when the path is accessed.
from llmxive_toolkit import paths

__all__ = ["validate_feature_matrix"]

def _load_schema(schema_path: Path) -> dict:
    """
    Load a JSON‑Schema from a YAML file.

    Parameters
    ----------
    schema_path : Path
        Path to the ``.yaml`` schema file.

    Returns
    -------
    dict
        The parsed schema dictionary.
    """
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_feature_matrix(
    csv_path: Path = None,
    schema_path: Path = None,
) -> None:
    """
    Validate the feature matrix CSV against the provided JSON‑Schema.

    The function reads the CSV into a ``pandas.DataFrame`` and validates
    each row (converted to a ``dict``) against the schema.  If any row
    fails validation a ``jsonschema.exceptions.ValidationError`` is
    raised.

    Parameters
    ----------
    csv_path : Path, optional
        Path to ``feature_matrix.csv``.  If omitted the default location
        ``data/processed/feature_matrix.csv`` is used.
    schema_path : Path, optional
        Path to the JSON‑Schema file.  If omitted the default location
        ``contracts/dataset.schema.yaml`` is used.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.
    ValidationError
        If any row does not conform to the schema.
    """
    # Resolve default locations
    if csv_path is None:
        csv_path = paths.data("processed", "feature_matrix.csv")
    if schema_path is None:
        schema_path = Path("contracts") / "dataset.schema.yaml"

    # Ensure the feature matrix exists
    if not csv_path.is_file():
        raise FileNotFoundError(f"Feature matrix not found: {csv_path}")

    # Load data
    df = pd.read_csv(csv_path)

    # Load schema
    schema = _load_schema(schema_path)

    # Validate each row
    for idx, row in df.iterrows():
        instance = row.to_dict()
        try:
            validate(instance=instance, schema=schema)
        except ValidationError as exc:
            # Augment the error with row information for easier debugging
            raise ValidationError(
                f"Row {idx} failed validation: {exc.message}"
            ) from exc

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _cli() -> None:
    """
    Minimal command‑line interface.

    Executes ``validate_feature_matrix`` with the default paths and
    prints a concise message.  The process exits with status 0 on
    success or 1 on any validation error.
    """
    try:
        validate_feature_matrix()
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValidationError as e:
        print(f"VALIDATION ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    else:
        print("Feature matrix validation passed.")
        sys.exit(0)

if __name__ == "__main__":
    _cli()