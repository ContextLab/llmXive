"""
Contract test for evaluation report schema.
Validates that evaluation reports conform to the expected structure.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_path, ensure_dir


class TestReportSchema:
    """
    Contract tests for evaluation report schema validation.
    """

    def test_schema_validation_function_exists(self):
        """Verify that the schema validation utility exists and is importable."""
        from tests.contract.schema_validator import validate_json_schema
        assert callable(validate_json_schema)

    def test_evaluation_report_schema_definition(self):
        """Verify the evaluation report schema exists."""
        from tests.contract.schema_validator import EVALUATION_REPORT_SCHEMA
        assert isinstance(EVALUATION_REPORT_SCHEMA, dict)

    def test_validate_valid_report(self):
        """Test validation against a valid evaluation report."""
        from tests.contract.schema_validator import validate_json_schema, EVALUATION_REPORT_SCHEMA

        valid_report = {
            "pipeline_version": "1.0.0",
            "timestamp": "2024-01-01T12:00:00Z",
            "metrics": {
                "accuracy": 0.85,
                "precision": 0.82,
                "recall": 0.88,
                "f1_score": 0.85,
                "baseline_accuracy": 0.5
            },
            "resource_usage": {
                "peak_ram_gb": 4.2,
                "total_time_hours": 2.5
            },
            "anomaly_detection": {
                "correlation_coefficient": 0.45,
                "p_value": 0.001,
                "threshold": 3.0
            }
        }

        is_valid, errors = validate_json_schema(valid_report, EVALUATION_REPORT_SCHEMA)
        assert is_valid, f"Valid report failed validation: {errors}"

    def test_validate_missing_metrics(self):
        """Test validation fails when metrics are missing."""
        from tests.contract.schema_validator import validate_json_schema, EVALUATION_REPORT_SCHEMA

        invalid_report = {
            "pipeline_version": "1.0.0",
            "timestamp": "2024-01-01T12:00:00Z"
            # Missing 'metrics'
        }

        is_valid, errors = validate_json_schema(invalid_report, EVALUATION_REPORT_SCHEMA)
        assert not is_valid
        assert len(errors) > 0

    def test_validate_invalid_resource_usage(self):
        """Test validation fails for invalid resource usage types."""
        from tests.contract.schema_validator import validate_json_schema, EVALUATION_REPORT_SCHEMA

        invalid_report = {
            "pipeline_version": "1.0.0",
            "timestamp": "2024-01-01T12:00:00Z",
            "metrics": {
                "accuracy": "not_a_number",  # Should be number
                "precision": 0.82,
                "recall": 0.88,
                "f1_score": 0.85,
                "baseline_accuracy": 0.5
            },
            "resource_usage": {
                "peak_ram_gb": 4.2,
                "total_time_hours": 2.5
            },
            "anomaly_detection": {
                "correlation_coefficient": 0.45,
                "p_value": 0.001,
                "threshold": 3.0
            }
        }

        is_valid, errors = validate_json_schema(invalid_report, EVALUATION_REPORT_SCHEMA)
        assert not is_valid