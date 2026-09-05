import json
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Mock config for testing
class MockConfig:
    MODELS_DIR = tempfile.mkdtemp()

# Temporarily patch config
import sys
from unittest.mock import patch

# We need to mock the config before importing the module
with patch.dict('sys.modules', {'config': type(sys)('config')}):
    import sys as mock_sys
    mock_config = mock_sys.modules['config']
    mock_config.MODELS_DIR = MockConfig.MODELS_DIR
    
    from models.save_artifacts import save_linear_coefficients, aggregate_metrics

class TestSaveArtifacts:
    @classmethod
    def teardown_class(cls):
        # Clean up temp directory
        if os.path.exists(MockConfig.MODELS_DIR):
            shutil.rmtree(MockConfig.MODELS_DIR)

    def test_save_linear_coefficients(self):
        """Test that linear coefficients are saved correctly to JSON."""
        test_coef = 0.5432
        test_intercept = 1.2345
        test_p_value = 0.0023
        
        save_linear_coefficients(test_coef, test_intercept, test_p_value)
        
        output_path = Path(MockConfig.MODELS_DIR) / "linear_coef.json"
        assert output_path.exists(), "linear_coef.json was not created"
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert 'coef' in data
        assert 'intercept' in data
        assert 'p_value' in data
        assert abs(data['coef'] - test_coef) < 1e-6
        assert abs(data['intercept'] - test_intercept) < 1e-6
        assert abs(data['p_value'] - test_p_value) < 1e-6

    def test_aggregate_metrics(self):
        """Test that metrics are aggregated correctly."""
        test_metrics = {
            'rf_r2': 0.85,
            'rf_rmse': 0.12,
            'rf_mae': 0.09,
            'gb_r2': 0.82,
            'gb_rmse': 0.15,
            'gb_mae': 0.11,
            'mean_r2': 0.05
        }
        
        aggregate_metrics(**test_metrics)
        
        output_path = Path(MockConfig.MODELS_DIR) / "metrics.json"
        assert output_path.exists(), "metrics.json was not created"
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        for key, value in test_metrics.items():
            assert key in data, f"Key {key} missing from metrics"
            assert abs(data[key] - value) < 1e-6, f"Value mismatch for {key}"

    def test_aggregate_metrics_partial(self):
        """Test that partial metrics update correctly."""
        # First call with some metrics
        aggregate_metrics(rf_r2=0.85, rf_rmse=0.12)
        
        # Second call with different metrics
        aggregate_metrics(gb_r2=0.82, gb_rmse=0.15)
        
        output_path = Path(MockConfig.MODELS_DIR) / "metrics.json"
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # Both sets should be present
        assert 'rf_r2' in data
        assert 'rf_rmse' in data
        assert 'gb_r2' in data
        assert 'gb_rmse' in data

    def test_save_linear_coefficients_types(self):
        """Test that values are converted to float correctly."""
        # Pass integer-like values
        save_linear_coefficients(1, 2, 3)
        
        output_path = Path(MockConfig.MODELS_DIR) / "linear_coef.json"
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data['coef'], float)
        assert isinstance(data['intercept'], float)
        assert isinstance(data['p_value'], float)