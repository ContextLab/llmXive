"""
Schema validation utilities for dataset and injection configurations.
Uses jsonschema for validation against YAML-defined schemas.
"""
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Tuple, Union

try:
    import jsonschema
    from jsonschema import validate, ValidationError, SchemaError
except ImportError:
    raise ImportError(
        "jsonschema is required. Install it via: pip install jsonschema"
    )

SCHEMAS_DIR = Path(__file__).parent
DATASET_SCHEMA_PATH = SCHEMAS_DIR / "dataset.schema.yaml"
INJECTION_SCHEMA_PATH = SCHEMAS_DIR / "injection.schema.yaml"

_dataset_schema = None
_injection_schema = None


def _load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file into a Python dictionary."""
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_dataset_schema() -> Dict[str, Any]:
    """Lazy-load and cache the dataset schema."""
    global _dataset_schema
    if _dataset_schema is None:
        if not DATASET_SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Dataset schema not found: {DATASET_SCHEMA_PATH}")
        _dataset_schema = _load_schema(DATASET_SCHEMA_PATH)
    return _dataset_schema


def get_injection_schema() -> Dict[str, Any]:
    """Lazy-load and cache the injection schema."""
    global _injection_schema
    if _injection_schema is None:
        if not INJECTION_SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Injection schema not found: {INJECTION_SCHEMA_PATH}")
        _injection_schema = _load_schema(INJECTION_SCHEMA_PATH)
    return _injection_schema


def validate_dataset(data: Union[Dict[str, Any], str, Path]) -> Tuple[bool, str]:
    """
    Validate dataset metadata against the dataset schema.

    Args:
        data: Can be a dict, a path to a JSON file, or a path to a YAML file.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    schema = get_dataset_schema()

    if isinstance(data, (str, Path)):
        path = Path(data)
        if not path.exists():
            return False, f"Data file not found: {path}"
        if path.suffix in [".yaml", ".yml"]:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        elif path.suffix == ".json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            return False, f"Unsupported file format: {path.suffix}"

    try:
        validate(instance=data, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, f"Validation Error: {e.message} at path: {'/'.join(map(str, e.path))}"
    except SchemaError as e:
        return False, f"Schema Error: {e.message}"


def validate_injection_config(data: Union[Dict[str, Any], str, Path]) -> Tuple[bool, str]:
    """
    Validate injection configuration against the injection schema.

    Args:
        data: Can be a dict, a path to a JSON file, or a path to a YAML file.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    schema = get_injection_schema()

    if isinstance(data, (str, Path)):
        path = Path(data)
        if not path.exists():
            return False, f"Data file not found: {path}"
        if path.suffix in [".yaml", ".yml"]:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        elif path.suffix == ".json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            return False, f"Unsupported file format: {path.suffix}"

    try:
        validate(instance=data, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, f"Validation Error: {e.message} at path: {'/'.join(map(str, e.path))}"
    except SchemaError as e:
        return False, f"Schema Error: {e.message}"


def main():
    """CLI entry point for schema validation testing."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python schema_validator.py <dataset|injection> <path_to_file>")
        sys.exit(1)

    mode = sys.argv[1]
    path = sys.argv[2]

    if mode == "dataset":
        is_valid, msg = validate_dataset(path)
    elif mode == "injection":
        is_valid, msg = validate_injection_config(path)
    else:
        print(f"Unknown mode: {mode}. Use 'dataset' or 'injection'.")
        sys.exit(1)

    if is_valid:
        print(f"✓ Validation successful for {path}")
        sys.exit(0)
    else:
        print(f"✗ Validation failed for {path}: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
