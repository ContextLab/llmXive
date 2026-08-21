"""
Schema validation utilities for contracts.

Provides functions to load JSON/YAML schemas and validate data instances
against them using the jsonschema library.
"""
import json
import logging
from pathlib import Path
from typing import Union

import yaml
from jsonschema import Draft7Validator, ValidationError

logger = logging.getLogger(__name__)

def load_schema(path: Union[str, Path]) -> Draft7Validator:
    """
    Load a JSON or YAML schema from a file path and return a Draft7Validator instance.

    Args:
        path: Path to the schema file (.json or .yaml/.yml).

    Returns:
        A Draft7Validator instance.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the file format is unsupported or parsing fails.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    logger.info(f"Loading schema from {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in [".json"]:
                schema = json.load(f)
            elif path.suffix in [".yaml", ".yml"]:
                schema = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported schema file format: {path.suffix}")

        validator = Draft7Validator(schema)
        logger.info(f"Schema loaded and validated successfully: {path}")
        return validator
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise ValueError(f"Failed to parse schema file {path}: {e}")

def validate_instance(validator: Draft7Validator, instance: dict) -> list:
    """
    Validate an instance against a schema validator.

    Args:
        validator: The Draft7Validator instance.
        instance: The data dictionary to validate.

    Returns:
        A list of error messages if validation fails, empty list if valid.
    """
    errors = list(validator.iter_errors(instance))
    if errors:
        error_messages = [f"Error at {e.path}: {e.message}" for e in errors]
        logger.error(f"Validation failed with {len(errors)} errors: {error_messages}")
        return error_messages
    
    logger.debug("Validation successful.")
    return []

def load_and_validate(schema_path: Union[str, Path], data_path: Union[str, Path]) -> tuple[bool, list]:
    """
    Load a schema and a data file, then validate the data against the schema.

    Args:
        schema_path: Path to the schema file.
        data_path: Path to the data file (.json).

    Returns:
        A tuple (is_valid, error_messages).
    """
    try:
        validator = load_schema(schema_path)
        
        data_path = Path(data_path)
        if not data_path.exists():
            return False, [f"Data file not found: {data_path}"]

        with open(data_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                return False, [f"Failed to parse data file {data_path}: {e}"]

        errors = validate_instance(validator, data)
        return len(errors) == 0, errors

    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        return False, [str(e)]

# Convenience wrappers for specific schemas
def get_dataset_validator() -> Draft7Validator:
    """Load the dataset schema validator."""
    return load_schema(Path("contracts/dataset.schema.yaml"))

def get_model_output_validator() -> Draft7Validator:
    """Load the model output schema validator."""
    return load_schema(Path("contracts/model_output.schema.yaml"))

def get_output_validator() -> Draft7Validator:
    """Load the generic output schema validator."""
    return load_schema(Path("contracts/output.schema.yaml"))