"""
Integration test for Runtime Validation (T037).
Verifies that the runtime validation script produces the expected output file
and that the JSON structure is correct.
"""
import os
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from runtime_validation import execute_pipeline_with_timing, write_validation_report

def test_write_validation_report_structure():
    """
    Test that the validation report is written with correct structure.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        outputs_dir = Path(tmpdir) / "data" / "outputs"
        outputs_dir.mkdir(parents=True)
        
        # Mock the get_logger and ensure_directories to avoid side effects
        with patch('runtime_validation.ensure_directories'):
            with patch('runtime_validation.project_root', Path(tmpdir)):
                report_path = write_validation_report(123.45, True)
                
                assert report_path.exists(), "Report file should exist"
                
                with open(report_path, 'r') as f:
                    data = json.load(f)
                
                assert "total_seconds" in data, "Missing total_seconds key"
                assert "passed" in data, "Missing passed key"
                assert isinstance(data["total_seconds"], (int, float)), "total_seconds should be numeric"
                assert isinstance(data["passed"], bool), "passed should be boolean"
                assert data["passed"] is True, "Passed flag should match input"
                assert data["total_seconds"] == 123.45, "Total seconds should match input"

def test_execute_pipeline_with_timing_logic():
    """
    Test the timing logic with a mock subprocess.
    """
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        with patch('time.time', side_effect=[0, 100]):  # Start 0, End 100
            total_seconds, passed = execute_pipeline_with_timing()
            
            assert total_seconds == 100, "Time calculation should be correct"
            assert passed is True, "Should pass if returncode is 0"
            mock_run.assert_called_once()

def test_execute_pipeline_with_timing_failure():
    """
    Test the timing logic when pipeline fails.
    """
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Error occurred"
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        with patch('time.time', side_effect=[0, 50]):
            total_seconds, passed = execute_pipeline_with_timing()
            
            assert total_seconds == 50, "Time calculation should be correct"
            assert passed is False, "Should fail if returncode is not 0"
            mock_run.assert_called_once()