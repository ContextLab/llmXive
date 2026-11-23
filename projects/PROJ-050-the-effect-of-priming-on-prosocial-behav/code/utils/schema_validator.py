"""
Schema validation utilities for the prosocial behavior research pipeline.

Validates datasets against defined YAML schemas:
- dataset.schema.yaml (raw/processed data structure)
- scored.schema.yaml (scoring results structure)
- model_results.schema.yaml (analysis results structure)
- output.schema.yaml (generic output structure, retained for backward compatibility)
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml
import pandas as pd

from code.config import PROJECT_ROOT

# Configure logger
logger = logging.getLogger(__name__)

# Directory where the YAML schema files live
SCHEMA_DIR = PROJECT_ROOT / "specs" / "001-the-effect-of-priming-on-prosocial-behav"

# Mapping from logical schema name to the actual YAML file name
SCHEMAS = {
    "dataset": "dataset.schema.yaml",
    "scored": "scored.schema.yaml",
    "model_results": "model_results.schema.yaml",
    # ``output`` is kept for legacy callers; it points to the same file as model_results
    "output": "model_results.schema.yaml",
}

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a schema definition from the specs directory.

    Args:
        schema_name: One of 'dataset', 'scored', 'model_results', or 'output'.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file doesn't exist.
        ValueError: If ``schema_name`` is invalid.
    """
    if schema_name not in SCHEMAS:
        raise ValueError(
            f"Unknown schema: {schema_name}. Must be one of {list(SCHEMAS.keys())}"
        )

    schema_path = SCHEMA_DIR / SCHEMAS[schema_name]

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_column_types(
    df: pd.DataFrame, expected_columns: Dict[str, str]
) -> Tuple[bool, List[str]]:
    """
    Validate that DataFrame columns exist and have expected dtypes.

    Args:
        df: DataFrame to validate.
        expected_columns: Mapping column name → expected dtype string.

    Returns:
        Tuple ``(is_valid, errors)`` where ``is_valid`` is ``True`` iff
        all required columns are present and have the correct type.
    """
    errors: List[str] = []

    for col, expected_dtype in expected_columns.items():
        if col not in df.columns:
            errors.append(f"Missing required column: '{col}'")
            continue

        # Use pandas type‑checking utilities for robust detection
        if expected_dtype == "string" and not pd.api.types.is_string_dtype(df[col]):
            errors.append(
                f"Column '{col}' expected string type, got {df[col].dtype}"
            )
        elif expected_dtype == "integer" and not pd.api.types.is_integer_dtype(df[col]):
            errors.append(
                f"Column '{col}' expected integer type, got {df[col].dtype}"
            )
        elif expected_dtype == "float" and not pd.api.types.is_float_dtype(df[col]):
            errors.append(
                f"Column '{col}' expected float type, got {df[col].dtype}"
            )
        elif expected_dtype == "boolean" and not pd.api.types.is_bool_dtype(df[col]):
            errors.append(
                f"Column '{col}' expected boolean type, got {df[col].dtype}"
            )
        elif expected_dtype == "datetime" and not pd.api.types.is_datetime64_any_dtype(
            df[col]
        ):
            errors.append(
                f"Column '{col}' expected datetime type, got {df[col].dtype}"
            )

    return len(errors) == 0, errors

def _apply_constraints(df: pd.DataFrame, constraints: Dict[str, Any]) -> List[str]:
    """
    Internal helper to evaluate ``constraints`` sections of a schema.

    Supported constraint keys:
        - min_value
        - max_value
        - allowed_values

    Returns a list of error messages (empty if no violations).
    """
    errors: List[str] = []

    for col, constraint in constraints.items():
        if col not in df.columns:
            # If the column is missing we let the required‑column check handle it
            continue

        series = df[col]

        if "min_value" in constraint:
            if series.min() < constraint["min_value"]:
                errors.append(
                    f"Column '{col}' has values below minimum {constraint['min_value']}"
                )

        if "max_value" in constraint:
            if series.max() > constraint["max_value"]:
                errors.append(
                    f"Column '{col}' has values above maximum {constraint['max_value']}"
                )

        if "allowed_values" in constraint:
            invalid = set(series.unique()) - set(constraint["allowed_values"])
            if invalid:
                errors.append(
                    f"Column '{col}' contains invalid values: {invalid}"
                )

    return errors

def validate_schema(df: pd.DataFrame, schema_name: str) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against a named schema.

    Args:
        df: DataFrame to validate.
        schema_name: One of 'dataset', 'scored', 'model_results', or 'output'.

    Returns:
        Tuple ``(is_valid, errors)``.
    """
    try:
        schema = load_schema(schema_name)
    except (FileNotFoundError, ValueError) as e:
        return False, [str(e)]

    errors: List[str] = []

    # ----- Required columns -----
    required_columns = schema.get("required_columns", {})
    is_valid, col_errors = validate_column_types(df, required_columns)
    errors.extend(col_errors)

    # ----- Optional columns (type checking only if present) -----
    optional_columns = schema.get("optional_columns", {})
    for col, expected_dtype in optional_columns.items():
        if col in df.columns:
            # Re‑use the same type‑checking logic
            dummy_df = pd.DataFrame({col: df[col]})
            _, opt_errors = validate_column_types(dummy_df, {col: expected_dtype})
            errors.extend(opt_errors)

    # ----- Value constraints (min/max/allowed) -----
    constraints = schema.get("constraints", {})
    errors.extend(_apply_constraints(df, constraints))

    return len(errors) == 0, errors

# ----------------------------------------------------------------------
# Convenience wrappers for the three primary schemas used throughout the
# pipeline.  They keep the public API stable for callers that only need a
# single‑schema check.
# ----------------------------------------------------------------------
def validate_dataset_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate ``df`` against ``dataset.schema.yaml``."""
    return validate_schema(df, "dataset")

def validate_scored_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate ``df`` against ``scored.schema.yaml``."""
    return validate_schema(df, "scored")

def validate_model_results_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate ``df`` against ``model_results.schema.yaml``."""
    return validate_schema(df, "model_results")

# Backward‑compatibility alias (some legacy code still asks for "output")
def validate_output_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate ``df`` against ``output.schema.yaml`` (alias for model_results)."""
    return validate_schema(df, "output")

def main() -> int:
    """
    Command‑line entry point for schema validation.

    Usage:
        python -m code.utils.schema_validator --schema <name> --file <path>
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate data against schema definitions"
    )
    parser.add_argument(
        "--schema",
        required=True,
        choices=list(SCHEMAS.keys()),
        help="Schema to validate against (dataset, scored, model_results, output)",
    )
    parser.add_argument(
        "--file", required=True, help="Path to CSV file to validate"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed output"
    )

    args = parser.parse_args()

    try:
        df = pd.read_csv(args.file)
        logger.info(f"Loaded {len(df)} rows from {args.file}")

        is_valid, errors = validate_schema(df, args.schema)

        if is_valid:
            logger.info(f"✓ Validation PASSED for schema '{args.schema}'")
            return 0
        else:
            logger.error(f"✗ Validation FAILED for schema '{args.schema}'")
            for error in errors:
                logger.error(f"  - {error}")
            return 1

    except Exception as e:
        logger.error(f"Error during validation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())