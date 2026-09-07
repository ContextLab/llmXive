"""
Contract tests to validate generated artifacts against schema definitions.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest
import yaml

# Add project root to path if running standalone
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.common import read_yaml, write_yaml, read_json, write_json

SCHEMA_DIR = project_root / "contracts"

def load_schema(schema_name: str) -> dict:
    """Load a schema from the contracts directory."""
    schema_path = SCHEMA_DIR / f"{schema_name}.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    return read_yaml(schema_path)

def validate_json_against_schema(data: dict, schema: dict) -> bool:
    """
    Basic validation of JSON data against a YAML schema.
    Checks for required fields and basic type constraints.
    Note: This is a simplified validator for CI purposes.
    """
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})

    # Check required fields
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Check types for known properties
    for field, value in data.items():
        if field in properties:
            prop_schema = properties[field]
            expected_type = prop_schema.get("type")

            if expected_type == "object" and not isinstance(value, dict):
                raise ValueError(f"Field '{field}' must be an object")
            elif expected_type == "array" and not isinstance(value, list):
                raise ValueError(f"Field '{field}' must be an array")
            elif expected_type == "string" and not isinstance(value, str):
                raise ValueError(f"Field '{field}' must be a string")
            elif expected_type == "integer" and not isinstance(value, int):
                raise ValueError(f"Field '{field}' must be an integer")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                raise ValueError(f"Field '{field}' must be a number")
            elif expected_type == "boolean" and not isinstance(value, bool):
                raise ValueError(f"Field '{field}' must be a boolean")

    return True

@pytest.fixture
def temp_dataset_file():
    """Create a temporary JSONL file with valid dataset records."""
    valid_record = {
        "id": "test_001",
        "steps": [
            {
                "step_id": "step_1",
                "code": "def step_1(): return 5",
                "dependencies": []
            },
            {
                "step_id": "step_2",
                "code": "def step_2(): return step_1() + 1",
                "dependencies": ["step_1"]
            }
        ]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        json.dump(valid_record, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_masking_file():
    """Create a temporary JSON file with valid masking map."""
    valid_record = {
        "batch_id": 1,
        "examples": [
            {
                "example_id": "test_001",
                "masks": [
                    {
                        "start_token": 10,
                        "end_token": 20,
                        "mask_type": "body",
                        "step_id": "step_1"
                    }
                ]
            }
        ]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(valid_record, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_eval_file():
    """Create a temporary JSON file with valid evaluation results."""
    valid_record = {
        "models": ["FIM", "NL-Control", "Baseline"],
        "scores": {
            "FIM": {"accuracy": 0.85, "count": 100},
            "NL-Control": {"accuracy": 0.72, "count": 100},
            "Baseline": {"accuracy": 0.65, "count": 100}
        },
        "statistical_test": {
            "test_type": "paired_t_test",
            "p_value": 0.03,
            "statistic": 2.45,
            "is_significant": True,
            "comparison": "FIM vs NL-Control"
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(valid_record, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_dataset_schema_validates_jsonl(temp_dataset_file):
    """Verify dataset.schema.yaml against generated JSONL."""
    schema = load_schema("dataset")
    with open(temp_dataset_file, 'r') as f:
        data = json.load(f)
    validate_json_against_schema(data, schema)

def test_masking_map_schema_validates_json(temp_masking_file):
    """Verify masking_map.schema.yaml against generated JSON."""
    schema = load_schema("masking_map")
    with open(temp_masking_file, 'r') as f:
        data = json.load(f)
    validate_json_against_schema(data, schema)

def test_evaluation_results_schema_validates_json(temp_eval_file):
    """Verify evaluation_results.schema.yaml against generated JSON."""
    schema = load_schema("evaluation_results")
    with open(temp_eval_file, 'r') as f:
        data = json.load(f)
    validate_json_against_schema(data, schema)