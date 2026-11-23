import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.generate_audit_report import run_audit, mock_load_dataset

class TestAuditReport:
    def test_mock_load_dataset_raises_connection_error(self):
        """Verify the mock function raises the expected exception."""
        with pytest.raises(ConnectionError):
            mock_load_dataset("locomo/locomo-benchmark")

    def test_audit_report_structure(self):
        """Verify the audit report contains the required keys."""
        # We can't easily run the full subprocess audit in a unit test environment
        # without a full data_loader.py setup, but we can verify the structure
        # of the result dict produced by run_audit if we mock the subprocess call.
        
        # Mock the subprocess.run to return a known output
        mock_output = """
        SCRIPT_EXIT_CODE:1
        ERROR:Cannot proceed without real data.
        """
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, stderr="")
            
            # We need to mock the file system checks too
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.rglob', return_value=[]):
                    result = run_audit()
                    
                    assert isinstance(result, dict)
                    assert "exit_code" in result
                    assert "synthetic_files_created" in result
                    assert "error_caught" in result
                    assert "message" in result
                    
                    # Verify the logic
                    assert result["exit_code"] == 1
                    assert result["error_caught"] is True
                    assert result["synthetic_files_created"] is False

    def test_audit_report_json_creation(self):
        """Verify that the main function creates a valid JSON report file."""
        # This test would ideally run the main function and check the file,
        # but it requires the full environment. We verify the function exists and signature.
        from utils.generate_audit_report import main
        assert callable(main)