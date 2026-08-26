"""
Tests for T028: Power limitation check.
"""
import os
import sys
import tempfile
import shutil
import pandas as pd
import pytest

# Add project root to path if needed, assuming standard structure
# In the actual runner, this is handled by the environment setup
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.check_power_limitation import (
    check_power_limitation, 
    get_predictor_count, 
    POWER_RATIO_THRESHOLD
)

class TestPowerLimitation:
    
    def setup_method(self):
        """Create a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create necessary subdirectories
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        os.makedirs("data/analysis", exist_ok=True)

    def teardown_method(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_sufficient_power(self):
        """Test case where samples >= 10 * predictors."""
        # Create a mock dataframe with 100 samples and 5 predictors
        # Predictors: clustering, path_length, degree, etc.
        data = {
            'id': range(100),
            'class': ['random'] * 100,
            'N': [100] * 100,
            'clustering_coefficient': [0.1] * 100,
            'average_path_length': [5.0] * 100,
            'average_degree': [10.0] * 100,
            'degree_distribution_std': [2.0] * 100,
            'decay_rate': [0.5] * 100,
            'r_squared': [0.95] * 100,
            'status': ['dissipative'] * 100
        }
        df = pd.DataFrame(data)
        
        is_sufficient, samples, predictors, message = check_power_limitation(df)
        
        assert is_sufficient is True
        assert samples == 100
        assert predictors == 4  # clustering, path_length, degree, std
        assert "PASS" in message
        assert "HALTING" not in message

    def test_insufficient_power(self):
        """Test case where samples < 10 * predictors."""
        # Create a mock dataframe with 20 samples and 5 predictors
        # Required: 5 * 10 = 50 samples. We have 20.
        data = {
            'id': range(20),
            'class': ['random'] * 20,
            'N': [100] * 20,
            'clustering_coefficient': [0.1] * 20,
            'average_path_length': [5.0] * 20,
            'average_degree': [10.0] * 20,
            'degree_distribution_std': [2.0] * 20,
            'decay_rate': [0.5] * 20,
            'r_squared': [0.95] * 20,
            'status': ['dissipative'] * 20
        }
        df = pd.DataFrame(data)
        
        is_sufficient, samples, predictors, message = check_power_limitation(df)
        
        assert is_sufficient is False
        assert samples == 20
        assert predictors == 4
        assert "FAIL" in message
        assert "HALTING" in message

    def test_predictor_counting_logic(self):
        """Test that the function correctly identifies predictor columns."""
        data = {
            'id': [1, 2],
            'class': ['a', 'b'],
            'N': [100, 100],
            'clustering_coefficient': [0.1, 0.2],
            'average_path_length': [5.0, 6.0],
            'decay_rate': [0.5, 0.6],
            'r_squared': [0.9, 0.9],
            'status': ['d', 'd']
        }
        df = pd.DataFrame(data)
        
        count, names = get_predictor_count(df)
        
        # Expected predictors: clustering_coefficient, average_path_length
        # Excluded: id, class, N, decay_rate, r_squared, status
        assert count == 2
        assert "clustering_coefficient" in names
        assert "average_path_length" in names
        assert "id" not in names
        assert "decay_rate" not in names

    def test_zero_predictors(self):
        """Test behavior when no predictor columns are found."""
        data = {
            'id': [1, 2],
            'class': ['a', 'b'],
            'N': [100, 100],
            'decay_rate': [0.5, 0.6],
            'r_squared': [0.9, 0.9],
            'status': ['d', 'd']
        }
        df = pd.DataFrame(data)
        
        count, names = get_predictor_count(df)
        
        assert count == 0
        assert names == []
        
        # Should not crash when checking power with 0 predictors
        # (though logically 10*0 = 0, so any N >= 0 passes)
        is_sufficient, samples, predictors, message = check_power_limitation(df)
        assert is_sufficient is True
        assert "PASS" in message