"""
validate_user_composition.py

Task T003 – Validate a user‑provided composition CSV.

The script reads a CSV file (default location ``data/input/compositions.csv``),
validates each record against the JSON‑schema contract
``contracts/hea_composition.schema.yaml`` and aborts with a clear
``ValueError`` if any required field is missing or the record does not
conform to the schema.

The CSV is expected to contain a column named ``composition`` whose
values are JSON objects (or JSON strings) mapping element symbols to
atomic fractions, e.g.:

.. code-block:: csv

    composition
    {"Fe":0.5,"Ni":0.5}
    {"Co":0.2,"Cr":0.2,"Fe":0.2,"Mn":0.2,"Ni":0.2}

The script can be used as a library (``validate_user_composition``) or
from the command line (``python -m code.data.validate_user_composition
--csv path/to/file.csv``).
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import yaml
from jsonschema import Draft7Validator, ValidationError

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_schema() -> Dict[str, Any]:
    """
    Load the ``hea_composition`` JSON‑schema from the project ``contracts``
    directory.

    Returns
    -------
    dict
        The parsed JSON‑schema.
    """
    # The project root is two levels up from this file:
    #   code/data/validate_user_composition.py
    #   ^^^^ ^^^  ^^^^^^^^^^^^^^^^^^^^
    project_root = Path(__file__).parents[2]
    schema_path = project_root / "contracts" / "hea_composition.schema.yaml"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_composition_field(value: Any) -> Dict[str, float]:
    """
    Convert the raw ``composition`` field from the CSV into a Python
    ``dict`` mapping element symbols to fractional amounts.

    The CSV may store the composition either as a JSON string or as a
    Python literal (e.g. ``{'Fe': 0.5, 'Ni': 0.5}``).  Both are accepted.

    Parameters
    ----------
    value : Any
        The raw cell value from the CSV.

    Returns
    -------
    dict
        Mapping of element symbols to fractions.

    Raises
    ------
    ValueError
        If the value cannot be parsed into a ``dict``.
    """
    if pd.isna(value):
        raise ValueError("Composition field is empty or NaN.")
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            # Try JSON first (most common)
            return json.loads(value)
        except json.JSONDecodeError:
            # Fallback to Python literal evaluation (e.g. "{'Fe':0.5}")
            try:
                return eval(value, {"__builtins__": {}})
            except Exception as exc:
                raise ValueError(f"Unable to parse composition string: {value}") from exc
    raise ValueError(f"Unsupported composition field type: {type(value)}")


def _validate_record(record: Dict[str, Any], validator: Draft7Validator, row_idx: int) -> None:
    """
    Validate a single CSV record against the schema.

    Parameters
    ----------
    record : dict
        Mapping of column names to values for the current row.
    validator : Draft7Validator
        Pre‑compiled JSON‑schema validator.
    row_idx : int
        Zero‑based row index (used for error messages).

    Raises
    ------
    ValueError
        If the record is missing required fields or fails schema validation.
    """
    if "composition" not in record:
        raise ValueError(f"Row {row_idx + 1}: missing required field 'composition'.")

    # Parse the composition column into a dict before validation.
    try:
        composition_dict = _parse_composition_field(record["composition"])
    except ValueError as exc:
        raise ValueError(f"Row {row_idx + 1}: composition parsing error – {exc}") from exc

    # Build a temporary JSON object that matches the schema shape.
    candidate = {"composition": composition_dict}

    errors: List[ValidationError] = list(validator.iter_errors(candidate))
    if errors:
        # Use the first error for a concise message.
        err = errors[0]
        raise ValueError(
            f"Row {row_idx + 1}: composition validation error – {err.message}"
        )


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def validate_user_composition(csv_path: str = "data/input/compositions.csv") -> pd.DataFrame:
    """
    Validate ``data/input/compositions.csv`` against the
    ``hea_composition`` schema.

    Parameters
    ----------
    csv_path : str, optional
        Path to the CSV file to validate.  Defaults to the canonical
        location ``data/input/compositions.csv``.

    Returns
    -------
    pandas.DataFrame
        The loaded DataFrame (unchanged) if validation succeeds.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.
    ValueError
        If any row fails validation.  The exception message includes the
        row number and a human‑readable description of the problem.
    """
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"Composition CSV not found: {csv_path}")

    df = pd.read_csv(path)

    # Load and compile the JSON‑schema once.
    schema = _load_schema()
    validator = Draft7Validator(schema)

    # Validate each row.
    for idx, row in df.iterrows():
        _validate_record(row.to_dict(), validator, idx)

    # All rows passed validation.
    return df


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a user‑provided HEA composition CSV against the "
            "``hea_composition`` JSON‑schema contract."
        )
    )
    parser.add_argument(
        "--csv",
        default="data/input/compositions.csv",
        help="Path to the composition CSV file (default: data/input/compositions.csv)",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    """
    Command‑line entry point.

    Returns
    -------
    int
        Exit code (0 on success, 1 on validation failure).
    """
    args = _parse_args(argv)
    try:
        validate_user_composition(args.csv)
        print(f"Validation succeeded for '{args.csv}'.")
        return 0
    except Exception as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
