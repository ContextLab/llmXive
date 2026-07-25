"""
Unit tests for the modeling pipeline.
Tests nested CV logic and alpha tuning on synthetic data.
"""
import os
import sys
import json
import tempfile
import pytest
import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.modeling import (
    load_cleaned_data,
    prepare_features_targets,
    run_nested_cv_ridge,
    run_primary_modeling_pipeline
)
from code.utils import write_csv, write_json


def create_test_data(n_samples=100, correlation=0.3):
    """
    Create synthetic test data with known correlation structure.
    
    Args:
        n_samples: Number of samples
        correlation: Target correlation between Global_Signal_SD and MWQ_Score
        
    Returns:
        DataFrame with test data
    """
    np.random.seed(42)
    
    # Generate features
    global_signal_sd = np.random.randn(n_samples)
    mean_fd = np.random.randn(n_samples) * 0.1 + 0.3
    mean_dvars = np.random.randn(n_samples) * 0.1 + 0.5
    age = np.random.randint(18, 65, n_samples)
    sex = np.random.choice([0, 1], n_samples)
    
    # Generate target with known correlation
    # MWQ = a * Global_Signal_SD + noise
    noise = np.random.randn(n_samples) * (1 - correlation)
    mwq_score = correlation * global_signal_sd + noise
    
    # Normalize MWQ to reasonable range (0-100 scale)
    mwq_score = (mwq_score - mwq_score.min()) / (mwq_score.max() - mwq_score.min()) * 100
    
    df = pd.DataFrame({
        'Subject_ID': [f'sub-{i:03d}' for i in range(n_samples)],
        'Global_Signal_SD': global_signal_sd,
        'MWQ_Score': mwq_score,
        'Age': age,
        'Sex': sex,
        'Mean_FD': mean_fd,
        'Mean_DVARS': mean_dvars
    })
    
    return df


class TestLoadCleanedData:
    def test_load_existing_file(self, tmp_path):
        """Test loading an existing cleaned data file."""
        # Create test data
        df = create_test_data(n_samples=50)
        data_path = tmp_path / "cleaned_data.csv"
        df.to_csv(data_path, index=False)
        
        # Load and verify
        loaded_df = load_cleaned_data(str(data_path))
        
        assert len(loaded_df) == 50
        assert 'Subject_ID' in loaded_df.columns
        assert 'MWQ_Score' in loaded_df.columns
        assert 'Global_Signal_SD' in loaded_df.columns
    
    def test_missing_file_raises_error(self, tmp_path):
        """Test that loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_cleaned_data(str(tmp_path / "nonexistent.csv"))
    
    def test_missing_columns_raises_error(self, tmp_path):
        """Test that missing required columns raises ValueError."""
        df = pd.DataFrame({'Subject_ID': [1, 2], 'Other': [3, 4]})
        data_path = tmp_path / "incomplete.csv"
        df.to_csv(data_path, index=False)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            load_cleaned_data(str(data_path))


class TestPrepareFeaturesTargets:
    def test_feature_extraction(self):
        """Test that features are correctly extracted."""
        df = create_test_data(n_samples=30)
        
        X, y, feature_names = prepare_features_targets(df)
        
        assert X.shape == (30, 5)
        assert y.shape == (30,)
        assert len(feature_names) == 5
        assert 'Global_Signal_SD' in feature_names
        assert 'Mean_FD' in feature_names
    
    def test_sex_conversion(self):
        """Test that string sex values are converted to numeric."""
        df = create_test_data(n_samples=30)
        df['Sex'] = ['F', 'M'] * 15
        
        X, y, feature_names = prepare_features_targets(df)
        
        # Sex should be converted to 0/1
        assert X[:, 4].dtype in [np.int64, np.int32, np.float64]
        assert set(np.unique(X[:, 4])).issubset({0, 1})


class TestNestedCVRidge:
    def test_nested_cv_runs(self):
        """Test that nested CV completes without errors."""
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        
        results = run_nested_cv_ridge(X, y, n_splits_outer=3, n_splits_inner=2)
        
        assert 'mean_mae' in results
        assert 'mean_r2' in results
        assert 'mean_pearson_r' in results
        assert 'best_alphas' in results
        assert len(results['best_alphas']) == 3
    
    def test_known_correlation_recovery(self):
        """Test that nested CV recovers known correlation in synthetic data."""
        # Create data with known correlation
        df = create_test_data(n_samples=200, correlation=0.3)
        X, y, _ = prepare_features_targets(df)
        
        # Run nested CV
        results = run_nested_cv_ridge(X, y, n_splits_outer=5, n_splits_inner=3)
        
        # Pearson r should be in reasonable range (allowing for variance)
        assert 0.15 <= results['mean_pearson_r'] <= 0.45, \
            f"Expected r around 0.3, got {results['mean_pearson_r']}"
    
    def test_out_of_fold_predictions(self):
        """Test that out-of-fold predictions are generated correctly."""
        X = np.random.randn(50, 5)
        y = np.random.randn(50)
        
        results = run_nested_cv_ridge(X, y, n_splits_outer=5, n_splits_inner=2)
        
        assert 'predictions' in results
        assert 'true_values' in results
        assert len(results['predictions']) == len(y)
        assert len(results['true_values']) == len(y)
        assert np.allclose(results['predictions'], results['predictions'])  # No NaNs


class TestPrimaryModelingPipeline:
    def test_full_pipeline(self, tmp_path):
        """Test the complete modeling pipeline."""
        # Create test data
        df = create_test_data(n_samples=100)
        data_path = tmp_path / "cleaned_data.csv"
        df.to_csv(data_path, index=False)
        
        output_path = tmp_path / "results" / "model_results.json"
        
        # Run pipeline
        results = run_primary_modeling_pipeline(str(data_path), str(output_path))
        
        # Verify output file exists
        assert os.path.exists(output_path)
        
        # Verify results structure
        assert 'mean_mae' in results
        assert 'mean_r2' in results
        assert 'mean_pearson_r' in results
        assert 'feature_names' in results
        assert results['n_samples'] == 100
    
    def test_output_json_valid(self, tmp_path):
        """Test that output JSON is valid and parseable."""
        df = create_test_data(n_samples=50)
        data_path = tmp_path / "cleaned_data.csv"
        df.to_csv(data_path, index=False)
        
        output_path = tmp_path / "results" / "model_results.json"
        
        run_primary_modeling_pipeline(str(data_path), str(output_path))
        
        # Verify JSON is valid
        with open(output_path, 'r') as f:
            loaded_results = json.load(f)
        
        assert 'mean_mae' in loaded_results
        assert isinstance(loaded_results['mean_mae'], float)


class TestEdgeCases:
    def test_small_sample_size(self):
        """Test with very small sample size."""
        X = np.random.randn(10, 3)
        y = np.random.randn(10)
        
        # Should handle small samples (though results may be unstable)
        results = run_nested_cv_ridge(X, y, n_splits_outer=2, n_splits_inner=2)
        
        assert results['n_samples'] == 10
    
    def test_high_dimensional_features(self):
        """Test with more features than samples (should still run, may overfit)."""
        X = np.random.randn(20, 15)
        y = np.random.randn(20)
        
        results = run_nested_cv_ridge(X, y, n_splits_outer=2, n_splits_inner=2)
        
        assert results['n_features'] == 15
        assert results['n_samples'] == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])