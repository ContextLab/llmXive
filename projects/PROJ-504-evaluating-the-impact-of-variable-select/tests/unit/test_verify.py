"""
Unit tests for the verify.py pilot run logic.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import math

# Import the module under test
# Note: We need to ensure the path is correct for the test environment
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from verify import run_pilot_simulation, check_pilot_results, calculate_adjusted_count


class TestRunPilotSimulation:
    def test_run_pilot_simulation_basic(self):
        """Test that pilot simulation runs and returns expected structure."""
        with patch('verify.fetch_datasets') as mock_fetch, \
             patch('verify.generate_synthetic_outcomes') as mock_gen, \
             patch('verify.select_variables_lasso') as mock_select:
             
            # Mock dataset
            mock_dataset = MagicMock()
            mock_dataset.dataset_id = 1468
            mock_dataset.X = np.random.rand(100, 5)
            mock_dataset.true_coefficients = np.array([1.0, 0.0, 1.0, 0.0, 1.0])
            
            mock_fetch.return_value = [mock_dataset]
            mock_gen.return_value = np.random.rand(100)
            mock_select.return_value = [0, 2, 4]  # Select all non-zero
            
            result = run_pilot_simulation(count=2, seed=42)
            
            assert result['status'] == 'success'
            assert result['simulation_count'] == 2
            assert len(result['results']) == 2
            assert all('power' in r for r in result['results'])
            
    def test_run_pilot_simulation_no_datasets(self):
        """Test handling when no datasets are fetched."""
        with patch('verify.fetch_datasets') as mock_fetch:
            mock_fetch.return_value = []
            
            result = run_pilot_simulation(count=10, seed=42)
            
            assert result['status'] == 'failed'
            assert 'error' in result


class TestCheckPilotResults:
    def test_check_pilot_results_pass(self):
        """Test passing pilot results."""
        # Simulate 100 simulations with low variance
        power_values = [0.5 + (i % 10) * 0.001 for i in range(100)]
        results = [{'power': p} for p in power_values]
        
        pilot_data = {
            'status': 'success',
            'elapsed_time': 100,  # Well under 5.5 hours
            'results': results
        }
        
        assert check_pilot_results(pilot_data) is True
        
    def test_check_pilot_results_runtime_fail(self):
        """Test failing due to excessive runtime."""
        pilot_data = {
            'status': 'success',
            'elapsed_time': 20000,  # > 5.5 hours (19800s)
            'results': [{'power': 0.5}]
        }
        
        assert check_pilot_results(pilot_data) is False
        
    def test_check_pilot_results_ci_width_fail(self):
        """Test failing due to high CI width."""
        # High variance data
        power_values = [0.2, 0.8, 0.1, 0.9, 0.3, 0.7] * 10  # 60 samples, high variance
        results = [{'power': p} for p in power_values]
        
        pilot_data = {
            'status': 'success',
            'elapsed_time': 100,
            'results': results
        }
        
        # CI width should be high
        assert check_pilot_results(pilot_data) is False
        
    def test_check_pilot_results_no_results(self):
        """Test failing when no results are present."""
        pilot_data = {
            'status': 'success',
            'elapsed_time': 100,
            'results': []
        }
        
        assert check_pilot_results(pilot_data) is False


class TestCalculateAdjustedCount:
    def test_calculate_adjusted_count_basic(self):
        """Test basic calculation of adjusted count."""
        # If current width is 0.2 and target is 0.1, we need 4x the samples
        new_count = calculate_adjusted_count(10, 0.2, 0.1)
        assert new_count == 40
        
    def test_calculate_adjusted_count_zero_width(self):
        """Test handling of zero width."""
        new_count = calculate_adjusted_count(10, 0.0, 0.1)
        assert new_count == 10
        
    def test_calculate_adjusted_count_max_cap(self):
        """Test that count is capped at max_pilot_count."""
        # This would calculate a very large number
        new_count = calculate_adjusted_count(10, 10.0, 0.1)
        assert new_count == 1000  # max_pilot_count
