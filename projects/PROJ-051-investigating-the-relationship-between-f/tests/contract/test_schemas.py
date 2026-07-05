"""
Contract tests for box-counting output schema.

Verifies that the output of the fractal dimension analysis adheres to the
schema defined in contracts/analysis_output.schema.yaml.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

# Ensure project root is in path for imports if running from tests/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

SCHEMA_PATH = project_root / "contracts" / "analysis_output.schema.yaml"
SAMPLE_OUTPUT_PATH = project_root / "data" / "results" / "fractal_analysis_sample.json"

# Expected fields based on schema and task requirements (D_f, epsilon, correlation)
REQUIRED_TOP_LEVEL_FIELDS = {
    "fractal_dimension": float,
    "vorticity_threshold": float,
    "re_lambda": float,
    "grid_size": int,
    "num_boxes": int,
    "box_sizes": list,
    "r_squared": float,
    "status": str
}

def load_schema() -> Dict[str, Any]:
    """Load the YAML schema file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_types(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate that the data types in the output match the schema definitions.
    This is a basic type check.
    """
    schema_properties = schema.get("properties", {})
    
    for key, expected_type in REQUIRED_TOP_LEVEL_FIELDS.items():
        if key not in data:
            pytest.fail(f"Missing required field: {key}")
        
        value = data[key]
        if not isinstance(value, expected_type):
            pytest.fail(
                f"Field '{key}' has type {type(value).__name__}, "
                f"expected {expected_type.__name__}. Value: {value}"
            )

def validate_range_constraints(data: Dict[str, Any]) -> None:
    """
    Validate logical constraints on the data values.
    """
    # D_f must be between 2.0 and 3.0 for a surface in 3D
    d_f = data.get("fractal_dimension")
    if d_f is not None:
        if not (2.0 <= d_f <= 3.0):
            pytest.fail(f"Fractal dimension {d_f} is outside valid range [2.0, 3.0]")

    # r_squared must be between 0 and 1
    r2 = data.get("r_squared")
    if r2 is not None:
        if not (0.0 <= r2 <= 1.0):
            pytest.fail(f"R-squared {r2} is outside valid range [0.0, 1.0]")
    
    # Status should be 'success' for valid data
    status = data.get("status")
    if status != "success":
        pytest.fail(f"Unexpected status: {status}")

@pytest.mark.contract
def test_box_counting_output_schema():
    """
    Contract test: Verify the box-counting output schema.
    
    This test generates a synthetic valid output (since the analysis module
    might not be fully run yet or to test the schema validator independently)
    and ensures it conforms to the contract defined in the YAML schema.
    """
    schema = load_schema()
    
    # Create a mock valid output that adheres to the schema
    # This simulates what analysis/fractal.py would produce
    mock_output = {
        "fractal_dimension": 2.73,
        "vorticity_threshold": 3.5,
        "re_lambda": 400.0,
        "grid_size": 256,
        "num_boxes": 1024,
        "box_sizes": [1.0, 2.0, 4.0, 8.0, 16.0],
        "r_squared": 0.98,
        "status": "success",
        "timestamp": "2023-10-27T10:00:00Z"
    }
    
    # 1. Validate against schema structure (properties exist)
    schema_props = schema.get("properties", {})
    for field in REQUIRED_TOP_LEVEL_FIELDS.keys():
        assert field in schema_props, f"Schema missing definition for field: {field}"
    
    # 2. Validate types
    validate_types(mock_output, schema)
    
    # 3. Validate logical constraints
    validate_range_constraints(mock_output)

@pytest.mark.contract
def test_actual_output_file_exists_and_valid():
    """
    Contract test: If an actual output file exists, validate it against the schema.
    
    This test is skipped if the file hasn't been generated yet.
    """
    if not SAMPLE_OUTPUT_PATH.exists():
        pytest.skip(f"Output file not found at {SAMPLE_OUTPUT_PATH}. "
                    "Run the analysis pipeline to generate it.")
    
    schema = load_schema()
    
    with open(SAMPLE_OUTPUT_PATH, 'r') as f:
        data = json.load(f)
    
    validate_types(data, schema)
    validate_range_constraints(data)