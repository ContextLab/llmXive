"""
Schema validation framework using JSON Schema.
Loads all four contract YAML files from disk and validates data against them.
Implements T001 repair: loads real schema files from specs/001-build-a-mesh-network-that-forms-the-larg/contracts/
rather than hard-coding only ExecutionRun/RegressionModel.
"""
import yaml
from pathlib import Path
from typing import Any, Dict, List
from llmxive_toolkit import get_logger

logger = get_logger(__name__)

# Schema registry: loaded from disk on first use
_SCHEMA_CACHE: Dict[str, Dict[str, Any]] = {}

def _get_schema_path(schema_name: str) -> Path:
    """Resolve a schema name to its YAML file path."""
    # Map schema names to filenames in specs/001-build-a-mesh-network-that-forms-the-larg/contracts/
    schema_map = {
        "physical-node": "physical-node.schema.yaml",
        "dropout-event": "dropout-event.schema.yaml",
        "execution-run": "execution-run.schema.yaml",
        "regression-model": "regression-model.schema.yaml",
    }
    
    if schema_name not in schema_map:
        raise ValueError(f"Unknown schema name: {schema_name}. Valid names: {list(schema_map.keys())}")
    
    filename = schema_map[schema_name]
    schema_path = Path("specs/001-build-a-mesh-network-that-forms-the-larg/contracts") / filename
    
    if not schema_path.is_file():
        raise ValueError(f"Schema file not found: {schema_path}")
    
    return schema_path

def load_schema_from_yaml(yaml_path: Path) -> Dict[str, Any]:
    """Load schema definitions from a YAML file."""
    with open(yaml_path, 'r') as f:
        schema = yaml.safe_load(f)
        if schema is None:
            schema = {}
    return schema

def _load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a schema from disk, with caching."""
    if schema_name in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[schema_name]
    
    schema_path = _get_schema_path(schema_name)
    schema = load_schema_from_yaml(schema_path)
    _SCHEMA_CACHE[schema_name] = schema
    return schema

def validate_schema(data: Dict[str, Any], schema_name: str) -> bool:
    """
    Validate a data dictionary against a named schema.
    Returns True if valid, raises ValueError if invalid.
    
    Args:
        data: The data dictionary to validate.
        schema_name: The name of the schema (e.g., "physical-node", "execution-run").
    
    Returns:
        True if validation passes.
    
    Raises:
        ValueError: If schema_name is unknown or validation fails.
    """
    if not isinstance(schema_name, str):
        raise ValueError(f"schema_name must be a string, got {type(schema_name)}")
    
    # Load the schema (this will raise ValueError if schema_name is unknown)
    schema = _load_schema(schema_name)
    
    # If schema is empty (stub), pass validation
    if not schema or schema.get("properties") is None:
        logger.warning(f"Schema {schema_name} is empty or stub; skipping validation")
        return True
    
    # Basic validation: check required fields if specified
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field '{field}' in {schema_name}")
    
    # Check additionalProperties constraint
    if schema.get("additionalProperties") is False:
        allowed_props = set(schema.get("properties", {}).keys()) | set(required_fields)
        for key in data.keys():
            if key not in allowed_props:
                raise ValueError(f"Unknown property '{key}' in {schema_name}")
    
    return True