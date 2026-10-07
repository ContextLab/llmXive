import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
import sys

# Add code to path if necessary
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.stats import linear_regression_with_mass_control, run_statistical_tests
from utils.config import get_project_root, get_data_processed_path

class TestRegressionWithMassControl:
    def test_regression_output_columns(self):
        """Test that regression output has required columns."""
        data = pd.DataFrame({
            'triaxiality': np.random.rand(100),
            'b_a_ratio': np.random.rand(100),
            'mass': np.random.rand(100) * 1e12,
            'sfr': np.random.rand(100)
        })
        
        result = linear_regression_with_mass_control(data)
        
        expected_cols = ['predictor', 'coefficient', 'p_value', 'r_squared', 'ci_lower', 'ci_upper']
        assert all(col in result.columns for col in expected_cols)
        assert len(result) > 0

    def test_regression_handles_nan(self):
        """Test that regression handles NaN values by dropping them."""
        data = pd.DataFrame({
            'triaxiality': [1.0, np.nan, 0.5] + [0.5] * 20,
            'b_a_ratio': [0.5, 0.5, np.nan] + [0.5] * 20,
            'mass': [1e12] * 23,
            'sfr': [0.1] * 23
        })
        
        # Should not raise, just drop NaNs
        result = linear_regression_with_mass_control(data)
        assert isinstance(result, pd.DataFrame)

    def test_regression_mass_coefficient_present(self):
        """Test that mass coefficient is in the result."""
        data = pd.DataFrame({
            'triaxiality': np.random.rand(50),
            'b_a_ratio': np.random.rand(50),
            'mass': np.random.rand(50) * 1e12,
            'sfr': np.random.rand(50)
        })
        
        result = linear_regression_with_mass_control(data)
        predictors = result['predictor'].tolist()
        assert 'mass' in predictors

class TestStatisticalTestsRunner:
    def test_run_statistical_tests_creates_output(self):
        """Test that the runner creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            chunks_dir = os.path.join(tmpdir, "matched_chunks")
            os.makedirs(chunks_dir)
            
            # Create a dummy chunk
            chunk_data = pd.DataFrame({
                'halo_id': range(100),
                'triaxiality': np.random.rand(100),
                'b_a_ratio': np.random.rand(100),
                'mass': np.random.rand(100) * 1e12,
                'sfr': np.random.rand(100),
                'galaxy_id': range(100)
            })
            chunk_path = os.path.join(chunks_dir, "match_001.csv")
            chunk_data.to_csv(chunk_path, index=False)
            
            output_path = os.path.join(tmpdir, "regression_results.csv")
            
            run_statistical_tests(chunks_dir, output_path)
            
            assert os.path.exists(output_path)
            result_df = pd.read_csv(output_path)
            assert len(result_df) > 0
            assert 'coefficient' in result_df.columns
            assert 'p_value' in result_df.columns
            assert 'r_squared' in result_df.columns
            assert 'ci_lower' in result_df.columns
            assert 'ci_upper' in result_df.columns