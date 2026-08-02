"""
Schema validation logic for enforcing contracts/*.yaml inputs.

This module provides utilities to validate data files against JSON Schema
definitions stored in the contracts directory. It integrates with the
existing error_contract module to ensure strict adherence to project
specifications.
"""
import os
import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

try:
    import jsonschema
    from jsonschema import validate, ValidationError, SchemaError
except ImportError:
    # Fallback for environments where jsonschema might not be installed yet,
    # though T002 should have added it to requirements.txt.
    raise ImportError(
        "The 'jsonschema' library is required for schema validation. "
        "Please ensure it is installed via 'pip install jsonschema'."
    )

from utils.error_contract import ContractViolationError, load_schema as error_contract_load_schema

# Default path to the contracts directory relative to project root
DEFAULT_CONTRACTS_DIR = "contracts"


def load_schema_from_file(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON or YAML schema from a file.

    Args:
        schema_path: Path to the schema file (.json or .yaml/.yml).

    Returns:
        Dictionary representing the loaded schema.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the file format is unsupported or invalid.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if path.suffix.lower() in ['.json']:
        return json.loads(content)
    elif path.suffix.lower() in ['.yaml', '.yml']:
        return yaml.safe_load(content)
    else:
        raise ValueError(f"Unsupported schema file format: {path.suffix}")


def validate_data_against_schema(
    data: Dict[str, Any],
    schema: Dict[str, Any],
    schema_name: Optional[str] = None
) -> bool:
    """
    Validate a data dictionary against a JSON Schema.

    Args:
        data: The data to validate.
        schema: The JSON Schema definition.
        schema_name: Optional name for error messages.

    Returns:
        True if validation passes.

    Raises:
        ContractViolationError: If the data does not match the schema.
        SchemaError: If the schema itself is invalid.
    """
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        error_msg = f"Schema validation failed"
        if schema_name:
            error_msg += f" for '{schema_name}'"
        error_msg += f": {e.message} (Instance path: {list(e.path)})"
        raise ContractViolationError(error_msg) from e


def validate_file_against_schema(
    data_path: Union[str, Path],
    schema_path: Union[str, Path],
    schema_name: Optional[str] = None
) -> bool:
    """
    Load a data file (JSON/CSV/YAML) and validate it against a schema.

    Note: For CSV files, simple loading is assumed. Complex CSV validation
    (e.g., column types) should be handled by specific loaders or pre-processing.
    This function primarily validates JSON/YAML structures.

    Args:
        data_path: Path to the data file.
        schema_path: Path to the schema file.
        schema_name: Optional name for error messages.

    Returns:
        True if validation passes.

    Raises:
        ContractViolationError: If validation fails.
    """
    data_path = Path(data_path)
    schema = load_schema_from_file(schema_path)

    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    # Determine data format
    suffix = data_path.suffix.lower()
    if suffix in ['.json']:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif suffix in ['.yaml', '.yml']:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    elif suffix == '.csv':
        # For CSV, we load into a dict of lists or list of dicts if jsonschema
        # expects a specific structure. However, jsonschema is primarily for JSON.
        # If the schema expects a specific JSON structure representing the CSV,
        # the user should convert first. Here we assume the schema expects
        # a representation of the CSV data (e.g. list of rows).
        import csv
        rows = []
        with open(data_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Ensure numeric strings are parsed if the schema expects numbers
                # This is a basic attempt; robust type coercion should be in the loader
                cleaned_row = {}
                for k, v in row.items():
                    if v.lower() == 'nan' or v == '':
                        cleaned_row[k] = None
                    else:
                        try:
                            if '.' in v:
                                cleaned_row[k] = float(v)
                            else:
                                cleaned_row[k] = int(v)
                        except ValueError:
                            cleaned_row[k] = v
                rows.append(cleaned_row)
        data = rows
    else:
        raise ValueError(f"Unsupported data file format for validation: {suffix}")

    return validate_data_against_schema(data, schema, schema_name)


def validate_contract_input(
    input_path: Union[str, Path],
    contract_name: str,
    contracts_dir: Optional[Union[str, Path]] = None
) -> bool:
    """
    Validate an input file against its corresponding contract schema.

    This is a convenience wrapper that locates the schema in the contracts
    directory based on the contract name and validates the input file.

    Args:
        input_path: Path to the input data file to validate.
        contract_name: Name of the contract (e.g., 'dataset', 'hrv_metrics').
                       Will look for contracts/{contract_name}.schema.yaml or .json.
        contracts_dir: Optional override for the contracts directory path.

    Returns:
        True if validation passes.

    Raises:
        ContractViolationError: If validation fails.
        FileNotFoundError: If the schema or input file is missing.
    """
    if contracts_dir is None:
        contracts_dir = DEFAULT_CONTRACTS_DIR
    else:
        contracts_dir = Path(contracts_dir)

    schema_path = None
    for ext in ['.yaml', '.yml', '.json']:
        candidate = Path(contracts_dir) / f"{contract_name}.schema{ext}"
        if candidate.exists():
            schema_path = candidate
            break

    if not schema_path:
        raise FileNotFoundError(
            f"Schema not found for contract '{contract_name}'. "
            f"Expected to find it in {contracts_dir} as "
            f"'{contract_name}.schema.yaml' or '.json'."
        )

    return validate_file_against_schema(input_path, schema_path, contract_name)
