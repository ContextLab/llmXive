"""
Unit tests for the Pre-Ingestion Validation Gate (T006)
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
# We need to adjust the path to import from code/
import sys
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from pre_ingestion_validation_gate import load_json_log, check_file_exists, run_validation_gate

class TestPreIngestionValidationGate:

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory structure for testing."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir)
        
        # Create required directories
        (project_root / "data" / "raw").mkdir(parents=True)
        (project_root / "results" / "logs").mkdir(parents=True)
        
        yield project_root
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_load_json_log_success(self, temp_project_root):
        """Test loading a valid JSON log file."""
        log_path = temp_project_root / "results" / "logs" / "test.json"
        test_data = {"status": "Pass", "reason": "OK"}
        with open(log_path, 'w') as f:
            json.dump(test_data, f)
        
        result = load_json_log(log_path)
        assert result["status"] == "Pass"

    def test_load_json_log_missing_file(self, temp_project_root):
        """Test loading a missing JSON log file raises FileNotFoundError."""
        log_path = temp_project_root / "results" / "logs" / "missing.json"
        with pytest.raises(FileNotFoundError):
            load_json_log(log_path)

    def test_check_file_exists_true(self, temp_project_root):
        """Test check_file_exists returns True for existing file."""
        file_path = temp_project_root / "data" / "raw" / "test.h5"
        file_path.touch()
        assert check_file_exists(file_path) is True

    def test_check_file_exists_false(self, temp_project_root):
        """Test check_file_exists returns False for missing file."""
        file_path = temp_project_root / "data" / "raw" / "missing.h5"
        assert check_file_exists(file_path) is False

    @patch('pre_ingestion_validation_gate.setup_logging')
    @patch('pre_ingestion_validation_gate.get_data_quality_logger')
    def test_gate_passes_all_checks(self, mock_data_logger, mock_setup_logging, temp_project_root):
        """Test that the gate passes when all validations are successful."""
        logs_dir = temp_project_root / "results" / "logs"
        data_dir = temp_project_root / "data" / "raw"

        # Create all required log files with "Pass" status
        logs = [
            ("moral_machine_validation.json", {"status": "Pass"}),
            ("era5_metadata_validation.json", {"status": "Pass"}),
            ("era5_sample_resolution_validation.json", {"status": "Pass"}),
            ("moral_machine_source_verify.json", {"status": "Pass"})
        ]
        for filename, content in logs:
            with open(logs_dir / filename, 'w') as f:
                json.dump(content, f)

        # Create the ERA5 full file
        (data_dir / "era5_full.h5").touch()

        # Mock the logger to avoid actual logging side effects
        mock_logger_instance = MagicMock()
        mock_setup_logging.return_value = mock_logger_instance
        mock_data_logger.return_value = mock_logger_instance

        # Run the gate
        result = run_validation_gate()
        assert result is True

    @patch('pre_ingestion_validation_gate.setup_logging')
    @patch('pre_ingestion_validation_gate.get_data_quality_logger')
    def test_gate_fails_missing_era5_file(self, mock_data_logger, mock_setup_logging, temp_project_root):
        """Test that the gate fails if ERA5 full file is missing."""
        logs_dir = temp_project_root / "results" / "logs"

        # Create all required log files
        logs = [
            ("moral_machine_validation.json", {"status": "Pass"}),
            ("era5_metadata_validation.json", {"status": "Pass"}),
            ("era5_sample_resolution_validation.json", {"status": "Pass"}),
            ("moral_machine_source_verify.json", {"status": "Pass"})
        ]
        for filename, content in logs:
            with open(logs_dir / filename, 'w') as f:
                json.dump(content, f)

        # Do NOT create the ERA5 full file

        mock_logger_instance = MagicMock()
        mock_setup_logging.return_value = mock_logger_instance
        mock_data_logger.return_value = mock_logger_instance

        # Expect an exception to be raised
        with pytest.raises(RuntimeError) as exc_info:
            run_validation_gate()
        
        assert "T002c" in str(exc_info.value)

    @patch('pre_ingestion_validation_gate.setup_logging')
    @patch('pre_ingestion_validation_gate.get_data_quality_logger')
    def test_gate_fails_moral_machine_validation_fail(self, mock_data_logger, mock_setup_logging, temp_project_root):
        """Test that the gate fails if Moral Machine validation fails."""
        logs_dir = temp_project_root / "results" / "logs"
        data_dir = temp_project_root / "data" / "raw"

        # Create log files, one with "Fail" status
        logs = [
            ("moral_machine_validation.json", {"status": "Fail", "reason": "Schema mismatch"}),
            ("era5_metadata_validation.json", {"status": "Pass"}),
            ("era5_sample_resolution_validation.json", {"status": "Pass"}),
            ("moral_machine_source_verify.json", {"status": "Pass"})
        ]
        for filename, content in logs:
            with open(logs_dir / filename, 'w') as f:
                json.dump(content, f)

        # Create the ERA5 full file
        (data_dir / "era5_full.h5").touch()

        mock_logger_instance = MagicMock()
        mock_setup_logging.return_value = mock_logger_instance
        mock_data_logger.return_value = mock_logger_instance

        with pytest.raises(RuntimeError) as exc_info:
            run_validation_gate()
        
        assert "T001a" in str(exc_info.value)