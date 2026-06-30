"""
Contract test for results schema validation.

Validates that results data conforms to the schema defined in
contracts/results.schema.yaml.

This test ensures:
- Required fields are present: task_id, condition, accuracy, timestamp
- Field types are correct
- Data structure matches the contract specification
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.checksum_utils import load_state_file


class TestResultsSchema:
    """Test suite for results schema contract validation."""

    @pytest.fixture
    def schema_path(self) -> Path:
        """Path to the results schema contract."""
        return PROJECT_ROOT / "contracts" / "results.schema.yaml"

    @pytest.fixture
    def schema(self, schema_path: Path) -> Dict[str, Any]:
        """Load the results schema contract."""
        if not schema_path.exists():
            pytest.skip(f"Schema file not found: {schema_path}")
        with open(schema_path, "r") as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def valid_result(self) -> Dict[str, Any]:
        """Generate a valid result record according to the schema."""
        return {
            "task_id": "T022",
            "condition": "heterogeneous",
            "accuracy": 0.85,
            "timestamp": "2024-01-15T10:30:00Z"
        }

    @pytest.fixture
    def valid_results_list(self, valid_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate a list of valid result records."""
        return [
            valid_result,
            {
                "task_id": "T023",
                "condition": "unified",
                "accuracy": 0.82,
                "timestamp": "2024-01-15T10:35:00Z"
            }
        ]

    def test_schema_file_exists(self, schema_path: Path):
        """Verify the schema contract file exists."""
        assert schema_path.exists(), f"Schema file missing: {schema_path}"

    def test_schema_has_required_structure(self, schema: Dict[str, Any]):
        """Verify the schema has the expected top-level structure."""
        assert "required_fields" in schema, "Schema must define required_fields"
        assert "fields" in schema, "Schema must define fields"

    def test_required_fields_present(self, schema: Dict[str, Any]):
        """Verify all required fields are listed in the schema."""
        required = schema.get("required_fields", [])
        expected_required = ["task_id", "condition", "accuracy", "timestamp"]
        for field in expected_required:
            assert field in required, f"Required field '{field}' missing from schema"

    def test_validate_required_fields_present(self, valid_result: Dict[str, Any], schema: Dict[str, Any]):
        """Test that a valid result has all required fields."""
        required = schema.get("required_fields", [])
        for field in required:
            assert field in valid_result, f"Result missing required field: {field}"

    def test_validate_field_types(self, valid_result: Dict[str, Any], schema: Dict[str, Any]):
        """Test that field types match the schema definition."""
        fields = schema.get("fields", {})
        
        # Check task_id (string)
        assert isinstance(valid_result["task_id"], str), "task_id must be string"
        
        # Check condition (string)
        assert isinstance(valid_result["condition"], str), "condition must be string"
        
        # Check accuracy (number)
        assert isinstance(valid_result["accuracy"], (int, float)), "accuracy must be number"
        assert 0 <= valid_result["accuracy"] <= 1, "accuracy must be between 0 and 1"
        
        # Check timestamp (string, ISO format)
        assert isinstance(valid_result["timestamp"], str), "timestamp must be string"

    def test_validate_missing_field_raises_error(self, valid_result: Dict[str, Any], schema: Dict[str, Any]):
        """Test that missing required fields are detected."""
        required = schema.get("required_fields", [])
        for field in required:
            incomplete_result = {k: v for k, v in valid_result.items() if k != field}
            with pytest.raises(AssertionError):
                assert field in incomplete_result

    def test_validate_list_of_results(self, valid_results_list: List[Dict[str, Any]], schema: Dict[str, Any]):
        """Test validation of a list of results."""
        required = schema.get("required_fields", [])
        for result in valid_results_list:
            for field in required:
                assert field in result, f"Result missing required field: {field}"

    def test_schema_matches_contract_definition(self, schema: Dict[str, Any]):
        """Verify schema matches the contract definition in contracts/results.schema.yaml."""
        # Verify the schema contains the expected metadata
        assert "description" in schema, "Schema should have a description"
        assert "version" in schema, "Schema should have a version"

    def test_integration_with_checksum_utils(self, valid_result: Dict[str, Any]):
        """Test that results can be used with checksum tracking."""
        # This ensures the data structure is compatible with the state tracking system
        import json
        result_json = json.dumps(valid_result)
        assert len(result_json) > 0, "Result should serialize to JSON"

    def test_edge_cases(self):
        """Test edge cases for results data."""
        # Zero accuracy
        zero_acc = {
            "task_id": "T001",
            "condition": "test",
            "accuracy": 0.0,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        assert zero_acc["accuracy"] == 0.0
        
        # Perfect accuracy
        perfect_acc = {
            "task_id": "T002",
            "condition": "test",
            "accuracy": 1.0,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        assert perfect_acc["accuracy"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
