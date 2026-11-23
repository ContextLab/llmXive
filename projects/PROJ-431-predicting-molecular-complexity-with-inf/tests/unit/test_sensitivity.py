import pytest
import json
import os
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path

# Import the function to test
from model import run_sensitivity_analysis

def test_run_sensitivity_analysis():
    """Test that sensitivity analysis produces valid output and stability metrics."""
    
    # Create a temporary directory for test artifacts
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = os.path.join(tmpdir, 'test_data.csv')
        output_path = os.path.join(tmpdir, 'sensitivity_sweep.json')

        # Create a synthetic dataset with known properties
        np.random.seed(42)
        n_samples = 100
        X = np.random.normal(0, 1, n_samples)
        y = 2.0 * X + np.random.normal(0, 0.5, n_samples)

        df = pd.DataFrame({
            'atom_entropy': X,
            'logS': y
        })
        df.to_csv(data_path, index=False)

        # Run sensitivity analysis
        result = run_sensitivity_analysis(
            data_path=data_path,
            output_path=output_path,
            alpha_range=[0.1, 1.0, 10.0],
            feature_col='atom_entropy',
            target_col='logS'
        )

        # Verify the output file exists
        assert os.path.exists(output_path), "Output JSON file was not created."

        # Load and verify the JSON content
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)

        # Check structure
        assert 'alpha_values' in loaded_data
        assert 'metrics' in loaded_data
        assert 'stability_metrics' in loaded_data

        # Check alpha values
        assert loaded_data['alpha_values'] == [0.1, 1.0, 10.0]
        assert len(loaded_data['metrics']) == 3

        # Check stability metrics keys
        sm = loaded_data['stability_metrics']
        required_keys = [
            'rmse_relative_range', 'pearson_relative_range',
            'rmse_mean', 'pearson_mean',
            'rmse_min', 'rmse_max',
            'pearson_min', 'pearson_max'
        ]
        for key in required_keys:
            assert key in sm, f"Missing key: {key}"

        # Verify numerical types
        assert isinstance(sm['rmse_relative_range'], float)
        assert isinstance(sm['pearson_relative_range'], float)

        # Verify that relative ranges are non-negative
        assert sm['rmse_relative_range'] >= 0
        assert sm['pearson_relative_range'] >= 0

        # Verify that means are non-zero (since we generated data with signal)
        assert sm['rmse_mean'] > 0
        assert abs(sm['pearson_mean']) > 0.5 # Should be reasonably correlated

def test_sensitivity_with_missing_values():
    """Test that sensitivity analysis handles missing values correctly."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = os.path.join(tmpdir, 'test_data_nan.csv')
        output_path = os.path.join(tmpdir, 'sensitivity_sweep_nan.json')

        # Create dataset with NaN values
        df = pd.DataFrame({
            'atom_entropy': [1.0, 2.0, np.nan, 4.0, 5.0],
            'logS': [0.5, 1.0, 1.5, np.nan, 2.5]
        })
        df.to_csv(data_path, index=False)

        # Should not raise an error, but drop NaN rows
        result = run_sensitivity_analysis(
            data_path=data_path,
            output_path=output_path,
            alpha_range=[1.0],
            feature_col='atom_entropy',
            target_col='logS'
        )

        # Verify output exists
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        # Should have processed the 3 valid rows
        assert len(loaded['metrics']) == 1
        assert loaded['metrics'][0]['rmse'] > 0
