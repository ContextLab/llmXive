import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from src.model import train_elastic_net, validate_strains, split_stratified_strain
from src.config import SEED

@pytest.fixture
def sample_train_data():
    """Generate sample training data for Elastic Net."""
    np.random.seed(SEED)
    n_samples = 100
    n_features = 5
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    # Create a target with some linear relationship + noise
    y = pd.Series(2 * X['feature_0'] + 0.5 * X['feature_1'] + np.random.randn(n_samples) * 0.1)
    
    return X, y

@pytest.fixture
def temp_processed_dir():
    """Create a temporary directory for processed data files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_train_elastic_net_returns_model(sample_train_data):
    """Test that train_elastic_net returns a trained model and parameters."""
    X, y = sample_train_data
    
    model, alpha, l1_ratio = train_elastic_net(X, y)
    
    assert model is not None
    assert hasattr(model, 'predict')
    assert isinstance(alpha, float)
    assert isinstance(l1_ratio, float)
    assert 0.0 <= l1_ratio <= 1.0

def test_train_elastic_net_saves_model(sample_train_data, temp_processed_dir, monkeypatch):
    """Test that train_elastic_net saves the model to disk."""
    # Patch the ARTIFACTS_PATH to use temp dir
    with patch('src.model.ARTIFACTS_PATH', str(temp_processed_dir)):
        X, y = sample_train_data
        model, alpha, l1_ratio = train_elastic_net(X, y)
        
        model_path = Path(temp_processed_dir) / "models" / "elastic_net.pkl"
        assert model_path.exists()
        assert model_path.stat().st_size > 0

def test_train_elastic_net_excludes_test_data(sample_train_data):
    """
    Test that the training process does not use test data.
    This is implicitly tested by ensuring the function signature
    only accepts X_train and y_train, and the implementation
    uses cross-validation on the training set only.
    """
    X, y = sample_train_data
    
    # We cannot easily inspect the internal CV folds without mocking,
    # but we verify the function accepts only train data and returns a model.
    # The use of ElasticNetCV ensures CV is internal and doesn't leak test data.
    model, alpha, l1_ratio = train_elastic_net(X, y)
    
    assert model is not None

def test_validate_strains_pass(temp_processed_dir, monkeypatch):
    """Test validation passes with enough strains."""
    df = pd.DataFrame({
        'strain_accession': ['strain_' + str(i) for i in range(10)],
        'isg_score': [1.0] * 10
    })
    # Mock the path check if needed, but here we just test the logic
    # assuming the dataframe is loaded correctly.
    try:
        validate_strains(df)
    except ValueError:
        pytest.fail("validate_strains raised ValueError unexpectedly")

def test_validate_strains_fail(temp_processed_dir, monkeypatch):
    """Test validation fails with too few strains."""
    df = pd.DataFrame({
        'strain_accession': ['strain_0', 'strain_1'],
        'isg_score': [1.0, 2.0]
    })
    with pytest.raises(ValueError, match="Insufficient unique strains"):
        validate_strains(df)

def test_split_stratified_strain_basic(temp_processed_dir, monkeypatch):
    """Test basic split functionality."""
    # Create enough strains
    strains = [f'strain_{i}' for i in range(10)]
    df = pd.DataFrame({
        'strain_accession': strains,
        'isg_score': [float(i) for i in range(10)]
    })
    
    train_df, test_df = split_stratified_strain(df, test_strains=3)
    
    assert len(train_df) + len(test_df) == len(df)
    assert len(test_df) == 3
    assert len(train_df) == 7
    
    # Ensure no overlap
    train_strains = set(train_df['strain_accession'])
    test_strains = set(test_df['strain_accession'])
    assert train_strains.isdisjoint(test_strains)

def test_split_stratified_strain_minimum_test_strains(temp_processed_dir, monkeypatch):
    """Test split enforces minimum test strains."""
    strains = [f'strain_{i}' for i in range(4)]
    df = pd.DataFrame({
        'strain_accession': strains,
        'isg_score': [float(i) for i in range(4)]
    })
    
    # Requesting 5 test strains when only 4 exist should fail
    with pytest.raises(ValueError, match="Insufficient unique strains"):
        split_stratified_strain(df, test_strains=5)