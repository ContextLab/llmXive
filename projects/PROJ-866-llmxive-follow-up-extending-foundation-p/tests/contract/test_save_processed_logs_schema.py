import json
import sys
from pathlib import Path
import tempfile
import pytest
import yaml

# Add code/ to path
code_root = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from engines.save_processed_logs import save_processed_logs, load_json_file

def load_schema(schema_path: Path):
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_against_schema(data, schema):
    """Simple manual validation against the schema structure."""
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})
    
    for field in required_fields:
        if field not in data:
            raise AssertionError(f"Missing required field: {field}")
        
        if field in properties:
            field_schema = properties[field]
            expected_type = field_schema.get("type")
            value = data[field]
            
            # Type checking (basic)
            if expected_type == "number":
                if not isinstance(value, (int, float)):
                    raise AssertionError(f"Field {field} must be a number, got {type(value)}")
            elif expected_type == "boolean":
                if not isinstance(value, bool):
                    raise AssertionError(f"Field {field} must be a boolean, got {type(value)}")
            elif expected_type == "string":
                # Allow string or specific string values for context_reduction_pct
                if field == "context_reduction_pct":
                    if not isinstance(value, (str, int, float)):
                        raise AssertionError(f"Field {field} must be number or string, got {type(value)}")
                else:
                    if not isinstance(value, str):
                        raise AssertionError(f"Field {field} must be a string, got {type(value)}")
            elif expected_type == "array":
                if not isinstance(value, list):
                    raise AssertionError(f"Field {field} must be an array, got {type(value)}")
            elif expected_type == "object":
                if not isinstance(value, dict):
                    raise AssertionError(f"Field {field} must be an object, got {type(value)}")
            elif isinstance(expected_type, list):
                # Multiple types allowed
                if not any(isinstance(value, t) for t in expected_type):
                    raise AssertionError(f"Field {field} must be one of {expected_type}, got {type(value)}")

@pytest.fixture
def schema_path():
    return Path(__file__).resolve().parent.parent.parent / "contracts" / "execution_log.schema.yaml"

def test_output_conforms_to_execution_log_schema(schema_path):
    """Test that saved processed logs conform to the execution_log.schema.yaml."""
    if not schema_path.exists():
        pytest.skip("Schema file not found")
        
    schema = load_schema(schema_path)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_dir = Path(tmp_dir) / "input"
        output_dir = Path(tmp_dir) / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create a test log
        log_data = {
            "workflow_id": "contract-test-001",
            "token_count": 150,
            "policy_violations": [
                {"node_id": "node-1", "rule_id": "rule-1"}
            ],
            "context_reduction_pct": 30.5,
            "is_valid": True,
            "status": "normal",
            "violation_details": [
                {"node_id": "node-1", "rule_id": "rule-1"}
            ],
            "timestamp": "2023-01-01T00:00:00"
        }
        
        input_file = input_dir / "log_contract-test-001_3.json"
        with open(input_file, 'w') as f:
            json.dump(log_data, f)
        
        save_processed_logs(input_dir, output_dir, [3])
        
        # Load and validate
        output_file = output_dir / "log_contract-test-001_3.json"
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        
        validate_against_schema(saved_data, schema)

def test_output_conforms_to_schema_edge_case(schema_path):
    """Test that edge case logs conform to the schema (deferred context)."""
    if not schema_path.exists():
        pytest.skip("Schema file not found")
        
    schema = load_schema(schema_path)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_dir = Path(tmp_dir) / "input"
        output_dir = Path(tmp_dir) / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        log_data = {
            "workflow_id": "edge-case-test",
            "token_count": 10,
            "policy_violations": [],
            "context_reduction_pct": "[deferred]",
            "is_valid": True,
            "status": "edge_case",
            "violation_details": [],
            "timestamp": "2023-01-01T00:00:00"
        }
        
        input_file = input_dir / "log_edge-case-test_0.json"
        with open(input_file, 'w') as f:
            json.dump(log_data, f)
        
        save_processed_logs(input_dir, output_dir, [0])
        
        output_file = output_dir / "log_edge-case-test_0.json"
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        
        validate_against_schema(saved_data, schema)
        
        # Specific checks for edge case
        assert saved_data["context_reduction_pct"] == "[deferred]"
        assert saved_data["status"] == "edge_case"