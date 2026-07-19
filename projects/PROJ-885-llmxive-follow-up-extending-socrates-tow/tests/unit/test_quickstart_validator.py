import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
from analysis.quickstart_validator import (
    check_directories,
    check_files,
    check_imports,
    validate_json_schema,
    check_data_artifacts,
    run_statistical_dry_run,
    REQUIRED_DIRS,
    REQUIRED_FILES,
    SCHEMA_CHECKS
)

class TestCheckDirectories:
    def test_missing_directory(self, tmp_path, monkeypatch):
        """Test detection of a missing directory."""
        # Patch the function to return a list containing a non-existent path
        with patch.object(Path, 'exists', return_value=False):
            passed, missing = check_directories()
            assert passed is False
            assert len(missing) > 0

    def test_all_directories_exist(self, tmp_path, monkeypatch):
        """Test success when all directories exist."""
        # Mock the existence check for all required dirs
        with patch('analysis.quickstart_validator.Path') as MockPath:
            mock_instance = MagicMock()
            mock_instance.exists.return_value = True
            mock_instance.is_dir.return_value = True
            MockPath.return_value = mock_instance
            
            passed, missing = check_directories()
            assert passed is True
            assert len(missing) == 0

class TestCheckFiles:
    def test_missing_file(self, monkeypatch):
        """Test detection of a missing file."""
        with patch('analysis.quickstart_validator.Path') as MockPath:
            mock_instance = MagicMock()
            mock_instance.exists.return_value = False
            MockPath.return_value = mock_instance
            
            passed, missing = check_files()
            assert passed is False
            assert len(missing) > 0

class TestValidateJsonSchema:
    def test_valid_list_schema(self, tmp_path):
        """Test validation of a valid list schema."""
        data = [
            {"id": 1, "name": "test"},
            {"id": 2, "name": "test2"}
        ]
        schema = {
            "type": "list",
            "required_fields": ["id", "name"]
        }
        
        file_path = tmp_path / "test.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        passed, msg = validate_json_schema(str(file_path), schema)
        assert passed is True

    def test_missing_fields_in_list(self, tmp_path):
        """Test validation failure when required fields are missing."""
        data = [{"id": 1}] # Missing 'name'
        schema = {
            "type": "list",
            "required_fields": ["id", "name"]
        }
        
        file_path = tmp_path / "test.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        passed, msg = validate_json_schema(str(file_path), schema)
        assert passed is False
        assert "name" in msg

    def test_invalid_json(self, tmp_path):
        """Test validation failure on invalid JSON."""
        file_path = tmp_path / "invalid.json"
        with open(file_path, 'w') as f:
            f.write("{ invalid json }")
        
        passed, msg = validate_json_schema(str(file_path), {"type": "list"})
        assert passed is False
        assert "Invalid JSON" in msg

    def test_empty_list(self, tmp_path):
        """Test validation failure on empty list."""
        data = []
        schema = {
            "type": "list",
            "required_fields": ["id"]
        }
        
        file_path = tmp_path / "empty.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        passed, msg = validate_json_schema(str(file_path), schema)
        assert passed is False
        assert "empty" in msg

class TestCheckDataArtifacts:
    def test_schema_validation_passes(self, tmp_path, monkeypatch):
        """Test successful validation of data artifacts."""
        # Create temporary files with valid content
        valid_data = [
            {"trajectory_id": "1", "condition": "Adapter", "injected_state": "de-escalate", "confidence_score": 0.9}
        ]
        
        # Mock the file paths to point to our temp files
        original_checks = SCHEMA_CHECKS.copy()
        
        # We need to mock the file reading to return our valid data
        # Since check_data_artifacts uses hardcoded paths, we patch validate_json_schema
        with patch('analysis.quickstart_validator.validate_json_schema', return_value=(True, "OK")):
            passed, errors = check_data_artifacts()
            assert passed is True
            assert len(errors) == 0

    def test_schema_validation_fails(self, tmp_path, monkeypatch):
        """Test failure when schema validation fails."""
        with patch('analysis.quickstart_validator.validate_json_schema', return_value=(False, "Error")):
            passed, errors = check_data_artifacts()
            assert passed is False
            assert len(errors) > 0

class TestCheckImports:
    def test_import_failure(self, monkeypatch):
        """Test detection of import failure."""
        with patch('analysis.quickstart_validator.__import__', side_effect=ImportError("Module not found")):
            passed, errors = check_imports()
            assert passed is False
            assert len(errors) > 0

class TestRunStatisticalDryRun:
    def test_dry_run_success(self, monkeypatch):
        """Test successful dry run of statistical module."""
        # Mock the import and callable check
        mock_main = MagicMock()
        mock_main.return_value = None
        
        with patch.dict('sys.modules', {'analysis.stats': MagicMock(generate_statistical_report=MagicMock(), main=mock_main)}):
            passed, msg = run_statistical_dry_run()
            assert passed is True
            assert "ready" in msg.lower()

    def test_dry_run_failure(self, monkeypatch):
        """Test failure when statistical module cannot be imported."""
        with patch.dict('sys.modules', {'analysis.stats': None}):
            passed, msg = run_statistical_dry_run()
            assert passed is False
            assert "failed" in msg.lower()
