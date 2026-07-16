"""
Unit tests for edge cases in code/analysis/fitting.py.
Specifically tests power-law convergence failure handling.
"""
import pytest
import numpy as np
import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.fitting import fit_power_law_model, run_fitting_for_subject


class TestPowerLawConvergenceFailure:
    """Tests for handling power-law convergence failures."""

    def test_fit_power_law_model_convergence_failure_raises_custom_error(self):
        """
        Test that fit_power_law_model raises a specific error when
        the powerlaw package fails to converge, rather than returning NaN
        or crashing silently.
        """
        # Create a mock that simulates a convergence failure
        mock_result = MagicMock()
        mock_result.loglikelihood = float('nan')  # Simulate failure state
        
        # We need to mock the powerlaw.Fit call to return a result that indicates failure
        # or raises an exception. Based on T033, we expect the code to handle this.
        # Let's create a scenario where the fit object's attributes indicate failure.
        
        with patch('analysis.fitting.powerlaw.Fit') as mock_fit_class:
            # Simulate a fit that exists but has no valid parameters (convergence failure)
            mock_fit_instance = MagicMock()
            mock_fit_instance.power_law = None
            mock_fit_instance.loglikelihood = float('-inf')
            mock_fit_instance.d = float('inf')
            mock_fit_instance.p = 0.0
            
            mock_fit_class.return_value = mock_fit_instance
            
            # Create a small array of avalanche sizes that might cause issues
            # (e.g., too few data points or all same value)
            avalanche_sizes = np.array([1.0, 1.0, 1.0, 1.0])
            
            # The function should raise a specific error or return a specific status
            # based on the T033 requirement to "explicitly handle convergence failure"
            # and "log a specific error code and exclude the participant".
            # We expect an exception here to signal the failure clearly.
            with pytest.raises(Exception) as exc_info:
                fit_power_law_model(avalanche_sizes)
            
            # Verify the error message contains relevant information
            error_msg = str(exc_info.value)
            assert "convergence" in error_msg.lower() or "fit" in error_msg.lower() or "failed" in error_msg.lower()

    def test_run_fitting_for_subject_handles_convergence_failure_gracefully(self):
        """
        Test that run_fitting_for_subject handles convergence failure by
        logging the error and excluding the participant from results,
        rather than crashing the pipeline.
        """
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create a mock participant data file with problematic data
            subject_id = "test_subject_convergence_fail"
            eeg_file = tmpdir_path / f"{subject_id}_eeg_processed.npy"
            
            # Create a file that will likely cause convergence issues
            # (e.g., constant values or very few unique values)
            np.save(eeg_file, np.array([5.0] * 100))
            
            # Mock the load_avalanche_sizes_from_store to return problematic sizes
            problematic_sizes = np.array([2.0, 2.0, 2.0, 2.0])
            
            with patch('analysis.fitting.load_avalanche_sizes_from_store', return_value=problematic_sizes):
                with patch('analysis.fitting.get_logger') as mock_logger:
                    mock_logger_instance = MagicMock()
                    mock_logger.return_value = mock_logger_instance
                    
                    # This should not crash the pipeline
                    # It should log the error and return a status indicating failure
                    result = run_fitting_for_subject(
                        subject_id=subject_id,
                        data_root=tmpdir_path,
                        processed_dir=tmpdir_path
                    )
                    
                    # Verify that an error was logged
                    mock_logger_instance.error.assert_called()
                    
                    # Verify the result indicates failure or exclusion
                    # The exact structure depends on the implementation, but it should not be a valid fit
                    assert result is not None
                    # If the function returns a dict, it should have a 'status' or 'error' key
                    if isinstance(result, dict):
                        assert 'status' in result or 'error' in result or 'converged' in result

    def test_fit_power_law_model_with_insufficient_data(self):
        """
        Test that fitting with insufficient data points (e.g., < 3)
        raises a clear error.
        """
        avalanche_sizes = np.array([1.0, 2.0])  # Only 2 points
        
        with pytest.raises(ValueError) as exc_info:
            fit_power_law_model(avalanche_sizes)
        
        assert "insufficient" in str(exc_info.value).lower() or "data" in str(exc_info.value).lower()

    def test_fit_power_law_model_with_non_positive_values(self):
        """
        Test that fitting with non-positive values raises a clear error.
        Power-law distributions are defined for positive values only.
        """
        avalanche_sizes = np.array([1.0, 0.0, -1.0, 2.0])
        
        with pytest.raises(ValueError) as exc_info:
            fit_power_law_model(avalanche_sizes)
        
        assert "positive" in str(exc_info.value).lower() or "non-positive" in str(exc_info.value).lower()

    def test_fit_power_law_model_with_all_zeros(self):
        """
        Test that fitting with all zeros raises a clear error.
        """
        avalanche_sizes = np.array([0.0, 0.0, 0.0])
        
        with pytest.raises(ValueError) as exc_info:
            fit_power_law_model(avalanche_sizes)
        
        assert "positive" in str(exc_info.value).lower() or "zero" in str(exc_info.value).lower()
