import pytest
import pandas as pd
import numpy as np
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from modeling.baseline import load_and_prepare_data, train_baseline_model, run_baseline_pipeline

@pytest.fixture
def mock_processed_data():
    """Create a mock dataframe with residuals and interaction features."""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'temperature': np.random.uniform(400, 600, n_samples),
        'Mg': np.random.uniform(0.5, 2.0, n_samples),
        'Si': np.random.uniform(0.2, 1.0, n_samples),
        'Cu': np.random.uniform(0.1, 0.8, n_samples),
        'Alloy_Series': np.random.choice(['6061', '7075', '5052'], n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Create interaction features (simulating T020 output)
    df['Temp_x_Mg'] = df['temperature'] * df['Mg']
    df['Temp_x_Si'] = df['temperature'] * df['Si']
    df['Temp_x_Cu'] = df['temperature'] * df['Cu']
    
    # Normalize (simulating T021 output - just scaling for this test)
    # In reality, this would be StandardScaler output
    for col in ['temperature', 'Mg', 'Si', 'Cu', 'Temp_x_Mg', 'Temp_x_Si', 'Temp_x_Cu']:
        df[col] = (df[col] - df[col].mean()) / df[col].std()
    
    # Create a mock residualized target (simulating T022 output)
    # y = b0 + b1*Temp + b2*Mg + b3*(Temp*Mg) + noise
    true_coefs = {
        'temperature': 0.5,
        'Mg': 0.3,
        'Temp_x_Mg': 0.2
    }
    
    y = (
        true_coefs['temperature'] * df['temperature'] +
        true_coefs['Mg'] * df['Mg'] +
        true_coefs['Temp_x_Mg'] * df['Temp_x_Mg'] +
        np.random.normal(0, 0.1, n_samples)
    )
    df['grain_size_residual'] = y
    
    return df

@patch('modeling.baseline.load_processed_data')
def test_load_and_prepare_data(mock_load_data, mock_processed_data):
    """Test that load_and_prepare_data correctly extracts X, y, and features."""
    mock_load_data.return_value = mock_processed_data
    
    X, y, feature_names = load_and_prepare_data()
    
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert 'grain_size_residual' not in feature_names
    assert 'Temp_x_Mg' in feature_names
    assert 'Temp_x_Si' in feature_names
    assert len(y) == len(mock_processed_data)
    assert len(X.columns) == len(feature_names)

def test_train_baseline_model():
    """Test that train_baseline_model returns correct structures."""
    # Create simple dummy data
    X = pd.DataFrame({
        'feat1': [1, 2, 3, 4, 5],
        'feat2': [2, 4, 6, 8, 10],
        'feat1_x_feat2': [2, 8, 18, 32, 50]
    })
    y = pd.Series([1.1, 2.2, 3.3, 4.4, 5.5])
    feature_names = ['feat1', 'feat2', 'feat1_x_feat2']
    
    model, metrics, coefficients = train_baseline_model(X, y, feature_names)
    
    assert model is not None
    assert 'r2_train' in metrics
    assert 'mae_train' in metrics
    assert 'intercept' in coefficients
    assert 'feat1' in coefficients
    assert 'feat1_x_feat2' in coefficients
    assert metrics['r2_train'] > 0.9 # Should fit well

@patch('modeling.baseline.load_processed_data')
@patch('modeling.baseline.LinearRegression')
@patch('modeling.baseline.save_model_artifacts')
def test_run_baseline_pipeline(mock_save, mock_lr_class, mock_load, mock_processed_data):
    """Test the full pipeline execution flow."""
    mock_load.return_value = mock_processed_data
    
    # Mock the model instance
    mock_model_instance = MagicMock()
    mock_model_instance.coef_ = [0.1, 0.2, 0.3]
    mock_model_instance.intercept_ = 0.5
    mock_model_instance.predict.return_value = np.array([1, 2, 3, 4, 5])
    mock_lr_class.return_value = mock_model_instance
    
    result = run_baseline_pipeline()
    
    assert result == 0
    mock_load.assert_called_once()
    mock_lr_class.assert_called_once()
    mock_save.assert_called_once()