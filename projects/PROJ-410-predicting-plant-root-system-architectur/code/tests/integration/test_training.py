"""
Integration tests for the training pipeline.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile

# Import functions from the training module
from train import load_split_data, train_model, evaluate_model, run_training_loop

@pytest.fixture
def mock_split_data(tmp_path):
    """Create mock split data files for integration testing."""
    # Create mock train/val/test datasets
    train_data = pd.DataFrame({
        'accession': [f'Col-{i}' for i in range(100)],
        'phenotype': np.random.randn(100) * 10 + 50,
        'nutrient_condition': ['low_N'] * 50 + ['high_N'] * 50,
        'SNP1': np.random.randint(0, 3, 100),
        'SNP2': np.random.randint(0, 3, 100),
        'SNP3': np.random.randint(0, 3, 100)
    })
    
    val_data = pd.DataFrame({
        'accession': [f'Ler-{i}' for i in range(20)],
        'phenotype': np.random.randn(20) * 10 + 50,
        'nutrient_condition': ['low_N'] * 10 + ['high_N'] * 10,
        'SNP1': np.random.randint(0, 3, 20),
        'SNP2': np.random.randint(0, 3, 20),
        'SNP3': np.random.randint(0, 3, 20)
    })
    
    test_data = pd.DataFrame({
        'accession': [f'Ws-{i}' for i in range(20)],
        'phenotype': np.random.randn(20) * 10 + 50,
        'nutrient_condition': ['low_N'] * 10 + ['high_N'] * 10,
        'SNP1': np.random.randint(0, 3, 20),
        'SNP2': np.random.randint(0, 3, 20),
        'SNP3': np.random.randint(0, 3, 20)
    })
    
    # Save to temporary directory
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    train_path = data_dir / "train.parquet"
    val_path = data_dir / "val.parquet"
    test_path = data_dir / "test.parquet"
    
    train_data.to_parquet(train_path)
    val_data.to_parquet(val_path)
    test_data.to_parquet(test_path)
    
    return {
        'train': train_path,
        'val': val_path,
        'test': test_path,
        'data_dir': data_dir
    }

def test_load_split_data(mock_split_data):
    """Test loading split data from parquet files."""
    train_df, val_df, test_df = load_split_data(mock_split_data['data_dir'])
    
    assert len(train_df) == 100
    assert len(val_df) == 20
    assert len(test_df) == 20
    assert 'phenotype' in train_df.columns
    assert 'nutrient_condition' in train_df.columns

def test_train_model_linear(mock_split_data):
    """Test training a linear model."""
    train_df, _, _ = load_split_data(mock_split_data['data_dir'])
    
    # Train a simple linear model
    model = train_model(
        train_df,
        model_type='linear',
        feature_cols=['SNP1', 'SNP2', 'SNP3'],
        target_col='phenotype',
        condition_col='nutrient_condition'
    )
    
    assert model is not None
    assert hasattr(model, 'coef_')

def test_train_model_rf(mock_split_data):
    """Test training a random forest model."""
    train_df, _, _ = load_split_data(mock_split_data['data_dir'])
    
    model = train_model(
        train_df,
        model_type='rf',
        feature_cols=['SNP1', 'SNP2', 'SNP3'],
        target_col='phenotype',
        condition_col='nutrient_condition'
    )
    
    assert model is not None
    assert hasattr(model, 'feature_importances_')

def test_evaluate_model(mock_split_data):
    """Test evaluating a trained model."""
    train_df, val_df, _ = load_split_data(mock_split_data['data_dir'])
    
    model = train_model(
        train_df,
        model_type='linear',
        feature_cols=['SNP1', 'SNP2', 'SNP3'],
        target_col='phenotype',
        condition_col='nutrient_condition'
    )
    
    metrics = evaluate_model(model, val_df, feature_cols=['SNP1', 'SNP2', 'SNP3'], target_col='phenotype')
    
    assert 'r2' in metrics
    assert 'mae' in metrics
    assert 'rmse' in metrics
    assert isinstance(metrics['r2'], float)

def test_run_training_loop(mock_split_data):
    """Test the full training loop for all models."""
    # Run training for all models
    results = run_training_loop(
        data_dir=mock_split_data['data_dir'],
        model_types=['linear', 'rf'],
        feature_cols=['SNP1', 'SNP2', 'SNP3'],
        target_col='phenotype',
        condition_col='nutrient_condition'
    )
    
    assert results is not None
    assert len(results) > 0
    
    # Check that results contain expected keys
    for model_type, metrics in results.items():
        assert 'r2' in metrics
        assert 'mae' in metrics
        assert 'rmse' in metrics
