"""
Contract tests for validating JSON data against YAML schemas.
"""
import json
import os
import sys
import yaml
import pytest
from pathlib import Path
from typing import Dict, Any

# Add code/utils to path for schema loading helpers if needed, 
# though we will implement validation logic directly here to avoid circular deps
# or import from utils.verify_schema if it exposes a validator.
# For T030, we implement the specific validator for the final report.

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a YAML schema from the contracts directory."""
    schema_path = CONTRACTS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def load_json_data(file_name: str) -> Dict[str, Any]:
    """Load JSON data from the data/processed directory."""
    data_path = DATA_PROCESSED_DIR / file_name
    if not data_path.exists():
        # If the file doesn't exist yet, we might be in a setup phase or the pipeline hasn't run.
        # However, for a contract test, we expect the file to exist if the pipeline ran.
        # We raise a clear error if missing, as the test cannot validate a missing file.
        raise FileNotFoundError(f"Data file not found: {data_path}")
    with open(data_path, "r") as f:
        return json.load(f)


@pytest.mark.skipif(
    not HAS_JSONSCHEMA,
    reason="jsonschema library not installed. Install with: pip install jsonschema"
)
class TestFinalReportSchema:
    """Contract test for the final audit report JSON structure."""

    def test_final_report_schema(self):
        """
        Validates data/processed/audit_report.json against contracts/report.schema.yaml.
        Ensures all required fields are present and types match the specification.
        """
        # 1. Load the schema
        schema = load_schema("report.schema.yaml")
        
        # 2. Load the data
        data = load_json_data("audit_report.json")

        # 3. Validate
        import jsonschema
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            pytest.fail(f"JSON data failed schema validation: {e.message} at path {list(e.path)}")

        # 4. Additional explicit checks for critical fields (defense in depth)
        assert "report_id" in data
        assert "generated_at" in data
        assert "dataset_summary" in data
        assert "power_results" in data
        assert "mdes_results" in data
        assert "success_metrics" in data
        assert "disclaimer" in data
        
        # Check success metrics specifically
        sm = data["success_metrics"]
        assert "observed_power_below_threshold" in sm
        assert "mdes_above_threshold" in sm
        
        # Check types
        assert isinstance(sm["observed_power_below_threshold"], (int, float))
        assert isinstance(sm["mdes_above_threshold"], (int, float))
        
        # Check ranges
        assert 0.0 <= sm["observed_power_below_threshold"] <= 1.0
        assert 0.0 <= sm["mdes_above_threshold"] <= 1.0
