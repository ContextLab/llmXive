import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from pre_ingestion_validation_gate import load_json_log, check_file_exists, run_validation_gate

class TestPreIngestionValidationGate:
    @pytest.fixture
    def temp_project_root(self, tmp_path):
        """Create a temporary project structure for testing."""
        # Create necessary directories
        (tmp_path / "results" / "logs").mkdir(parents=True)
        (tmp_path / "data" / "raw").mkdir(parents=True)
        return tmp_path

    def test_load_json_log_existing(self, temp_project_root):
        """Test loading an existing JSON log file."""
        log_path = temp_project_root / "results" / "logs" / "test.json"
        log_path.write_text('{"status": "pass", "details": "ok"}')
        
        result = load_json_log(log_path)
        assert result == {"status": "pass", "details": "ok"}

    def test_load_json_log_missing(self, temp_project_root):
        """Test loading a missing JSON log file."""
        log_path = temp_project_root / "results" / "logs" / "missing.json"
        
        result = load_json_log(log_path)
        assert result == {}

    def test_load_json_log_invalid_json(self, temp_project_root):
        """Test loading a JSON log file with invalid JSON."""
        log_path = temp_project_root / "results" / "logs" / "invalid.json"
        log_path.write_text('not valid json {')
        
        result = load_json_log(log_path)
        assert result == {}

    def test_check_file_exists_true(self, temp_project_root):
        """Test check_file_exists when file exists."""
        file_path = temp_project_root / "data" / "raw" / "test.h5"
        file_path.write_text("dummy content")
        
        assert check_file_exists(file_path) is True

    def test_check_file_exists_false(self, temp_project_root):
        """Test check_file_exists when file does not exist."""
        file_path = temp_project_root / "data" / "raw" / "missing.h5"
        
        assert check_file_exists(file_path) is False

    @patch('pre_ingestion_validation_gate.logging')
    def test_run_validation_gate_all_pass(self, mock_logging, temp_project_root):
        """Test run_validation_gate when all checks pass."""
        # Setup log file content
        log_content = """
        2026-01-01T00:00:00 - Task T001: Status: Pass
        2026-01-01T00:00:01 - Task T001c: Status: Pass
        2026-01-01T00:00:02 - Task T004: Status: Pass
        """
        log_path = temp_project_root / "results" / "logs" / "data_validation_log.txt"
        log_path.write_text(log_content)
        
        # Setup ERA5 full file
        era5_full_path = temp_project_root / "data" / "raw" / "era5_full.h5"
        era5_full_path.write_text("dummy era5 data")
        
        # Mock the logger to avoid actual logging side effects in tests
        mock_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_logger
        
        result = run_validation_gate(temp_project_root)
        
        assert result is True
        mock_logger.info.assert_any_call("Pre-Ingestion Validation Gate: PASSED")

    @patch('pre_ingestion_validation_gate.logging')
    def test_run_validation_gate_log_missing(self, mock_logging, temp_project_root):
        """Test run_validation_gate when validation log is missing."""
        # Do not create the log file
        
        mock_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_logger
        
        with pytest.raises(RuntimeError, match="Pre-Ingestion Validation Gate Failed"):
            run_validation_gate(temp_project_root)
        
        mock_logger.error.assert_any_call("Validation log file not found: %s", temp_project_root / "results" / "logs" / "data_validation_log.txt")

    @patch('pre_ingestion_validation_gate.logging')
    def test_run_validation_gate_era5_missing(self, mock_logging, temp_project_root):
        """Test run_validation_gate when ERA5 full file is missing."""
        # Setup log file content
        log_content = """
        2026-01-01T00:00:00 - Task T001: Status: Pass
        2026-01-01T00:00:01 - Task T001c: Status: Pass
        2026-01-01T00:00:02 - Task T004: Status: Pass
        """
        log_path = temp_project_root / "results" / "logs" / "data_validation_log.txt"
        log_path.write_text(log_content)
        
        # Do not create ERA5 full file
        
        mock_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_logger
        
        with pytest.raises(RuntimeError, match="Pre-Ingestion Validation Gate Failed"):
            run_validation_gate(temp_project_root)
        
        mock_logger.error.assert_any_call("T002c: ERA5 Full Fetch file not found: %s", temp_project_root / "data" / "raw" / "era5_full.h5")

    @patch('pre_ingestion_validation_gate.logging')
    def test_run_validation_gate_t001_fail(self, mock_logging, temp_project_root):
        """Test run_validation_gate when T001 fails (no Pass in log)."""
        # Setup log file content without T001 Pass
        log_content = """
        2026-01-01T00:00:00 - Task T001c: Status: Pass
        2026-01-01T00:00:01 - Task T004: Status: Pass
        """
        log_path = temp_project_root / "results" / "logs" / "data_validation_log.txt"
        log_path.write_text(log_content)
        
        # Setup ERA5 full file
        era5_full_path = temp_project_root / "data" / "raw" / "era5_full.h5"
        era5_full_path.write_text("dummy era5 data")
        
        mock_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_logger
        
        with pytest.raises(RuntimeError, match="Pre-Ingestion Validation Gate Failed"):
            run_validation_gate(temp_project_root)
        
        mock_logger.warning.assert_any_call("T001: Could not confirm PASS status in log.")