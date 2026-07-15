"""Contract validation logic for llmXive pipeline artifacts."""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    raise ImportError(
        "jsonschema is required for contract validation. "
        "Install it via: pip install jsonschema"
    )

# Cache for loaded schemas to avoid re-parsing YAML on every call
_SCHEMA_CACHE: Dict[str, Dict[str, Any]] = {}
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON schema from the contracts directory.
    
    Args:
        schema_name: Name of the YAML schema file (e.g., 'trace.schema.yaml').
        
    Returns:
        The loaded schema as a dictionary.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is invalid YAML.
    """
    if schema_name in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[schema_name]
    
    schema_path = CONTRACTS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    _SCHEMA_CACHE[schema_name] = schema
    return schema

def validate_artifact(
    artifact_data: Dict[str, Any], 
    schema_name: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate an artifact dictionary against a named schema.
    
    Args:
        artifact_data: The data to validate.
        schema_name: The name of the schema file in contracts/.
        
    Returns:
        A tuple (is_valid, error_message). 
        If valid, error_message is None.
        If invalid, is_valid is False and error_message describes the issue.
    """
    try:
        schema = load_schema(schema_name)
        validate(instance=artifact_data, schema=schema)
        return True, None
    except ValidationError as e:
        # Provide a more detailed error path if available
        path_str = ".".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
        return False, f"Schema validation error in {schema_name} at '{path_str}': {e.message}"
    except Exception as e:
        return False, f"Unexpected error validating {schema_name}: {str(e)}"

def validate_json_file(
    file_path: Path, 
    schema_name: str
) -> Tuple[bool, Optional[str]]:
    """
    Load a JSON file and validate it against a named schema.
    
    Args:
        file_path: Path to the JSON file.
        schema_name: The name of the schema file in contracts/.
        
    Returns:
        A tuple (is_valid, error_message).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return validate_artifact(data, schema_name)
    except json.JSONDecodeError as e:
        return False, f"JSON parsing error in {file_path}: {e.msg}"
    except FileNotFoundError:
        return False, f"File not found: {file_path}"
    except Exception as e:
        return False, f"Error processing {file_path}: {str(e)}"

def get_all_schema_names() -> List[str]:
    """Return a list of all available schema file names in the contracts directory."""
    if not CONTRACTS_DIR.exists():
        return []
    return [f.name for f in CONTRACTS_DIR.iterdir() if f.suffix == '.yaml']

def validate_trace_artifact(artifact_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Convenience wrapper to validate a trace artifact specifically.
    
    This function loads the 'trace.schema.yaml' and validates the provided
    artifact data against it. It is a specialized entry point for the
    trace generation pipeline (US1).
    
    Args:
        artifact_data: The trace data to validate (should contain tool sequences, etc.).
        
    Returns:
        A tuple (is_valid, error_message).
    """
    return validate_artifact(artifact_data, "trace.schema.yaml")

def validate_metrics_artifact(artifact_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Convenience wrapper to validate a metrics artifact specifically.
    
    Args:
        artifact_data: The metrics data to validate.
        
    Returns:
        A tuple (is_valid, error_message).
    """
    return validate_artifact(artifact_data, "metrics.schema.yaml")

def validate_benchmark_artifact(artifact_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Convenience wrapper to validate a benchmark results artifact specifically.
    
    Args:
        artifact_data: The benchmark results data to validate.
        
    Returns:
        A tuple (is_valid, error_message).
    """
    return validate_artifact(artifact_data, "benchmark_results.schema.yaml")

def validate_compressibility_artifact(artifact_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Convenience wrapper to validate a compressibility analysis artifact specifically.
    
    Args:
        artifact_data: The compressibility analysis data to validate.
        
    Returns:
        A tuple (is_valid, error_message).
    """
    return validate_artifact(artifact_data, "compressibility_analysis.schema.yaml")

# Re-export types for convenience
__all__ = [
    'load_schema',
    'validate_artifact',
    'validate_json_file',
    'get_all_schema_names',
    'validate_trace_artifact',
    'validate_metrics_artifact',
    'validate_benchmark_artifact',
    'validate_compressibility_artifact',
    'ValidationError'
]
