"""
Schema validation framework using pyyaml.
Validates ExecutionRun and RegressionModel structures.
Implements T007.
"""
import yaml
from pathlib import Path
from typing import Any, Dict, List
from orchestrator.logger import get_logger

logger = get_logger(__name__)

SCHEMAS = {
    "ExecutionRun": {
        "required": ["id", "timestamp", "node_count", "granularity", "throughput_ops"],
        "types": {
            "id": str,
            "timestamp": str,
            "node_count": int,
            "granularity": str,
            "throughput_ops": float
        }
    },
    "RegressionModel": {
        "required": ["model_id", "r_squared", "coefficients"],
        "types": {
            "model_id": str,
            "r_squared": float,
            "coefficients": dict
        }
    }
}

def validate_schema(data: Dict[str, Any], schema_name: str) -> bool:
    """
    Validate a data dictionary against a named schema.
    Returns True if valid, raises ValueError if invalid.
    """
    if schema_name not in SCHEMAS:
        raise ValueError(f"Unknown schema: {schema_name}")
    
    schema = SCHEMAS[schema_name]
    
    # Check required fields
    for field in schema["required"]:
        if field not in data:
            raise ValueError(f"Missing required field: {field} in {schema_name}")
    
    # Check types
    for field, expected_type in schema["types"].items():
        if field in data:
            if not isinstance(data[field], expected_type):
                raise ValueError(f"Invalid type for {field}: expected {expected_type}, got {type(data[field])}")
    
    return True

def load_schema_from_yaml(yaml_path: Path) -> Dict[str, Any]:
    """Load schema definitions from a YAML file."""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)
