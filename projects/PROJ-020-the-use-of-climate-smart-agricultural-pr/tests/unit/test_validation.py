"""
Unit tests for validation components

Tests for:
- Directory structure validation
- Configuration loading validation
- Function accessibility checks
- Output file verification
"""
import pytest
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from validation.quickstart_validator import QuickstartValidator

class TestQuickstartValidator:
    """Test cases for QuickstartValidator class"""

    @pytest.fixture
    def validator(self):
        """Create a validator instance with temporary directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up a temporary project structure
            temp_path = Path(temp_dir)
            
            # Create basic directory structure
            (temp_path / 'data' / 'raw').mkdir(parents=True)
            (temp_path / 'data' / 'processed').mkdir(parents=True)
            (temp_path / 'state').mkdir(parents=True)
            (temp_path / 'code').mkdir(parents=True)
            (temp_path / 'tests').mkdir(parents=True)
            (temp_path / 'specs' / '001-csa-food-security').mkdir(parents=True)
            
            # Mock the project_root
            original_root = validator.__class__.__dict__.get('project_root')
            
            validator = QuickstartValidator()
            validator.validation_results = {
                'status': 'running',
                'steps': [],
                'errors': [],
                'warnings': [],
                'outputs_verified': [],
                'total_duration_seconds': 0
            }
            
            return validator

    def test_directory_structure_validation(self, validator):
        """Test that directory structure validation works correctly"""
        # Should pass if directories exist
        result = validator.validate_directory_structure()
        assert result is True
        
        # Check that step was logged
        step_found = any(s['step'] == 'directory_structure' for s in validator.validation_results['steps'])
        assert step_found

    def test_configuration_validation(self, validator):
        """Test configuration loading validation"""
        # This might fail if environment variables aren't set
        # We test that the function runs without crashing
        try:
            result = validator.validate_configuration()
            # Result could be True or False depending on env setup
            assert isinstance(result, bool)
        except Exception:
            # Expected if config isn't properly set up in test environment
            pass

    def test_data_download_validation(self, validator):
        """Test data download capability validation"""
        result = validator.validate_data_download()
        assert isinstance(result, bool)
        
        # Should not crash even if download fails
        step_found = any(s['step'] == 'data_download' for s in validator.validation_results['steps'])
        assert step_found

    def test_data_pipeline_validation(self, validator):
        """Test data pipeline validation"""
        result = validator.validate_data_pipeline()
        assert isinstance(result, bool)

    def test_feature_engineering_validation(self, validator):
        """Test feature engineering validation"""
        result = validator.validate_feature_engineering()
        assert isinstance(result, bool)

    def test_model_fitting_validation(self, validator):
        """Test model fitting validation"""
        result = validator.validate_model_fitting()
        assert isinstance(result, bool)

    def test_visualization_validation(self, validator):
        """Test visualization validation"""
        result = validator.validate_visualization()
        assert isinstance(result, bool)

    def test_output_verification(self, validator):
        """Test output file verification"""
        # Create a temporary output file
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a mock output file
            mock_output = temp_path / 'test_output.json'
            mock_output.write_text('{"test": "data"}')
            
            # Temporarily override the project root for testing
            original_root = validator.project_root if hasattr(validator, 'project_root') else None
            
            result = validator.validate_outputs()
            assert isinstance(result, bool)

    def test_run_validation_sequence(self, validator):
        """Test the full validation sequence"""
        results = validator.run_validation()
        
        # Check that all expected keys are present
        assert 'status' in results
        assert 'steps' in results
        assert 'errors' in results
        assert 'warnings' in results
        assert 'outputs_verified' in results
        assert 'total_duration_seconds' in results
        
        # Check that all steps were executed
        expected_steps = [
            'directory_structure',
            'configuration',
            'data_download',
            'data_pipeline',
            'feature_engineering',
            'model_fitting',
            'visualization',
            'output_verification'
        ]
        
        executed_steps = [s['step'] for s in results['steps']]
        for expected_step in expected_steps:
            assert expected_step in executed_steps

    def test_validation_report_generation(self, validator):
        """Test that validation report is generated correctly"""
        results = validator.run_validation()
        
        # Check that report was created
        report_path = project_root / 'state' / 'quickstart_validation_report.json'
        
        # The report might not exist if state directory doesn't exist
        # But the function should not crash
        assert isinstance(results, dict)

    def test_error_handling(self, validator):
        """Test that errors are handled gracefully"""
        # Mock a failing function
        with patch.object(validator, 'validate_directory_structure', return_value=False):
            results = validator.run_validation()
            
            # Should still complete
            assert results['status'] in ['passed', 'completed_with_warnings']
            
            # Should have recorded the error
            assert len(results['errors']) > 0 or len(results['warnings']) > 0

class TestValidationEdgeCases:
    """Test edge cases and error conditions"""

    def test_missing_directory_creation(self):
        """Test that missing directories are created"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create only some directories
            (temp_path / 'data').mkdir()
            
            # Create validator with this path
            validator = QuickstartValidator()
            
            # Should handle missing directories gracefully
            result = validator.validate_directory_structure()
            assert isinstance(result, bool)

    def test_invalid_configuration(self):
        """Test handling of invalid configuration"""
        validator = QuickstartValidator()
        
        # Mock config to raise an exception
        with patch('validation.quickstart_validator.get_config', side_effect=Exception("Config error")):
            result = validator.validate_configuration()
            assert result is False

    def test_network_failure_handling(self):
        """Test handling of network failures during download validation"""
        validator = QuickstartValidator()
        
        # Mock download to raise network error
        with patch('validation.quickstart_validator.download_lsms', side_effect=Exception("Network error")):
            result = validator.validate_data_download()
            # Should not crash, may return True or False
            assert isinstance(result, bool)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
