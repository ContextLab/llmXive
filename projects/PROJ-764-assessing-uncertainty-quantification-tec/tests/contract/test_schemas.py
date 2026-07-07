"""
Contract tests for output schemas in the UQ pipeline.

This module validates that the generated data artifacts adhere to the
defined JSON schemas (material_sample and uq_prediction).
"""

import json
import os
import glob
import pytest
from typing import Dict, Any, List

# Path constants relative to project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
CONTRACTS_DIR = os.path.join(PROJECT_ROOT, "code", "contracts")

# Schema file paths
MATERIAL_SCHEMA_PATH = os.path.join(CONTRACTS_DIR, "material_sample.schema.yaml")
UQ_SCHEMA_PATH = os.path.join(CONTRACTS_DIR, "uq_prediction.schema.yaml")


def load_yaml_schema(path: str) -> Dict[str, Any]:
    """Load a YAML schema file. Uses a simple parser if PyYAML is not available,
    but relies on PyYAML as per project requirements."""
    try:
        import yaml
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except ImportError:
        pytest.skip("PyYAML not installed for schema loading")
    except FileNotFoundError:
        pytest.fail(f"Schema file not found: {path}")


def validate_type(value: Any, expected_type: str) -> bool:
    """Basic type validation mapping JSON Schema types to Python types."""
    if expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "array":
        return isinstance(value, list)
    elif expected_type == "object":
        return isinstance(value, dict)
    return False


def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validates a dictionary against a simple JSON Schema-like definition.
    Returns a list of error messages.
    """
    errors = []
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Check required fields
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Check types of present fields
    for key, value in data.items():
        if key in properties:
            prop_def = properties[key]
            expected_type = prop_def.get("type")
            if expected_type and not validate_type(value, expected_type):
                errors.append(f"Field '{key}' has wrong type. Expected {expected_type}, got {type(value).__name__}")
        else:
            # Optional: warn on extra fields if schema says 'additionalProperties: false'
            if schema.get("additionalProperties") is False:
                errors.append(f"Unexpected field: {key}")

    return errors


@pytest.fixture
def uq_schema():
    """Load the UQ prediction schema."""
    # If the schema file doesn't exist yet (T009 might be pending in some flows),
    # we define the expected structure here to ensure the test is robust.
    # However, per T009, the file should exist.
    if os.path.exists(UQ_SCHEMA_PATH):
        return load_yaml_schema(UQ_SCHEMA_PATH)
    
    # Fallback definition matching the task requirements for T016
    return {
        "type": "object",
        "properties": {
            "sample_id": {"type": "string"},
            "method": {"type": "string"},
            "prediction": {"type": "number"},
            "variance": {"type": "number"},
            "lower_50": {"type": "number"},
            "upper_50": {"type": "number"},
            "lower_90": {"type": "number"},
            "upper_90": {"type": "number"}
        },
        "required": ["sample_id", "method", "prediction", "variance", "lower_50", "upper_50", "lower_90", "upper_90"]
    }


@pytest.fixture
def material_schema():
    """Load the material sample schema."""
    if os.path.exists(MATERIAL_SCHEMA_PATH):
        return load_yaml_schema(MATERIAL_SCHEMA_PATH)
    
    # Fallback definition
    return {
        "type": "object",
        "properties": {
            "sample_id": {"type": "string"},
            "composition": {"type": "string"},
            "formation_energy": {"type": "number"}
        },
        "required": ["sample_id", "composition", "formation_energy"]
    }


class TestUQPredictionSchema:
    """Tests for the uq_prediction.csv output schema."""

    def test_file_exists(self):
        """Verify that the UQ predictions file exists."""
        # T016 is responsible for generating this. If it hasn't run, this test fails.
        # We check the specific path defined in tasks.md.
        paths = glob.glob(os.path.join(RESULTS_DIR, "**", "uq_predictions.csv"), recursive=True)
        assert len(paths) > 0, f"File results/uq_predictions.csv not found. Has T016 run?"

    def test_schema_compliance(self, uq_schema):
        """Validate the content of uq_predictions.csv against the schema."""
        # Find the file again
        file_path = glob.glob(os.path.join(RESULTS_DIR, "**", "uq_predictions.csv"), recursive=True)[0]
        
        import pandas as pd
        df = pd.read_csv(file_path)

        # Convert DataFrame rows to list of dicts for validation
        records = df.to_dict(orient="records")
        
        errors = []
        for i, record in enumerate(records):
            record_errors = validate_schema(record, uq_schema)
            if record_errors:
                errors.append(f"Row {i}: {record_errors}")

        if errors:
            pytest.fail(f"Schema validation failed for uq_predictions.csv:\n" + "\n".join(errors))


class TestMaterialSampleSchema:
    """Tests for the material sample data schema (if available)."""

    def test_schema_compliance(self, material_schema):
        """Validate material data if it exists."""
        # Check for processed features or raw data if needed
        # This is a sanity check for the data pipeline
        raw_files = glob.glob(os.path.join(DATA_DIR, "raw", "*.parquet"))
        processed_files = glob.glob(os.path.join(DATA_DIR, "processed", "*.csv"))

        if not raw_files and not processed_files:
            pytest.skip("No material data files found to validate")

        # If we have a parquet file (from T005), we can try to validate a sample
        if raw_files:
            import pandas as pd
            df = pd.read_parquet(raw_files[0])
            # Check if the schema matches expectations (basic check)
            required_cols = material_schema.get("required", [])
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                pytest.fail(f"Raw data missing required columns: {missing}")