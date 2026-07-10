"""
Contract validation module for enforcing schema contracts.

This module implements Constitution Principle V by validating data artifacts
against schema contracts defined in the contracts/ directory.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml


class ContractValidationError(Exception):
    """Exception raised when contract validation fails."""

    def __init__(self, message: str, details: Optional[List[str]] = None):
        super().__init__(message)
        self.details = details or []


def load_contract(contract_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a contract schema from a JSON or YAML file.

    Args:
        contract_path: Path to the contract file (JSON or YAML)

    Returns:
        Dictionary containing the contract schema

    Raises:
        FileNotFoundError: If the contract file does not exist
        ValueError: If the file format is unsupported or parsing fails
    """
    path = Path(contract_path)
    if not path.exists():
        raise FileNotFoundError(f"Contract file not found: {path}")

    content = path.read_text(encoding="utf-8")

    if path.suffix.lower() in [".json", ".yaml", ".yml"]:
        if path.suffix.lower() == ".json":
            return json.loads(content)
        else:
            return yaml.safe_load(content)
    else:
        raise ValueError(f"Unsupported contract file format: {path.suffix}")


def validate_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected type.

    Supported types: string, number, integer, boolean, array, object, null

    Args:
        value: The value to validate
        expected_type: The expected type as a string

    Returns:
        True if the type matches, False otherwise
    """
    type_mapping = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None),
    }

    if expected_type not in type_mapping:
        return False

    expected = type_mapping[expected_type]
    return isinstance(value, expected)


def validate_schema(
    data: Dict[str, Any], schema: Dict[str, Any], path: str = ""
) -> Tuple[bool, List[str]]:
    """
    Validate data against a JSON Schema-like contract.

    Args:
        data: The data to validate
        schema: The schema definition
        path: Current path in the data structure (for error reporting)

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []

    # Check required fields
    if "required" in schema:
        for field in schema["required"]:
            if field not in data:
                errors.append(f"Missing required field: {path}.{field}" if path else f"Missing required field: {field}")

    # Validate properties
    if "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            if prop_name in data:
                current_path = f"{path}.{prop_name}" if path else prop_name
                value = data[prop_name]

                # Type validation
                if "type" in prop_schema:
                    if not validate_type(value, prop_schema["type"]):
                        errors.append(
                            f"Type mismatch at {current_path}: expected {prop_schema['type']}, got {type(value).__name__}"
                        )

                # Array items validation
                if prop_schema.get("type") == "array" and "items" in prop_schema:
                    if isinstance(value, list):
                        for idx, item in enumerate(value):
                            item_path = f"{current_path}[{idx}]"
                            item_valid, item_errors = validate_schema(
                                item, prop_schema["items"], item_path
                            )
                            if not item_valid:
                                errors.extend(item_errors)

                # Object nested validation
                if prop_schema.get("type") == "object" and "properties" in prop_schema:
                    if isinstance(value, dict):
                        nested_valid, nested_errors = validate_schema(
                            value, prop_schema, current_path
                        )
                        if not nested_valid:
                            errors.extend(nested_errors)

                # String constraints
                if prop_schema.get("type") == "string":
                    if isinstance(value, str):
                        if "minLength" in prop_schema and len(value) < prop_schema["minLength"]:
                            errors.append(
                                f"String too short at {current_path}: minimum length {prop_schema['minLength']}"
                            )
                        if "maxLength" in prop_schema and len(value) > prop_schema["maxLength"]:
                            errors.append(
                                f"String too long at {current_path}: maximum length {prop_schema['maxLength']}"
                            )
                        if "pattern" in prop_schema:
                            import re
                            if not re.match(prop_schema["pattern"], value):
                                errors.append(
                                    f"Pattern mismatch at {current_path}: expected pattern {prop_schema['pattern']}"
                                )

                # Number constraints
                if prop_schema.get("type") in ["number", "integer"]:
                    if isinstance(value, (int, float)):
                        if "minimum" in prop_schema and value < prop_schema["minimum"]:
                            errors.append(
                                f"Value too low at {current_path}: minimum {prop_schema['minimum']}"
                            )
                        if "maximum" in prop_schema and value > prop_schema["maximum"]:
                            errors.append(
                                f"Value too high at {current_path}: maximum {prop_schema['maximum']}"
                            )

    return len(errors) == 0, errors


