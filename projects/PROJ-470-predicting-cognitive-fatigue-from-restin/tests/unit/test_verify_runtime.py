"""
Tests for code/verify_runtime.py
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.verify_runtime import load_resource_usage, verify_runtime, main
from code.utils.logging import get_logger

class TestLoadResourceUsage:
    def test_load_valid_file(self, tmp_path):
        """Test loading a valid resource usage file."""
        test_data = {"total_runtime_hours": 2.5, "peak_rss_gb": 4.0}
        test_file = tmp_path / "resource_usage.json"
        test_file.write_text(json.dumps(test_data))
        
        result = load_resource_usage(str(test_file))
        assert result == test_data
        assert result["total_runtime_hours"] == 2.5

    def test_load_missing_file(self):
        """Test loading a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_resource_usage("/nonexistent/path/file.json")

    def test_load_invalid_json(self, tmp_path):
        """Test loading a file with invalid JSON raises error."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            load_resource_usage(str(test_file))

class TestVerifyRuntime:
    def test_runtime_within_limit(self):
        """Test verification passes when runtime is within limit."""
        data = {"total_runtime_hours": 5.0}
        logger = get_logger("test")
        assert verify_runtime(data, 6.0, logger) is True

    def test_runtime_exceeds_limit(self):
        """Test verification fails when runtime exceeds limit."""
        data = {"total_runtime_hours": 7.5}
        logger = get_logger("test")
        assert verify_runtime(data, 6.0, logger) is False

    def test_runtime_exactly_limit(self):
        """Test verification passes when runtime equals limit."""
        data = {"total_runtime_hours": 6.0}
        logger = get_logger("test")
        assert verify_runtime(data, 6.0, logger) is True

    def test_missing_runtime_field(self):
        """Test verification fails when runtime field is missing."""
        data = {"peak_rss_gb": 4.0}
        logger = get_logger("test")
        assert verify_runtime(data, 6.0, logger) is False

class TestMainIntegration:
    @patch('code.verify_runtime.load_resource_usage')
    @patch('code.verify_runtime.verify_runtime')
    @patch('code.verify_runtime.sys.exit')
    def test_main_success(self, mock_exit, mock_verify, mock_load):
        """Test main function on successful verification."""
        mock_load.return_value = {"total_runtime_hours": 3.0}
        mock_verify.return_value = True
        
        with patch('sys.argv', ['verify_runtime.py']):
            main()
        
        mock_exit.assert_called_once_with(0)

    @patch('code.verify_runtime.load_resource_usage')
    @patch('code.verify_runtime.verify_runtime')
    @patch('code.verify_runtime.sys.exit')
    def test_main_failure(self, mock_exit, mock_verify, mock_load):
        """Test main function on failed verification."""
        mock_load.return_value = {"total_runtime_hours": 8.0}
        mock_verify.return_value = False
        
        with patch('sys.argv', ['verify_runtime.py']):
            main()
        
        mock_exit.assert_called_once_with(1)

    @patch('code.verify_runtime.load_resource_usage')
    @patch('code.verify_runtime.sys.exit')
    def test_main_file_not_found(self, mock_exit, mock_load):
        """Test main function when file is not found."""
        mock_load.side_effect = FileNotFoundError("File not found")
        
        with patch('sys.argv', ['verify_runtime.py']):
            main()
        
        mock_exit.assert_called_once_with(1)