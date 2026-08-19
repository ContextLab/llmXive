"""
Tests for the model training module (src/models/train.py).
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from sklearn.linear_model import LogisticRegression

from src.models.train import (
    calculate_vif, 
    run_vif_selection, 
    train_l1_logistic_regression, 
    train_model_fold, 
    save_model, 
    load_model
)

@pytest.fixture
def sample_features():
    """Generate a sample feature DataFrame with some multicollinearity."""
    np.random.seed(42)
    n = 100
    # Create correlated features
    f1 = np.random.randn(n)
    f2 = f1 * 0.9 + np.random.randn(n) * 0.1  # Highly correlated with f1
    f3 = np.random.randn(n)
    f4 = np.random.randn(n)
    f5 = f3 * 0.8 + np.random.randn(n) * 0.2  # Correlated with f3
    
    df = pd.DataFrame({
        'f1': f1,
        'f2': f2,
        'f3': f3,
        'f4': f4,
        'f5': f5
    })
    return df

@pytest.fixture
def sample_labels():
    """Generate sample binary labels."""
    np.random.seed(42)
    return pd.Series(np.random.randint(0, 2, 100))

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_calculate_vif_basic(sample_features):
    """Test that VIF is calculated correctly for a basic set."""
    vif_dict = calculate_vif(sample_features)
    assert isinstance(vif_dict, dict)
    assert len(vif_dict) == 5
    # f1 and f2 are correlated, so their VIF should be > 1
    assert vif_dict['f1'] > 1.0
    assert vif_dict['f2'] > 1.0
    # f4 is independent, VIF should be close to 1
    assert 1.0 <= vif_dict['f4'] < 1.5

def test_run_vif_selection_reduces_features(sample_features, sample_labels, temp_output_dir):
    """Test that VIF selection removes correlated features."""
    # Set a low threshold to force removal
    reduced_X, kept_features, final_vif = run_vif_selection(sample_features, threshold=2.0)
    
    assert isinstance(kept_features, list)
    assert len(kept_features) < 5 # Should have removed some
    assert reduced_X.shape[1] == len(kept_features)
    
    # Check that no kept feature has VIF >= 2.0
    for f in kept_features:
        assert final_vif[f] < 2.0

def test_run_vif_selection_empty_threshold(sample_features):
    """Test VIF selection with threshold=0 (removes everything)."""
    reduced_X, kept_features, _ = run_vif_selection(sample_features, threshold=0.0)
    # With threshold 0, everything is removed (VIF is always >= 1)
    # Actually, if VIF < 0 is impossible, all are removed.
    # But our logic stops when no features >= threshold. 
    # If threshold is 0, and VIF is always >= 1, all are removed.
    assert len(kept_features) == 0

def test_train_l1_logistic_regression_basic(sample_features, sample_labels):
    """Test basic training of L1 logistic regression."""
    # First reduce features to ensure no errors
    reduced_X, kept_features, _ = run_vif_selection(sample_features, threshold=10.0)
    if len(kept_features) == 0:
        # If all removed, add one back for test validity
        reduced_X = sample_features[['f4']]
        kept_features = ['f4']
    
    model = train_l1_logistic_regression(reduced_X, sample_labels)
    
    assert isinstance(model, LogisticRegression)
    assert model.penalty == 'l1'
    assert model.solver == 'liblinear'
    assert hasattr(model, 'coef_')

def test_train_l1_logistic_regression_no_features_left(sample_labels):
    """Test training fails when no features are left."""
    empty_X = pd.DataFrame(index=range(100))
    with pytest.raises(ValueError, match="No features remaining"):
        train_l1_logistic_regression(empty_X, sample_labels)

def test_train_model_fold(sample_features, sample_labels, temp_output_dir):
    """Test the full fold training pipeline including file saving."""
    model, kept_features = train_model_fold(
        sample_features, 
        sample_labels, 
        fold_idx=0, 
        vif_threshold=10.0, 
        output_dir=temp_output_dir
    )
    
    assert isinstance(model, LogisticRegression)
    assert isinstance(kept_features, list)
    
    # Check file was created
    file_path = Path(temp_output_dir) / "vif_filtered_features_fold_0.csv"
    assert file_path.exists()
    
    # Check content
    df = pd.read_csv(file_path)
    assert 'feature' in df.columns
    assert len(df) == len(kept_features)

def test_save_and_load_model(sample_features, sample_labels, temp_output_dir):
    """Test saving and loading a model."""
    reduced_X, kept_features, _ = run_vif_selection(sample_features, threshold=10.0)
    if len(kept_features) == 0:
        reduced_X = sample_features[['f4']]
    
    model = train_l1_logistic_regression(reduced_X, sample_labels)
    
    model_path = Path(temp_output_dir) / "test_model.pkl"
    save_model(model, model_path)
    
    assert model_path.exists()
    
    loaded_model = load_model(model_path)
    
    assert isinstance(loaded_model, LogisticRegression)
    np.testing.assert_array_equal(model.coef_, loaded_model.coef_)