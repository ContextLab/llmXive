"""
Tests for Task T043c: Execute Evaluation.

This module contains tests to verify that the evaluation execution script
runs correctly and produces the required artifacts.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Mock the evaluation modules to avoid heavy dependencies in unit tests
from unittest.mock import patch, MagicMock

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    project_root = Path(temp_dir)
    
    # Create necessary directories
    (project_root / "data").mkdir()
    (project_root / "docs").mkdir()
    (project_root / "code").mkdir()
    
    yield project_root
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_run_evaluation_step_success(temp_project_dir):
    """Test that run_evaluation_step creates the evaluation log on success."""
    from code.validation.execute_evaluation import run_evaluation_step
    
    # Mock the metrics and report modules
    with patch('code.validation.execute_evaluation.run_metrics') as mock_metrics, \
         patch('code.validation.execute_evaluation.run_report') as mock_report:
        
        mock_metrics.return_value = None
        mock_report.return_value = None
        
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(str(temp_project_dir))
        
        try:
            run_evaluation_step()
            
            # Verify log file was created
            log_path = temp_project_dir / "data" / "evaluation_log.json"
            assert log_path.exists(), "evaluation_log.json was not created"
            
            # Verify log content
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data['status'] == 'SUCCESS'
            assert 'runtime_seconds' in log_data
            assert 'artifacts_created' in log_data
            assert len(log_data['artifacts_created']) > 0
            
        finally:
            os.chdir(original_cwd)

def test_run_evaluation_step_failure(temp_project_dir):
    """Test that run_evaluation_step handles exceptions and logs failure."""
    from code.validation.execute_evaluation import run_evaluation_step
    
    # Mock metrics to raise an exception
    with patch('code.validation.execute_evaluation.run_metrics') as mock_metrics:
        mock_metrics.side_effect = Exception("Test failure")
        
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(str(temp_project_dir))
        
        try:
            with pytest.raises(Exception):
                run_evaluation_step()
            
            # Verify log file was created even on failure
            log_path = temp_project_dir / "data" / "evaluation_log.json"
            assert log_path.exists(), "evaluation_log.json was not created on failure"
            
            # Verify log content
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data['status'] == 'FAILED'
            assert log_data['error_message'] == "Test failure"
            
        finally:
            os.chdir(original_cwd)

def test_main_returns_zero_on_success(temp_project_dir):
    """Test that main() returns 0 on success."""
    from code.validation.execute_evaluation import main
    
    with patch('code.validation.execute_evaluation.run_evaluation_step') as mock_step:
        mock_step.return_value = None
        
        original_cwd = os.getcwd()
        os.chdir(str(temp_project_dir))
        
        try:
            result = main()
            assert result == 0
        finally:
            os.chdir(original_cwd)

def test_main_returns_one_on_failure(temp_project_dir):
    """Test that main() returns 1 on failure."""
    from code.validation.execute_evaluation import main
    
    with patch('code.validation.execute_evaluation.run_evaluation_step') as mock_step:
        mock_step.side_effect = Exception("Fatal error")
        
        original_cwd = os.getcwd()
        os.chdir(str(temp_project_dir))
        
        try:
            result = main()
            assert result == 1
        finally:
            os.chdir(original_cwd)