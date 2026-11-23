import os
import sys
import tempfile
import pickle
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add code to path if not already there
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from classification.train_classifier import load_filtered_data, encode_labels, train_model

@pytest.fixture
def sample_data(tmp_path):
    """Create sample features and labels for testing."""
    # Create sample features (100 samples, 50 features)
    X = np.random.randn(100, 50)
    
    # Create labels DataFrame with some 'null' values
    labels_data = {
        'clip_id': [f"clip_{i}" for i in range(100)],
        'label': ['valid'] * 40 + ['invalid'] * 40 + ['null'] * 20,
        'reason': [''] * 80 + ['confidence_low'] * 20,
        'confidence_score': [0.95] * 80 + [0.5] * 20,
        'perturbation_type': [0] * 80 + [0] * 20
    }
    labels_df = pd.DataFrame(labels_data)
    
    # Save to temp files
    features_path = tmp_path / "features.npy"
    labels_path = tmp_path / "labels.csv"
    output_path = tmp_path / "classifier.pkl"
    
    np.save(features_path, X)
    labels_df.to_csv(labels_path, index=False)
    
    return X, labels_df, features_path, labels_path, output_path

def test_load_filtered_data_filters_nulls(sample_data):
    """Test that load_filtered_data correctly filters out null labels."""
    X, labels_df, features_path, labels_path, _ = sample_data
    
    X_loaded, y_loaded, indices_loaded = load_filtered_data(features_path, labels_path)
    
    # Should have 80 samples (100 - 20 nulls)
    assert len(X_loaded) == 80
    assert len(y_loaded) == 80
    
    # All labels should be 0 or 1 (no nulls)
    assert set(np.unique(y_loaded)).issubset({0, 1})
    
    # Indices should match non-null clip IDs
    expected_indices = labels_df[labels_df['label'] != 'null']['clip_id'].values
    assert np.array_equal(indices_loaded, expected_indices)

def test_encode_labels(sample_data):
    """Test that encode_labels converts labels to integers correctly."""
    # Create simple label array
    y = np.array([1, 0, 1, 0, 1])  # 1=valid, 0=invalid
    encoded = encode_labels(y)
    
    assert encoded.dtype == int
    assert np.array_equal(encoded, y)

def test_train_model_random_forest(sample_data):
    """Test training a Random Forest model."""
    X, _, features_path, labels_path, output_path = sample_data
    
    X_loaded, y_loaded, _ = load_filtered_data(features_path, labels_path)
    
    result = train_model(X_loaded, y_loaded, model_type="random_forest", output_path=output_path)
    
    # Check result structure
    assert 'model' in result
    assert 'scaler' in result
    assert 'model_type' in result
    assert result['model_type'] == 'random_forest'
    assert 'best_params' in result
    assert 'test_f1' in result
    
    # Check that model file was created
    assert output_path.exists()
    
    # Verify model can be loaded and used for prediction
    with open(output_path, 'rb') as f:
        loaded_result = pickle.load(f)
    
    assert 'model' in loaded_result
    assert 'scaler' in loaded_result
    
    # Test prediction on a small sample
    test_sample = X_loaded[:5]
    test_scaled = loaded_result['scaler'].transform(test_sample)
    predictions = loaded_result['model'].predict(test_scaled)
    
    assert len(predictions) == 5
    assert set(predictions).issubset({0, 1})

def test_train_model_mlp(sample_data):
    """Test training an MLP model."""
    X, _, features_path, labels_path, output_path = sample_data
    
    X_loaded, y_loaded, _ = load_filtered_data(features_path, labels_path)
    
    result = train_model(X_loaded, y_loaded, model_type="mlp", output_path=output_path)
    
    # Check result structure
    assert 'model' in result
    assert result['model_type'] == 'mlp'
    assert 'test_f1' in result
    
    # Check that model file was created
    assert output_path.exists()

def test_train_model_with_imbalanced_data(sample_data):
    """Test training with imbalanced data (should still work but might have lower F1)."""
    # Create highly imbalanced labels
    X, labels_df, features_path, labels_path, output_path = sample_data
    
    # Modify labels to be highly imbalanced (90% valid, 10% invalid)
    labels_df.loc[labels_df['label'] == 'invalid', 'label'] = 'valid'
    # Ensure we still have at least some invalids
    labels_df.loc[labels_df['clip_id'] == 'clip_0', 'label'] = 'invalid'
    labels_df.loc[labels_df['clip_id'] == 'clip_1', 'label'] = 'invalid'
    
    labels_df.to_csv(labels_path, index=False)
    
    X_loaded, y_loaded, _ = load_filtered_data(features_path, labels_path)
    
    # Should still train
    result = train_model(X_loaded, y_loaded, model_type="random_forest", output_path=output_path)
    
    assert 'model' in result
    assert result['test_f1'] >= 0.0  # F1 should be non-negative
    
    # Check that stats file was created
    stats_path = output_path.with_suffix('.json')
    assert stats_path.exists()
    
    with open(stats_path, 'r') as f:
        stats = json.load(f)
    
    assert 'test_f1' in stats
    assert 'best_params' in stats
