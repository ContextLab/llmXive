import os
import sys
from pathlib import Path
from typing import List, Set, Dict, Any
import yaml
import pandas as pd

# Custom error code constant for schema validation failures
E_SCHEMA_MISSING = "E_SCHEMA_MISSING"

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load and parse a YAML schema file.

    Args:
        schema_path: Path to the YAML schema file.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the schema is invalid or missing required keys.
        yaml.YAMLError: If the YAML content is malformed.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r') as f:
        try:
            schema = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in schema file: {e}")

    if not isinstance(schema, dict):
        raise ValueError("Schema must be a YAML dictionary")

    if "required_columns" not in schema:
        raise ValueError("Schema must contain 'required_columns' key")

    return schema

def validate_columns(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Check if a DataFrame contains all required columns defined in the schema.

    Args:
        df: Pandas DataFrame to validate.
        schema: Schema dictionary containing 'required_columns'.

    Returns:
        List of missing column names. Empty list if all columns are present.
    """
    required = set(schema["required_columns"])
    present = set(df.columns)
    missing = required - present
    return list(missing)

def validate_data(data_path: str, schema_path: str) -> Dict[str, Any]:
    """
    Validate a CSV data file against a YAML schema.

    This function loads the data and schema, checks for required columns,
    and returns a validation result. If columns are missing, it exits
    with code E_SCHEMA_MISSING.

    Args:
        data_path: Path to the CSV data file.
        schema_path: Path to the YAML schema file.

    Returns:
        Dictionary with 'valid' (bool) and 'missing_columns' (list).

    Raises:
        SystemExit: If required columns are missing (code E_SCHEMA_MISSING).
        FileNotFoundError: If data or schema file is not found.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")

    schema = load_schema(schema_path)
    df = pd.read_csv(data_path)

    missing = validate_columns(df, schema)

    if missing:
        print(f"Validation Failed: Missing required columns: {missing}", file=sys.stderr)
        # Exit with the specific error code string converted to int if needed,
        # or simply a non-zero integer. The spec asks for E_SCHEMA_MISSING.
        # Python sys.exit accepts strings, but standard practice is integer codes.
        # We will exit with a specific integer code and print the error code.
        print(f"Error Code: {E_SCHEMA_MISSING}", file=sys.stderr)
        sys.exit(1)

    return {"valid": True, "missing_columns": []}

def main():
    """
    Command-line entry point for data validation.
    Expects two arguments: <data_file> <schema_file>
    """
    if len(sys.argv) != 3:
        print("Usage: python -m src.data.validate <data_file> <schema_file>", file=sys.stderr)
        sys.exit(2)

    data_path = sys.argv[1]
    schema_path = sys.argv[2]

    try:
        result = validate_data(data_path, schema_path)
        if result["valid"]:
            print("Validation Successful: All required columns present.")
            sys.exit(0)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)
    except ValueError as e:
        print(f"Schema Error: {e}", file=sys.stderr)
        sys.exit(4)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(5)

if __name__ == "__main__":
    main()
