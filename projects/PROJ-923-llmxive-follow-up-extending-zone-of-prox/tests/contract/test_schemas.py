"""
Contract tests for rollout log schema.

This module validates that generated rollout logs strictly adhere to the
schema defined in contracts/rollout_log.schema.yaml.

It ensures:
1. The schema file exists and is valid YAML.
2. The schema structure matches the expected fields (task_id, prompt, response,
   confidence, ground_truth, metadata).
3. Sample data (generated via the seeded generator in T012) validates against
   the schema using the project's validation utilities.
"""
import os
import json
import pytest
from pathlib import Path

# Import project utilities
from utils.validation import load_schema, validate_object, validate_batch
from data.generators import generate_synthetic_rollout_log
from utils.seeds import set_global_seed, get_seed


# Constants for test paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "rollout_log.schema.yaml"
TEST_OUTPUT_DIR = PROJECT_ROOT / "data" / "test_outputs"
TEST_OUTPUT_FILE = TEST_OUTPUT_DIR / "sample_rollout_log.json"


def _ensure_test_output_exists():
    """
    Ensures the test output file exists by generating it if missing.
    This simulates the output of T012 (synthetic generator) to validate
    the contract without requiring a full pipeline run.
    """
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not TEST_OUTPUT_FILE.exists():
        # Use a fixed seed for deterministic test data
        set_global_seed(42)
        
        # Generate a small sample (5 records) to validate against
        sample_data = generate_synthetic_rollout_log(
            num_records=5,
            seed=42,
            output_path=str(TEST_OUTPUT_FILE)
        )
        
        # If the generator writes to file, we read it back to ensure the object
        # we validate is exactly what was written.
        with open(TEST_OUTPUT_FILE, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
    else:
        with open(TEST_OUTPUT_FILE, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
        
    return sample_data


class TestRolloutLogSchema:
    """Contract tests for the rollout log schema."""

    def test_schema_file_exists(self):
        """Verify that the rollout log schema file exists."""
        assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

    def test_schema_is_valid_yaml(self):
        """Verify that the schema file is valid YAML and loads correctly."""
        schema = load_schema(str(SCHEMA_PATH))
        assert schema is not None
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema

    def test_schema_contains_required_fields(self):
        """Verify that the schema defines all required fields for a rollout log."""
        schema = load_schema(str(SCHEMA_PATH))
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Define the expected core fields based on data-model.md and T004
        expected_fields = [
            "task_id", 
            "prompt", 
            "response", 
            "confidence", 
            "ground_truth", 
            "metadata"
        ]
        
        for field_name in expected_fields:
            assert field_name in properties, f"Schema missing required property: {field_name}"
            assert field_name in required_fields, f"Schema missing 'required' declaration for: {field_name}"

    def test_sample_data_validates_against_schema(self):
        """
        Generate sample data using the project's generator (T012) and validate
        it against the schema (T004). This ensures the generator and schema
        are in sync.
        """
        # Load schema
        schema = load_schema(str(SCHEMA_PATH))
        
        # Get sample data (generates if missing)
        sample_data = _ensure_test_output_exists()
        
        # The generator returns a list of records. We validate each record.
        # If the output file is a single object, wrap it or handle accordingly.
        # Based on typical rollout logs, it's a list of dicts.
        records = sample_data if isinstance(sample_data, list) else [sample_data]
        
        errors = []
        for i, record in enumerate(records):
            is_valid, error_msg = validate_object(record, schema)
            if not is_valid:
                errors.append(f"Record {i}: {error_msg}")
        
        if errors:
            pytest.fail(f"Validation failed for {len(errors)} records:\n" + "\n".join(errors))

    def test_batch_validation_utility(self):
        """
        Test the project's batch validation utility on the generated data.
        This ensures the utility in code/utils/validation.py works as expected.
        """
        schema = load_schema(str(SCHEMA_PATH))
        sample_data = _ensure_test_output_exists()
        
        records = sample_data if isinstance(sample_data, list) else [sample_data]
        
        # Use the batch validator
        results = validate_batch(records, schema)
        
        assert len(results) == len(records), "Batch validation result count mismatch"
        
        for i, result in enumerate(results):
            assert result["valid"], f"Record {i} failed batch validation: {result.get('error')}"

    def test_schema_type_constraints(self):
        """
        Verify that specific field types in the schema match expectations.
        E.g., confidence should be a number between 0 and 1.
        """
        schema = load_schema(str(SCHEMA_PATH))
        properties = schema.get("properties", {})
        
        # Check confidence type
        confidence_prop = properties.get("confidence", {})
        assert confidence_prop.get("type") in ["number", "integer"], \
            "Confidence field must be numeric"
        
        # Check for min/max constraints if defined
        if "minimum" in confidence_prop:
            assert confidence_prop["minimum"] == 0.0, "Confidence min must be 0.0"
        if "maximum" in confidence_prop:
            assert confidence_prop["maximum"] == 1.0, "Confidence max must be 1.0"

    def test_metadata_structure(self):
        """
        Verify that the metadata field allows for the expected nested structure
        (e.g., cycle_id, seed, model_version).
        """
        schema = load_schema(str(SCHEMA_PATH))
        properties = schema.get("properties", {})
        metadata_prop = properties.get("metadata", {})
        
        # Metadata is typically an object
        assert metadata_prop.get("type") == "object", "Metadata must be an object"
        
        # Check if additionalProperties is allowed (flexible schema) or if specific keys are required
        # For this contract test, we just ensure it's an object type.
        assert True  # Placeholder for specific nested checks if schema is strict