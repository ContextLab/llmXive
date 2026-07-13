"""
Unit tests for XGBoost trainer module.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.xgboost_trainer import XGBoostTrainer
from utils.error_handlers import ModelTrainingError, DataValidationError


@pytest.fixture
def sample_data():
    """Create a small sample dataset for testing."""
    np.random.seed(42)
    n_samples = 50
    data = {
        'element_A': np.random.rand(n_samples),
        'element_B': np.random.rand(n_samples),
        'element_C': np.random.rand(n_samples),
        'hardness_hv': np.random.rand(n_samples) * 100
    }
    # Normalize composition to sum to 1
    total = data['element_A'] + data['element_B'] + data['element_C']
    data['element_A'] /= total
    data['element_B'] /= total
    data['element_C'] /= total
    return pd.DataFrame(data)


@pytest.fixture
def temp_data_dir(sample_data):
    """Create a temporary directory with sample data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir) / "solder_hardness_validated.csv"
        sample_data.to_csv(data_path, index=False)
        yield data_path


def test_trainer_initialization():
    """Test that trainer initializes correctly."""
    trainer = XGBoostTrainer(seed=42, cv_folds=3)
    assert trainer.seed == 42
    assert trainer.cv_folds == 3
    assert trainer.model is None


def test_load_data_success(temp_data_dir):
    """Test successful data loading."""
    trainer = XGBoostTrainer()
    df = trainer.load_data(temp_data_dir)
    assert len(df) == 50
    assert 'hardness_hv' in df.columns
    assert 'element_A' in df.columns


def test_load_data_not_found():
    """Test error when data file not found."""
    trainer = XGBoostTrainer()
    with pytest.raises(DataValidationError):
        trainer.load_data(Path("/nonexistent/path.csv"))


def test_prepare_features(sample_data):
    """Test feature preparation."""
    trainer = XGBoostTrainer()
    trainer.target_col = 'hardness_hv'
    X, y = trainer.prepare_features(sample_data)
    assert X.shape[0] == 50
    assert X.shape[1] == 3
    assert y.shape[0] == 50
    assert len(trainer.feature_names) == 3


def test_train_model_flow(sample_data, temp_data_dir):
    """Test the full training flow."""
    trainer = XGBoostTrainer(seed=42, cv_folds=3)
    trainer.load_data(temp_data_dir)
    X, y = trainer.prepare_features(sample_data)

    # Mock the grid search to speed up test
    with patch.object(trainer, 'tune_hyperparameters') as mock_tune:
        mock_tune.return_value = {
            'n_estimators': 10,
            'max_depth': 3,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'objective': 'reg:squarederror',
            'random_state': 42,
            'n_jobs': -1,
            'verbosity': 0
        }
        params = trainer.tune_hyperparameters(X, y)
        trainer.train_model(X, y, params)
        
        assert trainer.model is not None
        assert hasattr(trainer, 'best_params')


def test_save_model(temp_data_dir, sample_data):
    """Test model saving."""
    trainer = XGBoostTrainer(seed=42, cv_folds=3)
    trainer.load_data(temp_data_dir)
    X, y = trainer.prepare_features(sample_data)

    # Mock tuning and training
    with patch.object(trainer, 'tune_hyperparameters') as mock_tune:
        mock_tune.return_value = {
            'n_estimators': 5,
            'max_depth': 2,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'objective': 'reg:squarederror',
            'random_state': 42,
            'n_jobs': -1,
            'verbosity': 0
        }
        params = trainer.tune_hyperparameters(X, y)
        trainer.train_model(X, y, params)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = trainer.save_model(Path(tmpdir))
            assert (output_dir / "xgboost_hardness_model.json").exists()
            assert (output_dir / "xgboost_training_metadata.json").exists()


def test_get_feature_importance(temp_data_dir, sample_data):
    """Test feature importance retrieval."""
    trainer = XGBoostTrainer(seed=42, cv_folds=3)
    trainer.load_data(temp_data_dir)
    X, y = trainer.prepare_features(sample_data)

    # Mock training
    with patch.object(trainer, 'tune_hyperparameters') as mock_tune:
        mock_tune.return_value = {
            'n_estimators': 5,
            'max_depth': 2,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'objective': 'reg:squarederror',
            'random_state': 42,
            'n_jobs': -1,
            'verbosity': 0
        }
        params = trainer.tune_hyperparameters(X, y)
        trainer.train_model(X, y, params)

        importance_df = trainer.get_feature_importance()
        assert 'feature' in importance_df.columns
        assert 'importance' in importance_df.columns
        assert len(importance_df) == 3


def test_evaluate_model(temp_data_dir, sample_data):
    """Test model evaluation."""
    trainer = XGBoostTrainer(seed=42, cv_folds=3)
    trainer.load_data(temp_data_dir)
    X, y = trainer.prepare_features(sample_data)

    # Mock training
    with patch.object(trainer, 'tune_hyperparameters') as mock_tune:
        mock_tune.return_value = {
            'n_estimators': 5,
            'max_depth': 2,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'objective': 'reg:squarederror',
            'random_state': 42,
            'n_jobs': -1,
            'verbosity': 0
        }
        params = trainer.tune_hyperparameters(X, y)
        trainer.train_model(X, y, params)

        metrics = trainer.evaluate_model(X, y)
        assert 'cv_r2_mean' in metrics
        assert 'cv_rmse_mean' in metrics
        assert metrics['cv_folds'] == 3


def test_no_model_error(sample_data):
    """Test error when operations are performed on untrained model."""
    trainer = XGBoostTrainer()
    trainer.load_data(Path("/tmp/fake.csv")) if False else None  # Skip actual load
    
    with pytest.raises(ModelTrainingError):
        trainer.evaluate_model(sample_data.drop(columns=['hardness_hv']), 
                             sample_data['hardness_hv'])

    with pytest.raises(ModelTrainingError):
        trainer.get_feature_importance()

    with pytest.raises(ModelTrainingError):
        trainer.save_model()