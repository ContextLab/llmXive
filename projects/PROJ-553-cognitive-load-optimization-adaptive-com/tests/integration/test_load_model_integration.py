import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from train_load_model import train_model, validate_against_golden_set, engineer_features
from utils import setup_logging

logger = setup_logging()

@pytest.fixture
def mock_training_data():
    """
    Creates a mock dataset for training.
    """
    np.random.seed(42)
    n = 100
    data = {
        'session_id': range(n),
        'latency': np.random.exponential(10, n),
        'error_count': np.random.poisson(2, n),
        'hint_count': np.random.poisson(1, n),
        'target_load': np.random.uniform(0, 100, n) # Mock target
    }
    df = pd.DataFrame(data)
    # Add split column
    df['split'] = np.random.choice(['train', 'val'], n, p=[0.8, 0.2])
    return df

@pytest.fixture
def mock_golden_set():
    """
    Creates a mock Golden Set for validation.
    """
    np.random.seed(42)
    n = 50
    data = {
        'session_id': range(n),
        'latency': np.random.exponential(10, n),
        'error_count': np.random.poisson(2, n),
        'hint_count': np.random.poisson(1, n),
        'expert_load_score': np.random.uniform(0, 100, n) # Mock expert labels
    }
    return pd.DataFrame(data)

def test_train_and_validate(mock_training_data, mock_golden_set, tmp_path):
    """
    Integration test for the full training and validation pipeline.
    """
    # 1. Engineer features
    train_df = engineer_features(mock_training_data)
    
    # Define feature columns
    exclude_cols = ['session_id', 'split', 'target_load']
    feature_cols = [col for col in train_df.columns if col not in exclude_cols]

    # 2. Prepare data
    train_data = train_df[train_df['split'] == 'train']
    val_data = train_df[train_df['split'] == 'val']

    X_train = train_data[feature_cols].fillna(0)
    y_train = train_data['target_load'].fillna(0)
    X_val = val_data[feature_cols].fillna(0)
    y_val = val_data['target_load'].fillna(0)

    # 3. Train model
    model = train_model(X_train, y_train, X_val, y_val)

    # 4. Validate against Golden Set
    # Ensure mock golden set has the same features
    golden_df = mock_golden_set.copy()
    golden_df = engineer_features(golden_df)
    
    r, p = validate_against_golden_set(model, golden_df, feature_cols)

    # Assert that validation ran and produced a correlation
    assert -1 <= r <= 1, f"Pearson r must be between -1 and 1, got {r}"
    assert p >= 0, f"P-value must be non-negative, got {p}"
    
    logger.info(f"Integration test passed. Pearson r = {r:.4f}, p-value = {p:.4f}")

def test_collinearity_check(mock_training_data):
    """
    Test the collinearity check function.
    """
    from train_load_model import check_collinearity
    
    exclude_cols = ['session_id', 'split', 'target_load']
    feature_cols = [col for col in mock_training_data.columns if col not in exclude_cols]
    
    high_vif = check_collinearity(mock_training_data, feature_cols, threshold=5.0)
    
    # Should return a list of tuples
    assert isinstance(high_vif, list)
    for item in high_vif:
        assert isinstance(item, tuple)
        assert len(item) == 2
        assert item[1] > 5.0
