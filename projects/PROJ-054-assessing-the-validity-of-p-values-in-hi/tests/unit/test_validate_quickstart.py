"""
Unit tests for the quickstart validation script.
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from validate_quickstart import check_directories, check_artifacts, run_pipeline_validation

class TestCheckDirectories:
    """Tests for the check_directories function."""
    
    def test_all_directories_exist(self, tmp_path):
        """Test that the function returns True when all directories exist."""
        # Create required directories
        required_dirs = [
            'code', 'code/utils', 'data', 'data/raw', 'data/synthetic', 
            'data/results', 'data/sweep', 'tests', 'tests/unit', 
            'tests/integration', 'docs', 'docs/plots', 'specs'
        ]
        
        for dir_path in required_dirs:
            (tmp_path / dir_path).mkdir(parents=True)
        
        # Mock the base path
        with patch('validate_quickstart.Path') as mock_path:
            mock_path.return_value.__truediv__.return_value.exists.return_value = True
            mock_path.return_value.__truediv__.return_value.is_dir.return_value = True
            
            result = check_directories()
            assert result is True
    
    def test_missing_directory(self, tmp_path):
        """Test that the function returns False when a directory is missing."""
        # Mock the base path to simulate missing directory
        with patch('validate_quickstart.Path') as mock_path:
            mock_path.return_value.__truediv__.return_value.exists.return_value = False
            
            result = check_directories()
            assert result is False

class TestCheckArtifacts:
    """Tests for the check_artifacts function."""
    
    def test_all_artifacts_exist(self, tmp_path):
        """Test that the function returns True when all artifacts exist."""
        # Create required artifacts
        required_artifacts = [
            'requirements.txt',
            'code/.ruff.toml',
            'code/.black',
            'code/utils/exceptions.py',
            'code/utils/regularization.py'
        ]
        
        for artifact in required_artifacts:
            file_path = tmp_path / artifact
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("dummy content")
        
        # Mock the base path
        with patch('validate_quickstart.Path') as mock_path:
            mock_path.return_value.__truediv__.return_value.exists.return_value = True
            mock_path.return_value.__truediv__.return_value.stat.return_value.st_size = 100
            
            result = check_artifacts()
            assert result is True
    
    def test_empty_artifact(self, tmp_path):
        """Test that the function returns False when an artifact is empty."""
        # Mock the base path to simulate empty file
        with patch('validate_quickstart.Path') as mock_path:
            mock_path.return_value.__truediv__.return_value.exists.return_value = True
            mock_path.return_value.__truediv__.return_value.stat.return_value.st_size = 0
            
            result = check_artifacts()
            assert result is False

class TestRunPipelineValidation:
    """Tests for the run_pipeline_validation function."""
    
    def test_successful_validation(self, tmp_path):
        """Test that the function returns success when validation passes."""
        # Mock all dependencies
        with patch('validate_quickstart.check_directories') as mock_dirs, \
             patch('validate_quickstart.check_artifacts') as mock_artifacts, \
             patch('validate_quickstart.subprocess.run') as mock_subprocess, \
             patch('validate_quickstart.Path') as mock_path:
            
            mock_dirs.return_value = True
            mock_artifacts.return_value = True
            mock_subprocess.return_value.returncode = 0
            mock_path.return_value.__truediv__.return_value.exists.return_value = True
            
            result = run_pipeline_validation()
            
            assert result['directories_check'] is True
            assert result['artifacts_check'] is True
            assert result['pipeline_execution'] is True
            assert len(result['errors']) == 0
    
    def test_failed_validation(self, tmp_path):
        """Test that the function returns failure when validation fails."""
        # Mock all dependencies
        with patch('validate_quickstart.check_directories') as mock_dirs, \
             patch('validate_quickstart.check_artifacts') as mock_artifacts, \
             patch('validate_quickstart.subprocess.run') as mock_subprocess, \
             patch('validate_quickstart.Path') as mock_path:
            
            mock_dirs.return_value = False
            mock_artifacts.return_value = True
            mock_subprocess.return_value.returncode = 1
            mock_path.return_value.__truediv__.return_value.exists.return_value = True
            
            result = run_pipeline_validation()
            
            assert result['directories_check'] is False
            assert result['artifacts_check'] is True
            assert result['pipeline_execution'] is False
            assert len(result['errors']) > 0

class TestIntegration:
    """Integration tests for the validation script."""
    
    def test_full_validation_flow(self, tmp_path):
        """Test the complete validation flow."""
        # Create a minimal project structure
        required_dirs = [
            'code', 'code/utils', 'data', 'data/raw', 'data/synthetic', 
            'data/results', 'data/sweep', 'tests', 'tests/unit', 
            'tests/integration', 'docs', 'docs/plots', 'specs'
        ]
        
        for dir_path in required_dirs:
            (tmp_path / dir_path).mkdir(parents=True)
        
        # Create required artifacts
        required_artifacts = [
            ('requirements.txt', 'numpy\nscipy\n'),
            ('code/.ruff.toml', '[tool.ruff]\n'),
            ('code/.black', '[tool.black]\n'),
            ('code/utils/exceptions.py', 'class TestException(Exception):\n    pass\n'),
            ('code/utils/regularization.py', 'def test_func():\n    pass\n'),
            ('data/sweep/power_analysis_result.json', '{"required_iterations": 100}\n'),
            ('data/sweep/seed_map.json', '{"seeds": [1, 2, 3]}\n')
        ]
        
        for artifact, content in required_artifacts:
            file_path = tmp_path / artifact
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        
        # Change to temp directory and run validation
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the validation
            results = run_pipeline_validation()
            
            # Verify results
            assert results['directories_check'] is True
            assert results['artifacts_check'] is True
            
        finally:
            os.chdir(original_cwd)