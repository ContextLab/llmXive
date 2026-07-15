"""
Contract test for metrics schema (US2).

Validates that the metrics extracted by code/metrics/extract.py
conform to the schema defined in contracts/metrics.schema.yaml.

This test ensures:
1. The schema file exists and is valid YAML.
2. Generated metrics (simulated here to match expected structure) 
   pass validation against the schema.
3. The MetricsValidator in code/utils/validators.py correctly 
   identifies valid and invalid metrics.
"""
import json
import os
import sys
import pytest
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.validators import MetricsValidator
from config import Config

class TestMetricsSchemaContract:
    """Contract tests for the metrics schema."""
    
    @pytest.fixture
    def config(self):
        """Provide Config instance."""
        return Config()
    
    @pytest.fixture
    def valid_metrics_sample(self):
        """
        Provide a sample of valid metrics matching the schema.
        This mirrors the structure expected from code/metrics/extract.py.
        """
        return {
            "trace_id": "session_123e4567-e89b-12d3-a456-426614174000",
            "sequence_entropy": 2.45,
            "tool_repetition_frequency": 0.35,
            "argument_semantic_variance": 0.82,
            "trace_length": 15,
            "unique_tools_used": 4,
            "final_state_hash": "a1b2c3d4e5f6",
            "extraction_timestamp": "2023-10-27T10:00:00Z"
        }
    
    @pytest.fixture
    def invalid_metrics_sample(self):
        """
        Provide a sample of invalid metrics to test schema rejection.
        Missing required fields and wrong types.
        """
        return {
            "trace_id": "session_123",
            "sequence_entropy": "not_a_number",  # Wrong type
            "tool_repetition_frequency": 0.35,
            # Missing argument_semantic_variance
            "trace_length": "fifteen",  # Wrong type
            "unique_tools_used": 4,
            "final_state_hash": "a1b2c3",
            "extraction_timestamp": "2023-10-27"
        }
    
    def test_schema_file_exists(self, config):
        """Verify that the metrics schema file exists."""
        schema_path = Path(config.PROJECT_ROOT) / "contracts" / "metrics.schema.yaml"
        assert schema_path.exists(), f"Schema file not found at {schema_path}"
        
        # Verify it's valid YAML
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
            assert schema is not None
            assert "type" in schema
    
    def test_valid_metrics_pass_validation(self, valid_metrics_sample, config):
        """Verify that valid metrics pass the schema validation."""
        validator = MetricsValidator(config)
        
        is_valid, errors = validator.validate(valid_metrics_sample)
        
        assert is_valid, f"Valid metrics failed validation: {errors}"
        assert len(errors) == 0
    
    def test_invalid_metrics_fail_validation(self, invalid_metrics_sample, config):
        """Verify that invalid metrics fail the schema validation."""
        validator = MetricsValidator(config)
        
        is_valid, errors = validator.validate(invalid_metrics_sample)
        
        assert not is_valid, "Invalid metrics should have failed validation"
        assert len(errors) > 0
        # Check for specific expected errors
        error_messages = [e.get('message', str(e)) for e in errors]
        assert any("sequence_entropy" in msg or "type" in msg for msg in error_messages), \
            f"Expected type error for sequence_entropy, got: {errors}"
    
    def test_metrics_schema_structure_matches_extractor(self, config):
        """
        Verify that the schema expects the fields produced by the extractor.
        This ensures alignment between code/metrics/extract.py and the schema.
        """
        schema_path = Path(config.PROJECT_ROOT) / "contracts" / "metrics.schema.yaml"
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        required_fields = schema.get('properties', {}).keys()
        expected_fields = {
            'trace_id', 'sequence_entropy', 'tool_repetition_frequency',
            'argument_semantic_variance', 'trace_length', 'unique_tools_used',
            'final_state_hash', 'extraction_timestamp'
        }
        
        # All expected fields should be in the schema
        missing_in_schema = expected_fields - set(required_fields)
        assert len(missing_in_schema) == 0, \
            f"Schema is missing expected fields: {missing_in_schema}"
    
    def test_metrics_validator_uses_schema(self, config):
        """
        Verify that MetricsValidator actually uses the schema file
        for validation, not just hardcoded checks.
        """
        schema_path = Path(config.PROJECT_ROOT) / "contracts" / "metrics.schema.yaml"
        validator = MetricsValidator(config)
        
        # Check that the validator has loaded the schema
        assert hasattr(validator, 'schema')
        assert validator.schema is not None
        assert validator.schema.get('type') == 'object'