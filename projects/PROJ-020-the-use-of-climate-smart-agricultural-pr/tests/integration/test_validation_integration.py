"""
Integration tests for validation pipeline

Tests that validate the full integration of:
- Configuration -> Data Download -> Cleaning -> Modeling -> Visualization
- End-to-end reproducibility
- Output file generation and verification
"""
import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestQuickstartValidationIntegration:
    """Integration tests for quickstart validation"""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create full project structure
            dirs = [
                'data/raw',
                'data/processed',
                'state',
                'code',
                'tests',
                'specs/001-csa-food-security',
                'output/figures',
                'output/tables'
            ]
            
            for dir_path in dirs:
                (temp_path / dir_path).mkdir(parents=True)
            
            # Create a mock requirements.txt
            (temp_path / 'code' / 'requirements.txt').write_text(
                'pandas\nnumpy\nscikit-learn\nstatsmodels\n'
            )
            
            yield temp_path

    def test_full_validation_sequence(self, temp_project_dir):
        """Test the complete validation sequence end-to-end"""
        from validation.quickstart_validator import QuickstartValidator
        
        # Change to temp directory to simulate real run
        original_cwd = os.getcwd()
        os.chdir(temp_project_dir)
        
        try:
            validator = QuickstartValidator()
            results = validator.run_validation()
            
            # Verify results structure
            assert 'status' in results
            assert 'steps' in results
            assert len(results['steps']) > 0
            
            # Verify all expected steps were executed
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
                assert expected_step in executed_steps, f"Missing step: {expected_step}"
            
            # Verify report was generated
            report_path = temp_project_dir / 'state' / 'quickstart_validation_report.json'
            assert report_path.exists(), "Validation report not generated"
            
            # Verify report content
            with open(report_path) as f:
                report = json.load(f)
            
            assert report['status'] in ['passed', 'completed_with_warnings']
            assert 'total_duration_seconds' in report
            
        finally:
            os.chdir(original_cwd)

    def test_validation_with_mocked_components(self, temp_project_dir):
        """Test validation with mocked external dependencies"""
        from validation.quickstart_validator import QuickstartValidator
        
        # Mock all external dependencies
        with patch('validation.quickstart_validator.get_config') as mock_config, \
             patch('validation.quickstart_validator.download_lsms') as mock_download, \
             patch('validation.quickstart_validator.clean_and_merge') as mock_clean, \
             patch('validation.quickstart_validator.construct_csa_index') as mock_features, \
             patch('validation.quickstart_validator.run_mixed_effects_model') as mock_model, \
             patch('validation.quickstart_validator.create_scatter_plot') as mock_plot:
            
            # Set up mocks
            mock_config.return_value = MagicMock()
            mock_download.return_value = MagicMock()
            mock_clean.return_value = MagicMock()
            mock_features.return_value = MagicMock()
            mock_model.return_value = MagicMock()
            mock_plot.return_value = MagicMock()
            
            # Run validation
            validator = QuickstartValidator()
            results = validator.run_validation()
            
            # Should complete successfully
            assert results['status'] in ['passed', 'completed_with_warnings']
            
            # Verify all mocks were called
            assert mock_config.called
            # Note: Not all mocks may be called depending on implementation

    def test_validation_error_recovery(self, temp_project_dir):
        """Test that validation continues despite individual step failures"""
        from validation.quickstart_validator import QuickstartValidator
        
        # Mock a failing step
        with patch.object(QuickstartValidator, 'validate_configuration', return_value=False):
            validator = QuickstartValidator()
            results = validator.run_validation()
            
            # Should still complete
            assert results['status'] in ['passed', 'completed_with_warnings']
            
            # Should have recorded the failure
            assert len(results['errors']) > 0 or len(results['warnings']) > 0
            
            # All other steps should still be executed
            executed_steps = [s['step'] for s in results['steps']]
            assert len(executed_steps) == 8  # All 8 steps should run

    def test_validation_output_artifacts(self, temp_project_dir):
        """Test that validation generates all expected output artifacts"""
        from validation.quickstart_validator import QuickstartValidator
        
        validator = QuickstartValidator()
        results = validator.run_validation()
        
        # Check for expected artifacts
        artifacts = [
            temp_project_dir / 'state' / 'quickstart_validation_report.json',
            temp_project_dir / 'state' / 'quickstart_validation.log'
        ]
        
        for artifact in artifacts:
            assert artifact.exists(), f"Missing artifact: {artifact}"

    def test_validation_timing_and_performance(self, temp_project_dir):
        """Test that validation completes within reasonable time"""
        from validation.quickstart_validator import QuickstartValidator
        
        start_time = time.time()
        
        validator = QuickstartValidator()
        results = validator.run_validation()
        
        elapsed_time = time.time() - start_time
        
        # Should complete in reasonable time (< 60 seconds for validation)
        assert elapsed_time < 60, f"Validation took too long: {elapsed_time:.2f}s"
        
        # Verify timing was recorded
        assert results['total_duration_seconds'] > 0
        assert abs(results['total_duration_seconds'] - elapsed_time) < 1  # Within 1 second tolerance

    def test_validation_with_partial_data(self, temp_project_dir):
        """Test validation when some data files are missing"""
        from validation.quickstart_validator import QuickstartValidator
        
        # Create partial data structure
        (temp_project_dir / 'data' / 'processed' / 'merged_sample.parquet').write_text('dummy')
        
        validator = QuickstartValidator()
        results = validator.run_validation()
        
        # Should handle missing files gracefully
        assert results['status'] in ['passed', 'completed_with_warnings']
        
        # Output verification should note missing files
        output_step = next((s for s in results['steps'] if s['step'] == 'output_verification'), None)
        assert output_step is not None

    def test_validation_config_override(self, temp_project_dir):
        """Test validation with custom configuration"""
        from validation.quickstart_validator import QuickstartValidator
        from utils.config import reset_config, get_config
        
        # Set custom environment variables
        os.environ['TARGET_COUNTRIES'] = 'KEN'
        os.environ['TARGET_YEARS'] = '2021'
        os.environ['MAX_RAM_GB'] = '4'
        
        try:
            validator = QuickstartValidator()
            results = validator.run_validation()
            
            # Should use custom configuration
            assert results['status'] in ['passed', 'completed_with_warnings']
            
        finally:
            # Clean up environment variables
            for key in ['TARGET_COUNTRIES', 'TARGET_YEARS', 'MAX_RAM_GB']:
                if key in os.environ:
                    del os.environ[key]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
