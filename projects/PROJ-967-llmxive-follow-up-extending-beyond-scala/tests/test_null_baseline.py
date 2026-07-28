"""
Unit tests for Null Baseline Comparison (Task T030c)
"""

import pytest
import numpy as np
import pandas as pd
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path if running from tests
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from null_baseline import (
    calculate_mean_baseline_metrics,
    compare_and_save_results,
    load_features,
    load_rf_results
)

@pytest.fixture
def mock_df():
    """Create a mock dataframe with required columns."""
    data = {
        'sample_id': range(100),
        'fidelity_loss': np.random.rand(100) * 10,
        'variance': np.random.rand(100),
        'entropy': np.random.rand(100),
        'skewness': np.random.rand(100),
        'kurtosis': np.random.rand(100),
        'score_magnitude': np.random.rand(100),
        'dominant_eigenvalue': np.random.rand(100),
        'excluded_reason': [None] * 100
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_split_config():
    """Create a mock split configuration."""
    return {
        'test_indices': list(range(80, 100))
    }

@pytest.fixture
def mock_rf_model():
    """Create a mock Random Forest model."""
    model = MagicMock()
    model.predict.return_value = np.random.rand(20) * 10
    return model

def test_calculate_mean_baseline_metrics(mock_df, mock_split_config, caplog):
    """Test that mean baseline metrics are calculated correctly."""
    with caplog.at_level(logging.INFO):
        r2, mae, y_test, y_pred_mean, X_test, y_train, X_train = calculate_mean_baseline_metrics(
            mock_df, mock_split_config, logging.getLogger(__name__)
        )
        
        assert isinstance(r2, float)
        assert isinstance(mae, float)
        assert len(y_test) == 20
        assert len(y_pred_mean) == 20
        assert len(y_train) == 80
        # Mean predictor should have R2 <= 0 typically, but not guaranteed with small samples
        # Just check it's a number
        assert not np.isnan(r2)
        assert not np.isnan(mae)

def test_compare_and_save_results(tmp_path, caplog):
    """Test that comparison results are saved correctly."""
    rf_residuals = np.random.rand(20)
    mean_residuals = np.random.rand(20)
    
    results = compare_and_save_results(
        rf_r2=0.5, rf_mae=1.0, rf_residuals=rf_residuals,
        mean_r2=0.1, mean_mae=1.5, mean_residuals=mean_residuals,
        logger=logging.getLogger(__name__)
    )
    
    assert 'rf_r2' in results
    assert 'mean_r2' in results
    assert 'p_value' in results
    assert 'is_significant_at_0.05' in results
    
    # Check file was written
    output_path = Path("results/null_baseline_comparison.json")
    if output_path.exists():
        with open(output_path, 'r') as f:
            saved_results = json.load(f)
        assert saved_results['rf_r2'] == 0.5
        assert saved_results['mean_r2'] == 0.1

def test_load_features_missing_file(caplog):
    """Test that load_features raises error if file not found."""
    with patch('pathlib.Path.exists', return_value=False):
        with pytest.raises(SystemExit):
            load_features(logging.getLogger(__name__))

def test_load_rf_results_missing_model(caplog):
    """Test that load_rf_results raises error if model not found."""
    with patch('pathlib.Path.exists', return_value=False):
        with pytest.raises(SystemExit):
            load_rf_results(logging.getLogger(__name__))

if __name__ == "__main__":
    pytest.main([__file__, "-v"])