import pytest
import json
import os
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from code.model_training import (
    get_memory_usage_mb,
    check_memory_pressure,
    profile_memory_usage,
    force_gc,
    load_feature_matrix,
    load_model,
    train_random_forest,
    run_cross_validation,
    log_cv_metrics,
    calculate_permutation_importance,
    rank_traits,
    save_model,
    save_metrics,
    run_training_pipeline,
    run_full_training_and_save
)
from code.config import get_results_root

@pytest.fixture
def sample_feature_matrix(tmp_path):
    """Create a sample feature matrix for testing."""
    # Create a small dataset with 20 samples, 5 features, 1 target
    np.random.seed(42)
    n_samples = 20
    n_features = 5
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'trait_{i}' for i in range(n_features)]
    )
    y = pd.Series(np.random.randint(0, 2, n_samples))
    
    # Save to CSV
    df = pd.concat([X, y], axis=1)
    df.columns = list(X.columns) + ['link_label']
    output_path = tmp_path / "feature_matrix.csv"
    df.to_csv(output_path, index=False)
    return output_path

@pytest.fixture
def mock_cv_results():
    """Mock CV metrics for testing log_cv_metrics."""
    return {
        'auc_mean': 0.85,
        'auc_std': 0.05,
        'precision_mean': 0.82,
        'recall_mean': 0.78
    }

class TestMemoryFunctions:
    def test_get_memory_usage_mb(self):
        """Test memory usage function returns a positive number."""
        mem = get_memory_usage_mb()
        assert isinstance(mem, float)
        assert mem >= 0

    def test_check_memory_pressure(self):
        """Test memory pressure check."""
        # Should not raise
        result = check_memory_pressure(threshold_mb=10000)
        assert isinstance(result, bool)

    def test_force_gc(self):
        """Test that force_gc runs without error."""
        force_gc()  # Should not raise

class TestModelTraining:
    def test_train_random_forest(self, sample_feature_matrix, tmp_path):
        """Test training a random forest model."""
        # Load data
        df = pd.read_csv(sample_feature_matrix)
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]
        
        # Train
        model = train_random_forest(X, y)
        
        # Verify
        assert model is not None
        assert hasattr(model, 'predict')
        assert model.n_estimators == 100  # Default

    def test_run_cross_validation(self, sample_feature_matrix):
        """Test cross-validation returns expected metrics."""
        df = pd.read_csv(sample_feature_matrix)
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]
        
        metrics = run_cross_validation(X, y, n_splits=3)
        
        # Check required keys
        assert 'auc_mean' in metrics
        assert 'auc_std' in metrics
        assert 'precision_mean' in metrics
        assert 'recall_mean' in metrics
        
        # Check types
        assert isinstance(metrics['auc_mean'], float)
        assert isinstance(metrics['auc_std'], float)

class TestLogCvMetrics:
    def test_log_cv_metrics_creates_file(self, mock_cv_results, tmp_path):
        """Test that log_cv_metrics creates a JSON file with correct keys."""
        output_path = tmp_path / "test_metrics.json"
        
        log_cv_metrics(mock_cv_results, str(output_path))
        
        # Verify file exists
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['auc_mean'] == 0.85
        assert data['auc_std'] == 0.05
        assert data['precision_mean'] == 0.82
        assert data['recall_mean'] == 0.78
        assert 'timestamp' in data
        assert data['task_id'] == 'T027'

    def test_log_cv_metrics_missing_key_raises(self, tmp_path):
        """Test that missing required keys raises an error."""
        incomplete_metrics = {
            'auc_mean': 0.85,
            # Missing other required keys
        }
        
        output_path = tmp_path / "test_metrics.json"
        
        with pytest.raises(ValueError, match="Missing required metric key"):
            log_cv_metrics(incomplete_metrics, str(output_path))

class TestImportance:
    def test_calculate_permutation_importance(self, sample_feature_matrix):
        """Test permutation importance calculation."""
        df = pd.read_csv(sample_feature_matrix)
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]
        
        model = train_random_forest(X, y)
        importance_df = calculate_permutation_importance(model, X, y, n_repeats=2)
        
        assert isinstance(importance_df, pd.DataFrame)
        assert 'feature' in importance_df.columns
        assert 'importance_mean' in importance_df.columns
        assert len(importance_df) == len(X.columns)

    def test_rank_traits(self, sample_feature_matrix):
        """Test trait ranking."""
        df = pd.read_csv(sample_feature_matrix)
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]
        
        model = train_random_forest(X, y)
        importance_df = calculate_permutation_importance(model, X, y, n_repeats=2)
        
        top_traits = rank_traits(importance_df, top_n=3)
        
        assert isinstance(top_traits, list)
        assert len(top_traits) == 3
        assert all(isinstance(t, str) for t in top_traits)

class TestIntegration:
    def test_run_training_pipeline(self, sample_feature_matrix, tmp_path):
        """Test the full training pipeline."""
        df = pd.read_csv(sample_feature_matrix)
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]
        
        metrics = run_training_pipeline(X, y, n_splits=3)
        
        assert 'auc_mean' in metrics
        assert metrics['auc_mean'] > 0  # Should be a valid score
        
        # Check that metrics file was created in tmp_path (mocked results root)
        # Note: In a real test, we'd need to mock get_results_root()
        # For now, we just verify the function returns metrics

if __name__ == "__main__":
    pytest.main([__file__, "-v"])