def validate_artifact(
    artifact_path: Union[str, Path],
    contract_path: Optional[Union[str, Path]] = None,
    contract_name: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate an artifact against its corresponding contract.

    Args:
        artifact_path: Path to the artifact file (JSON)
        contract_path: Optional explicit path to contract file
        contract_name: Optional contract name (used to find contract in contracts/)

    Returns:
        Tuple of (is_valid, list_of_error_messages)

    Raises:
        ContractValidationError: If validation fails
    """
    artifact_path = Path(artifact_path)

    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact file not found: {artifact_path}")

    # Load artifact data
    artifact_content = artifact_path.read_text(encoding="utf-8")
    try:
        data = json.loads(artifact_content)
    except json.JSONDecodeError as e:
        raise ContractValidationError(
            f"Failed to parse artifact as JSON: {e}"
        )

    # Determine contract path
    if contract_path:
        contract_file = Path(contract_path)
    elif contract_name:
        contract_file = Path("contracts") / f"{contract_name}.json"
    else:
        # Infer contract name from artifact name
        contract_file = Path("contracts") / f"{artifact_path.stem}.json"

    if not contract_file.exists():
        raise FileNotFoundError(f"Contract file not found: {contract_file}")

    # Load and validate against contract
    schema = load_contract(contract_file)
    is_valid, errors = validate_schema(data, schema)

    if not is_valid:
        raise ContractValidationError(
            f"Validation failed for {artifact_path.name}",
            details=errors,
        )

    return True, []


def validate_all_artifacts(
    artifacts_dir: Union[str, Path],
    contracts_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Tuple[bool, List[str]]]:
    """
    Validate all JSON artifacts in a directory against their contracts.

    Args:
        artifacts_dir: Directory containing artifact files
        contracts_dir: Optional directory containing contract files

    Returns:
        Dictionary mapping artifact names to (is_valid, errors) tuples
    """
    artifacts_dir = Path(artifacts_dir)
    contracts_dir = Path(contracts_dir) if contracts_dir else Path("contracts")

    results = {}

    for artifact_file in artifacts_dir.glob("*.json"):
        try:
            is_valid, errors = validate_artifact(
                artifact_file, contract_path=None, contract_name=None
            )
            results[artifact_file.name] = (is_valid, errors)
        except FileNotFoundError as e:
            results[artifact_file.name] = (False, [str(e)])
        except ContractValidationError as e:
            results[artifact_file.name] = (False, e.details)
        except Exception as e:
            results[artifact_file.name] = (False, [f"Unexpected error: {str(e)}"])

    return results


def get_contract_for_artifact(
    artifact_path: Union[str, Path], contracts_dir: Optional[Union[str, Path]] = None
) -> Optional[Path]:
    """
    Find the contract file for a given artifact.

    Args:
        artifact_path: Path to the artifact file
        contracts_dir: Directory containing contract files

    Returns:
        Path to the contract file if found, None otherwise
    """
    artifact_path = Path(artifact_path)
    contracts_dir = Path(contracts_dir) if contracts_dir else Path("contracts")

    contract_name = f"{artifact_path.stem}.json"
    contract_path = contracts_dir / contract_name

    return contract_path if contract_path.exists() else None


# Convenience function for use in other modules
def enforce_contract(
    artifact_path: Union[str, Path],
    contract_path: Optional[Union[str, Path]] = None,
) -> bool:
    """
    Enforce a contract on an artifact, raising an exception if validation fails.

    Args:
        artifact_path: Path to the artifact file
        contract_path: Optional path to the contract file

    Returns:
        True if validation passes (raises exception otherwise)
    """
    is_valid, errors = validate_artifact(
        artifact_path, contract_path=contract_path
    )
    if not is_valid:
        raise ContractValidationError(
            f"Contract validation failed for {artifact_path}",
            details=errors,
        )
    return True