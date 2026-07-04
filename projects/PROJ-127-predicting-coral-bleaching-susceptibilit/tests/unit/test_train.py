import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from train import spatial_split, evaluate_model

def create_mock_data(n_rows=100):
    """Create a mock dataframe for testing."""
    np.random.seed(42)
    data = {
        'longitude': np.random.uniform(-180, 180, n_rows),
        'feature_1': np.random.rand(n_rows),
        'feature_2': np.random.rand(n_rows),
        'bleaching_event': np.random.choice([0, 1], n_rows, p=[0.7, 0.3])
    }
    return pd.DataFrame(data)

class TestSpatialSplit:
    def test_spatial_split_west_east(self):
        df = create_mock_data(1000)
        # Ensure we have both positive and negative longitudes
        assert df['longitude'].max() > 0
        assert df['longitude'].min() < 0

        X_train, X_test, y_train, y_test = spatial_split(df, 'bleaching_event')

        # Check split logic: Train (lon > 0), Test (lon <= 0)
        assert len(X_train) > 0
        assert len(X_test) > 0
        
        # Verify no leakage of target or longitude in features
        assert 'longitude' not in X_train.columns
        assert 'longitude' not in X_test.columns
        assert 'bleaching_event' not in X_train.columns
        assert 'bleaching_event' not in X_test.columns

    def test_spatial_split_zero_positives(self):
        # Create data where test set (lon <= 0) has no positive events
        data = {
            'longitude': [-10.0] * 50 + [10.0] * 50, # Test: -10, Train: 10
            'feature_1': np.random.rand(100),
            'bleaching_event': [0] * 50 + [1, 1, 1, 1, 1] # Only positives in Train
        }
        df = pd.DataFrame(data)

        X_train, X_test, y_train, y_test = spatial_split(df, 'bleaching_event')

        assert y_test.sum() == 0
        # The function should still return the split, evaluation logic handles the warning

class TestEvaluateModel:
    def test_evaluate_zero_positives_warning(self):
        from unittest.mock import Mock
        
        # Mock model
        mock_model = Mock()
        mock_model.predict_proba.return_value = np.array([[0.9, 0.1], [0.8, 0.2], [0.7, 0.3]])
        
        y_test = pd.Series([0, 0, 0]) # Zero positives
        X_test = pd.DataFrame({'f1': [1, 2, 3]})

        result = evaluate_model(mock_model, X_test, y_test)
        
        assert result['roc_auc'] is None
        assert 'warning' in result