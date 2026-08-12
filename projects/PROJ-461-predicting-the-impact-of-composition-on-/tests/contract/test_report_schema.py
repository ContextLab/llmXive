"""
Contract test for report schema in tests/contract/test_report_schema.py.

This test verifies that the generated analysis report artifacts (JSON/HTML metadata)
conform to the defined schema in `contracts/report.schema.yaml`.

It ensures:
1. The schema file exists and is valid YAML.
2. The report artifacts (if they exist) match the schema structure.
3. Required fields (metrics, plots, sensitivity) are present.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

# Import the schema validator utility from the existing project API
from utils.schema_validator import load_schema, validate_instance

# Configure logger
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
REPORTS_DIR = PROJECT_ROOT / "reports"
SCHEMA_PATH = CONTRACTS_DIR / "report.schema.yaml"
METRICS_PATH = REPORTS_DIR / "metrics.json"
SENSITIVITY_PATH = REPORTS_DIR / "sensitivity_analysis.json"

def load_report_schema() -> Dict[str, Any]:
    """Load the report schema from the contracts directory."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    
    return schema

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file if it exists."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class TestReportSchema:
    """Contract tests for the analysis report schema."""

    def test_schema_file_exists_and_valid(self):
        """Verify that the report schema file exists and is valid YAML."""
        assert SCHEMA_PATH.exists(), f"Schema file missing at {SCHEMA_PATH}"
        
        try:
            schema = load_report_schema()
            assert isinstance(schema, dict), "Schema must be a dictionary"
            assert "type" in schema, "Schema must define a root type"
            assert schema["type"] == "object", "Root schema type must be object"
            logger.info("Schema file exists and is valid YAML.")
        except yaml.YAMLError as e:
            pytest.fail(f"Schema file is not valid YAML: {e}")

    def test_metrics_conform_to_schema(self):
        """Verify that metrics.json (if present) conforms to the report schema."""
        if not METRICS_PATH.exists():
            pytest.skip("metrics.json not found. Skipping metrics validation.")
        
        schema = load_report_schema()
        validator = load_schema(schema)
        
        metrics_data = load_json_file(METRICS_PATH)
        
        if not metrics_data:
            pytest.skip("metrics.json is empty.")

        errors = list(validator.iter_errors(metrics_data))
        assert len(errors) == 0, f"metrics.json does not conform to schema: {[e.message for e in errors]}"
        logger.info("metrics.json conforms to report schema.")

    def test_sensitivity_analysis_conforms_to_schema(self):
        """Verify that sensitivity_analysis.json (if present) conforms to the report schema."""
        if not SENSITIVITY_PATH.exists():
            pytest.skip("sensitivity_analysis.json not found. Skipping sensitivity validation.")
        
        schema = load_report_schema()
        validator = load_schema(schema)
        
        sensitivity_data = load_json_file(SENSITIVITY_PATH)
        
        if not sensitivity_data:
            pytest.skip("sensitivity_analysis.json is empty.")

        errors = list(validator.iter_errors(sensitivity_data))
        assert len(errors) == 0, f"sensitivity_analysis.json does not conform to schema: {[e.message for e in errors]}"
        logger.info("sensitivity_analysis.json conforms to report schema.")

    def test_required_report_structure(self):
        """
        Verify that the combined report structure (metrics + sensitivity) 
        contains all required top-level keys defined in the schema.
        """
        schema = load_report_schema()
        required_props = schema.get("properties", {})
        
        # We check if the schema defines required properties
        required_fields = schema.get("required", [])
        
        if not required_fields:
            logger.warning("Schema does not define 'required' fields.")
            return

        # Load available data
        combined_data = {}
        if METRICS_PATH.exists():
            combined_data.update(load_json_file(METRICS_PATH))
        if SENSITIVITY_PATH.exists():
            combined_data.update(load_json_file(SENSITIVITY_PATH))
        
        # If no data exists, skip (expected in early pipeline stages)
        if not combined_data:
            pytest.skip("No report data found to validate structure.")

        missing_fields = [f for f in required_fields if f not in combined_data]
        
        # Note: This test might fail if the pipeline hasn't generated all artifacts yet.
        # In a full run, this ensures the final report is complete.
        if missing_fields:
            # We treat this as a soft failure or skip if data is partial
            # For a strict contract test, we assert.
            # However, since T028 is a contract test, it should pass if the schema is valid
            # and the data that *exists* matches. If data is missing entirely, it's a pipeline issue.
            # We assert that if we have data, it matches the schema (covered by previous tests).
            # This test specifically checks for the presence of required keys if data is present.
            if METRICS_PATH.exists() or SENSITIVITY_PATH.exists():
                pytest.fail(f"Missing required report fields: {missing_fields}")
        
        logger.info("Report structure validation passed.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
