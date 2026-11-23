"""
Unit tests for code/validate_schemas.py
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# We need to ensure the code directory is in the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate_schemas import load_schema, validate_artifact, validate_all_artifacts
import jsonschema


class TestLoadSchema:
    def test_load_json_schema(self, tmp_path):
        """Test loading a JSON schema."""
        schema_content = {"type": "object", "properties": {"name": {"type": "string"}}}
        schema_file = tmp_path / "test.schema.json"
        schema_file.write_text(json.dumps(schema_content))

        with patch("validate_schemas.CONTRACTS_DIR", str(tmp_path)):
            result = load_schema("test.schema.json")
            assert result == schema_content

    def test_load_yaml_schema(self, tmp_path):
        """Test loading a YAML schema."""
        schema_content = {"type": "object", "properties": {"name": {"type": "string"}}}
        schema_file = tmp_path / "test.schema.yaml"
        # Simple YAML representation
        schema_file.write_text("type: object\nproperties:\n  name:\n    type: string")

        with patch("validate_schemas.CONTRACTS_DIR", str(tmp_path)):
            # Ensure pyyaml is mocked or available
            with patch("validate_schemas.yaml") as mock_yaml:
                mock_yaml.safe_load.return_value = schema_content
                result = load_schema("test.schema.yaml")
                assert result == schema_content
                mock_yaml.safe_load.assert_called_once()

    def test_schema_not_found(self, tmp_path):
        """Test error when schema file is not found."""
        with patch("validate_schemas.CONTRACTS_DIR", str(tmp_path)):
            with pytest.raises(FileNotFoundError):
                load_schema("nonexistent.schema.json")


class TestValidateArtifact:
    @pytest.fixture
    def mock_schema(self):
        return {
            "type": "object",
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"}
            }
        }

    def test_validate_json_valid(self, tmp_path, mock_schema):
        """Test validating a valid JSON artifact."""
        data = {"id": 1, "name": "test"}
        artifact_file = tmp_path / "valid.json"
        artifact_file.write_text(json.dumps(data))

        schema_file = tmp_path / "test.schema.json"
        schema_file.write_text(json.dumps(mock_schema))

        with patch("validate_schemas.CONTRACTS_DIR", str(tmp_path)):
            is_valid, error = validate_artifact(artifact_file, "test.schema.json")
            assert is_valid is True
            assert error is None

    def test_validate_json_invalid(self, tmp_path, mock_schema):
        """Test validating an invalid JSON artifact (missing required field)."""
        data = {"id": 1}  # Missing 'name'
        artifact_file = tmp_path / "invalid.json"
        artifact_file.write_text(json.dumps(data))

        schema_file = tmp_path / "test.schema.json"
        schema_file.write_text(json.dumps(mock_schema))

        with patch("validate_schemas.CONTRACTS_DIR", str(tmp_path)):
            is_valid, error = validate_artifact(artifact_file, "test.schema.json")
            assert is_valid is False
            assert error is not None
            assert "required" in error.lower()

    def test_validate_json_invalid_syntax(self, tmp_path):
        """Test validating a JSON artifact with syntax errors."""
        artifact_file = tmp_path / "bad.json"
        artifact_file.write_text("{ invalid json }")

        schema_file = tmp_path / "test.schema.json"
        schema_file.write_text("{}")

        with patch("validate_schemas.CONTRACTS_DIR", str(tmp_path)):
            is_valid, error = validate_artifact(artifact_file, "test.schema.json")
            assert is_valid is False
            assert "Invalid JSON" in error

    def test_validate_csv_valid(self, tmp_path, mock_schema):
        """Test validating a valid CSV artifact."""
        import pandas as pd
        df = pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})
        artifact_file = tmp_path / "valid.csv"
        df.to_csv(artifact_file, index=False)

        schema_file = tmp_path / "test.schema.json"
        schema_file.write_text(json.dumps(mock_schema))

        with patch("validate_schemas.CONTRACTS_DIR", str(tmp_path)):
            is_valid, error = validate_artifact(artifact_file, "test.schema.json")
            assert is_valid is True
            assert error is None

    def test_validate_csv_missing_columns(self, tmp_path, mock_schema):
        """Test validating a CSV artifact with missing columns."""
        import pandas as pd
        df = pd.DataFrame({"id": [1, 2]})  # Missing 'name'
        artifact_file = tmp_path / "invalid.csv"
        df.to_csv(artifact_file, index=False)

        schema_file = tmp_path / "test.schema.json"
        schema_file.write_text(json.dumps(mock_schema))

        with patch("validate_schemas.CONTRACTS_DIR", str(tmp_path)):
            is_valid, error = validate_artifact(artifact_file, "test.schema.json")
            assert is_valid is False
            assert "Missing required columns" in error

    def test_artifact_not_found(self, tmp_path):
        """Test error when artifact file is not found."""
        with patch("validate_schemas.CONTRACTS_DIR", str(tmp_path)):
            is_valid, error = validate_artifact(tmp_path / "nonexistent.json", "test.schema.json")
            assert is_valid is False
            assert "not found" in error.lower()

    def test_unsupported_file_type(self, tmp_path):
        """Test error for unsupported file types."""
        artifact_file = tmp_path / "test.txt"
        artifact_file.write_text("content")

        schema_file = tmp_path / "test.schema.json"
        schema_file.write_text("{}")

        with patch("validate_schemas.CONTRACTS_DIR", str(tmp_path)):
            is_valid, error = validate_artifact(artifact_file, "test.schema.json")
            assert is_valid is False
            assert "Unsupported file type" in error


class TestValidateAllArtifacts:
    def test_validate_all_success(self, tmp_path, monkeypatch):
        """Test successful validation of all artifacts."""
        # Create mock artifacts
        (tmp_path / "data").mkdir()
        (tmp_path / "contracts").mkdir()

        # Mock artifacts
        changed_lines = tmp_path / "data" / "changed_lines.json"
        changed_lines.write_text(json.dumps({"project_id": 1, "lines": [1, 2]}))

        coverage = tmp_path / "data" / "coverage_metrics.csv"
        coverage.write_text("project_id,test_type,coverage_percentage\n1,unit,80.0")

        analysis = tmp_path / "data" / "analysis_results.json"
        analysis.write_text(json.dumps({"p_value": 0.05, "test_type": "t-test"}))

        # Mock schemas
        schema_dataset = {"type": "object", "required": ["project_id", "lines"]}
        (tmp_path / "contracts" / "dataset.schema.json").write_text(json.dumps(schema_dataset))

        schema_coverage = {"type": "object", "required": ["project_id", "test_type", "coverage_percentage"]}
        (tmp_path / "contracts" / "coverage.schema.json").write_text(json.dumps(schema_coverage))

        schema_analysis = {"type": "object", "required": ["p_value", "test_type"]}
        (tmp_path / "contracts" / "analysis_result.schema.json").write_text(json.dumps(schema_analysis))

        # Patch paths
        monkeypatch.chdir(tmp_path)
        with patch("validate_schemas.CONTRACTS_DIR", str(tmp_path / "contracts")):
            with patch("validate_schemas.get_data_dir", return_value=str(tmp_path / "data")):
                with patch("validate_schemas.validate_artifact") as mock_validate:
                    # Mock validate_artifact to return True for all
                    mock_validate.return_value = (True, None)
                    result = validate_all_artifacts()
                    assert result is True

    def test_validate_all_failure(self, tmp_path, monkeypatch):
        """Test failure when one artifact is invalid."""
        (tmp_path / "data").mkdir()
        (tmp_path / "contracts").mkdir()

        # Mock artifacts
        changed_lines = tmp_path / "data" / "changed_lines.json"
        changed_lines.write_text(json.dumps({"project_id": 1, "lines": [1, 2]}))

        # Patch paths
        monkeypatch.chdir(tmp_path)
        with patch("validate_schemas.CONTRACTS_DIR", str(tmp_path / "contracts")):
            with patch("validate_schemas.get_data_dir", return_value=str(tmp_path / "data")):
                with patch("validate_schemas.validate_artifact") as mock_validate:
                    # First returns True, second returns False
                    mock_validate.side_effect = [(True, None), (False, "Error"), (True, None)]
                    result = validate_all_artifacts()
                    assert result is False
                    # Check that validate_artifact was called for each artifact
                    assert mock_validate.call_count == 3