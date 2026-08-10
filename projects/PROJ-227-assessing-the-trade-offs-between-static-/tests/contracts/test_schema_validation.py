import json
import yaml
import jsonschema
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

def load_schema(filename: str) -> dict:
    """Load a YAML schema file and return it as a dict."""
    schema_path = CONTRACTS_DIR / filename
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def generate_sample_data(schema: dict) -> dict:
    """Generate minimal valid sample data based on schema required fields."""
    # This is a simplified generator for validation testing only.
    # In production, this would map real data to the schema.
    sample = {}
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    for key in required:
        prop = properties.get(key, {})
        prop_type = prop.get("type")
        prop_format = prop.get("format")
        enum_vals = prop.get("enum")
        
        if enum_vals:
            sample[key] = enum_vals[0]
        elif prop_type == "string":
            if prop_format == "date-time":
                sample[key] = "2023-10-27T10:00:00Z"
            else:
                sample[key] = "test-string"
        elif prop_type == "integer":
            sample[key] = 0
        elif prop_type == "number":
            sample[key] = 0.0
        elif prop_type == "boolean":
            sample[key] = False
        elif prop_type == "array":
            sample[key] = []
        elif prop_type == "object":
            sample[key] = {}
    
    return sample

@pytest.mark.parametrize("schema_file", [
    "dataset.schema.yaml",
    "analysis_log.schema.yaml",
    "analysis_results.schema.yaml",
    "dataset_manifest.schema.yaml",
    "statistical_report.schema.yaml",
    "tool_version.schema.yaml"
])
def test_schema_validation(schema_file):
    """Verify that each schema validates a corresponding minimal sample data."""
    schema = load_schema(schema_file)
    sample_data = generate_sample_data(schema)
    
    # Validate
    try:
        jsonschema.validate(instance=sample_data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Schema validation failed for {schema_file}: {e.message}")

def test_dataset_schema_specific():
    """Specific test for dataset schema enum values."""
    schema = load_schema("dataset.schema.yaml")
    valid_data = {
        "id": "test-123",
        "language": "python",
        "source": "HumanEval",
        "code": "def hello(): pass",
        "test_prompt": "print('hello')",
        "static_only": False,
        "created_at": "2023-10-27T10:00:00Z"
    }
    jsonschema.validate(instance=valid_data, schema=schema)

def test_analysis_log_schema_specific():
    """Specific test for analysis log status enum."""
    schema = load_schema("analysis_log.schema.yaml")
    valid_data = {
        "run_id": "run-001",
        "snippet_id": "snip-001",
        "tool_name": "CodeQL",
        "tool_version": "2.0.0",
        "timestamp": "2023-10-27T10:00:00Z",
        "status": "success",
        "duration_seconds": 1.5,
        "issues_found": []
    }
    jsonschema.validate(instance=valid_data, schema=schema)

def test_statistical_report_n_a_metrics():
    """Test that statistical report handles N/A for Precision/Recall/F1."""
    schema = load_schema("statistical_report.schema.yaml")
    valid_data = {
        "report_id": "report-001",
        "generated_at": "2023-10-27T10:00:00Z",
        "methodology_note": "See SPEC_AMENDMENT_001",
        "metrics": {
            "issue_detection_rate": 0.85,
            "pass_rate": 0.70,
            "precision": "N/A",
            "recall": "N/A",
            "f1_score": "N/A"
        },
        "correlation_tests": [
            {
                "test_type": "spearman",
                "coefficient": 0.65,
                "p_value": 0.03,
                "alpha": 0.05,
                "corrected": False
            }
        ]
    }
    jsonschema.validate(instance=valid_data, schema=schema)
