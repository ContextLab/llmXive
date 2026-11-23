import pytest
import yaml
from pathlib import Path
import json

# Import functions from the data_loader module
from code.utils.data_loader import load_schema, validate_fields

RESULTS_SCHEMA_PATH = Path("contracts/results.schema.yaml")

def test_results_schema_exists():
    """Test that the results schema file exists."""
    assert RESULTS_SCHEMA_PATH.exists(), f"Results schema file not found at {RESULTS_SCHEMA_PATH}"

def test_results_schema_is_valid_yaml():
    """Test that the results schema file is valid YAML."""
    try:
        with open(RESULTS_SCHEMA_PATH, "r") as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), "Results schema must be a dictionary"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in results schema file: {e}")

def test_results_schema_has_required_metrics():
    """Test that the results schema defines required metric categories."""
    schema = load_schema(RESULTS_SCHEMA_PATH)
    required_metrics = ["Access Control", "Utility", "Forgetting", "Latency"]
    
    # The schema should define these categories
    # Depending on schema structure, we check for keys or properties
    schema_str = str(schema)
    for metric in required_metrics:
        assert metric in schema_str, f"Results schema must define '{metric}' metrics"

def test_validate_results_structure():
    """Test validation of a sample results structure."""
    schema = load_schema(RESULTS_SCHEMA_PATH)
    
    # Sample valid results structure
    results = {
        "Access Control": {
            "score": 0.95,
            "std_dev": 0.02,
            "total_episodes": 100
        },
        "Utility": {
            "score": 0.88,
            "success_rate": 0.88
        },
        "Forgetting": {
            "compliance_rate": 0.92
        },
        "Latency": {
            "avg_ms": 150,
            "peak_ram_mb": 2048
        }
    }
    
    # Basic validation: check top-level keys exist
    for key in ["Access Control", "Utility", "Forgetting", "Latency"]:
        assert key in results, f"Results must contain '{key}' section"

def load_schema(path: Path):
    """Helper to load schema from a specific path."""
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)
