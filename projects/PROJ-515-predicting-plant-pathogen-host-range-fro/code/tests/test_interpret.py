"""
Tests for SHAP interpretation module.
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from sklearn.linear_model import LogisticRegression

from src.models.interpret import (
    calculate_shap_values,
    generate_feature_importance_report,
    run_shap_analysis
)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_model_and_data():
    """Create a simple trained logistic regression model and sample data."""
    # Create sample data
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    
    X = np.random.randn(n_samples, n_features)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    
    # Train a simple model
    model = LogisticRegression(penalty='l1', solver='liblinear', random_state=42)
    model.fit(X, y)
    
    feature_names = [f"feature_{i}" for i in range(n_features)]
    feature_df = pd.DataFrame(X, columns=feature_names)
    
    return model, feature_df, feature_names


def test_calculate_shap_values_basic(sample_model_and_data):
    """Test basic SHAP value calculation."""
    model, feature_df, feature_names = sample_model_and_data
    
    shap_values, base_values, names = calculate_shap_values(
        model, 
        feature_df, 
        feature_names
    )
    
    assert shap_values is not None
    assert shap_values.shape[0] == len(feature_df)
    assert shap_values.shape[1] == len(feature_names)
    assert names == feature_names
    assert base_values is not None


def test_generate_feature_importance_report(temp_output_dir, sample_model_and_data):
    """Test feature importance report generation."""
    model, feature_df, feature_names = sample_model_and_data
    
    shap_values, _, _ = calculate_shap_values(model, feature_df, feature_names)
    
    output_path = temp_output_dir / "feature_importance.csv"
    importance_df = generate_feature_importance_report(
        shap_values, 
        feature_names, 
        output_path
    )
    
    # Check file exists
    assert output_path.exists()
    
    # Check DataFrame structure
    assert 'feature_name' in importance_df.columns
    assert 'mean_abs_shap' in importance_df.columns
    assert 'mean_shap' in importance_df.columns
    assert 'std_shap' in importance_df.columns
    
    # Check sorting (descending by mean_abs_shap)
    assert importance_df['mean_abs_shap'].is_monotonic_decreasing
    
    # Check all features are present
    assert len(importance_df) == len(feature_names)


def test_run_shap_analysis_integration(temp_output_dir, sample_model_and_data):
    """Test the full SHAP analysis pipeline."""
    model, feature_df, feature_names = sample_model_and_data
    
    # Save model
    model_path = temp_output_dir / "model.pkl"
    import joblib
    joblib.dump(model, model_path)
    
    # Save features
    features_path = temp_output_dir / "features.csv"
    feature_df.to_csv(features_path, index=False)
    
    # Output path
    output_path = temp_output_dir / "importance.csv"
    
    # Run analysis
    result_df = run_shap_analysis(
        model_path=str(model_path),
        feature_matrix_path=str(features_path),
        output_path=str(output_path),
        n_samples=50
    )
    
    # Verify results
    assert output_path.exists()
    assert len(result_df) == len(feature_names)
    assert result_df['mean_abs_shap'].max() > 0
    assert 'feature_name' in result_df.columns