"""
Unit tests for the pipeline profiling module (T041).

Tests verify that:
1. The profile report is generated correctly
2. The report contains expected sections
3. The profiling function handles errors gracefully
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest
import argparse
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / 'code'
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.profile_pipeline import profile_function, run_pipeline_profiling


class TestProfileFunction:
    """Tests for the profile_function helper."""
    
    def test_profile_successful_function(self):
        """Test profiling a function that runs successfully."""
        def dummy_func(x, y):
            return x + y
        
        result = profile_function(dummy_func, args=(2, 3), kwargs={}, func_name="test_add")
        
        assert result['function'] == "test_add"
        assert result['success'] is True
        assert result['stats_text'] is not None
        assert len(result['stats_text']) > 0
        assert 'dummy_func' in result['stats_text']
    
    def test_profile_function_with_error(self):
        """Test profiling a function that raises an exception."""
        def failing_func():
            raise ValueError("Intentional error for testing")
        
        result = profile_function(failing_func, func_name="test_fail")
        
        assert result['function'] == "test_fail"
        assert result['success'] is False
        assert result['error'] is not None
        assert 'Intentional error' in result['error']
        assert result['stats_text'] is not None
    
    def test_profile_function_empty_args(self):
        """Test profiling with no arguments."""
        def no_args_func():
            return 42
        
        result = profile_function(no_args_func, func_name="test_no_args")
        
        assert result['success'] is True
        assert result['stats_text'] is not None


class TestRunPipelineProfiling:
    """Tests for the main profiling function."""
    
    def test_report_generation(self):
        """Test that the report file is generated with correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_profile_report.txt"
            
            # Mock the component functions to avoid dependency on actual data
            with patch('utils.profile_pipeline.profile_function') as mock_profile:
                mock_profile.return_value = {
                    'function': 'Mocked Function',
                    'success': True,
                    'stats_text': 'Mocked stats output',
                    'error': None
                }
                
                results = run_pipeline_profiling(output_path)
                
                # Verify file was created
                assert output_path.exists()
                
                # Verify content structure
                with open(output_path, 'r') as f:
                    content = f.read()
                
                assert "GWAS PIPELINE PROFILE REPORT" in content
                assert "Generated:" in content
                assert "PROFILING:" in content
                assert "PROFILE SUMMARY" in content
                assert "END OF REPORT" in content
                
                # Verify mocked content
                assert "Mocked Function" in content
                assert "Mocked stats output" in content
    
    def test_report_directory_creation(self):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "new_subdir" / "profile_report.txt"
            
            with patch('utils.profile_pipeline.profile_function') as mock_profile:
                mock_profile.return_value = {
                    'function': 'Test',
                    'success': True,
                    'stats_text': 'Stats',
                    'error': None
                }
                
                run_pipeline_profiling(output_path)
                
                assert output_path.exists()
                assert output_path.parent.exists()
    
    def test_report_with_failed_components(self):
        """Test report generation when some components fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "profile_report.txt"
            
            call_count = [0]
            
            def mock_profile_func(func, args=None, kwargs=None, func_name="unknown"):
                call_count[0] += 1
                if call_count[0] == 1:
                    return {
                        'function': func_name,
                        'success': True,
                        'stats_text': 'Success stats',
                        'error': None
                    }
                else:
                    return {
                        'function': func_name,
                        'success': False,
                        'stats_text': 'Error stats',
                        'error': 'Component failed'
                    }
            
            with patch('utils.profile_pipeline.profile_function', side_effect=mock_profile_func):
                results = run_pipeline_profiling(output_path)
                
                with open(output_path, 'r') as f:
                    content = f.read()
                
                assert "Successful: 1" in content
                assert "Failed: 5" in content  # 6 total, 1 successful