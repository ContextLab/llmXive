import json
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Mock the config to avoid needing real datasets for this unit test
# We test the logic flow, not the real data fetch
from unittest.mock import patch, MagicMock

# Import the function to test
from code.main import run_baseline_analysis, clean_data_listwise

class TestMainPipelineLogic:
    
    def test_clean_data_listwise_removes_nan(self):
        """Test T016: Listwise deletion of missing values."""
        data = np.array([
            [1.0, 2.0, 3.0],
            [4.0, np.nan, 6.0],
            [7.0, 8.0, 9.0],
            [10.0, 11.0, np.nan]
        ])
        
        clean = clean_data_listwise(data)
        
        # Should only keep the first and third rows
        assert clean.shape == (2, 3)
        assert np.all(clean == np.array([[1.0, 2.0, 3.0], [7.0, 8.0, 9.0]]))

    def test_clean_data_listwise_empty_after_drop(self):
        """Test T016: Raise error if all data is missing."""
        data = np.array([
            [np.nan, 2.0],
            [np.nan, np.nan]
        ])
        
        with pytest.raises(ValueError, match="Dataset empty after listwise deletion"):
            clean_data_listwise(data)

    def test_baseline_analysis_skips_small_sample(self):
        """Test T015: Skip datasets with N < 30."""
        # Mock the loader to return a small dataset
        small_data = np.random.rand(10, 5)
        
        with patch('code.main.load_dataset') as mock_load, \
             patch('code.main.get_dataset_info') as mock_info:
            
            mock_load.return_value = small_data
            mock_info.return_value = {"id": "test_small"}
            
            result = run_baseline_analysis("test_small")
            
            assert result["status"] == "skipped"
            assert "insufficient sample size" in result["reason"]
            assert result["n_obs"] == 10

    def test_baseline_analysis_output_structure(self):
        """Test T014: Verify output matches schema keys."""
        # Mock a valid dataset (N > 30)
        valid_data = np.random.rand(50, 5)
        
        # Mock the theoretical power calculation
        with patch('code.main.load_dataset') as mock_load, \
             patch('code.main.get_dataset_info') as mock_info, \
             patch('code.main.calculate_theoretical_power') as mock_theory, \
             patch('code.main.run_bootstrap_power_simulation') as mock_empirical, \
             patch('code.main.bootstrap_validity_check') as mock_valid:
            
            mock_load.return_value = valid_data
            mock_info.return_value = {"id": "test_valid"}
            mock_theory.return_value = 0.80
            mock_empirical.return_value = {"power_estimate": 0.78}
            mock_valid.return_value = True
            
            result = run_baseline_analysis("test_valid")
            
            # Verify required keys exist
            assert "dataset_id" in result
            assert "theoretical_power" in result
            assert "empirical_power" in result
            assert "absolute_error" in result
            assert "status" in result
            
            # Verify calculation
            assert result["absolute_error"] == abs(0.80 - 0.78)
            assert result["status"] == "completed"
