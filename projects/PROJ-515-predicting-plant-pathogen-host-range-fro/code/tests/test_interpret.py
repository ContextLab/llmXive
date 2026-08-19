"""
Tests for the interpret module (SHAP value generation and feature importance).

Tests cover:
- SHAP value calculation
- Feature importance report generation
- Integration of SHAP analysis pipeline
"""

import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Import the module under test
from src.models.interpret import (
    calculate_shap_values,
    generate_feature_importance_report,
    run_shap_analysis,
    generate_bias_awareness_report
)

# Import training utilities for test setup
from src.models.train import train_l1_logistic_regression, save_model


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_model_and_data():
    """Create a sample trained model and feature matrix for testing."""
    # Create sample data
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    
    X = np.random.randn(n_samples, n_features)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    
    # Create feature names
    feature_names = [f'feature_{i}' for i in range(n_features)]
    X_df = pd.DataFrame(X, columns=feature_names)
    
    # Train a simple model
    model = train_l1_logistic_regression(X_df, y)
    
    return {
        'model': model,
        'X': X_df,
        'y': y,
        'feature_names': feature_names
    }


def test_calculate_shap_values_basic(sample_model_and_data, temp_output_dir):
    """Test basic SHAP value calculation."""
    model = sample_model_and_data['model']
    X = sample_model_and_data['X']
    feature_names = sample_model_and_data['feature_names']
    
    # Calculate SHAP values
    shap_values, expected_value = calculate_shap_values(model, X, feature_names)
    
    # Assertions
    assert shap_values is not None
    assert isinstance(shap_values, np.ndarray)
    assert shap_values.shape == (len(X), len(feature_names))
    assert expected_value is not None
    assert isinstance(expected_value, (int, float, np.number))
    
    # Check that SHAP values have reasonable magnitude
    assert np.all(np.isfinite(shap_values))
    assert np.abs(expected_value) < 10  # Should be a reasonable value


def test_generate_feature_importance_report(sample_model_and_data, temp_output_dir):
    """Test feature importance report generation."""
    model = sample_model_and_data['model']
    X = sample_model_and_data['X']
    feature_names = sample_model_and_data['feature_names']
    
    # Calculate SHAP values first
    shap_values, _ = calculate_shap_values(model, X, feature_names)
    
    # Generate report
    output_path = temp_output_dir / "feature_importance.csv"
    summary = generate_feature_importance_report(shap_values, feature_names, output_path)
    
    # Assertions
    assert output_path.exists(), "Feature importance CSV should be created"
    
    # Check CSV content
    df = pd.read_csv(output_path)
    assert 'feature_name' in df.columns
    assert 'mean_abs_shap' in df.columns
    assert len(df) == len(feature_names)
    
    # Check that features are sorted by mean_abs_shap (descending)
    assert df['mean_abs_shap'].is_monotonic_decreasing
    
    # Check summary
    assert 'total_features' in summary
    assert summary['total_features'] == len(feature_names)
    assert 'top_features' in summary
    assert len(summary['top_features']) <= 20  # Default top_n
    
    # Check JSON summary file
    json_path = output_path.with_suffix('.json')
    assert json_path.exists(), "Feature importance JSON should be created"
    
    with open(json_path, 'r') as f:
        json_summary = json.load(f)
    
    assert json_summary == summary


def test_run_shap_analysis_integration(sample_model_and_data, temp_output_dir):
    """Test complete SHAP analysis pipeline."""
    model = sample_model_and_data['model']
    X = sample_model_and_data['X']
    feature_names = sample_model_and_data['feature_names']
    
    # Save model
    model_path = temp_output_dir / "model.pkl"
    save_model(model, model_path)
    
    # Save feature matrix
    features_path = temp_output_dir / "features.csv"
    X.to_csv(features_path, index=False)
    
    # Run SHAP analysis
    result = run_shap_analysis(
        model_path=str(model_path),
        feature_matrix_path=str(features_path),
        output_dir=temp_output_dir,
        top_n=5
    )
    
    # Assertions
    assert 'report_path' in result
    assert 'diagnostics_path' in result
    assert 'summary' in result
    assert 'diagnostics' in result
    
    # Check files were created
    assert Path(result['report_path']).exists()
    assert Path(result['diagnostics_path']).exists()
    
    # Check report content
    report_df = pd.read_csv(result['report_path'])
    assert len(report_df) == len(feature_names)
    assert 'feature_name' in report_df.columns
    assert 'mean_abs_shap' in report_df.columns


def test_generate_bias_awareness_report(temp_output_dir):
    """Test bias awareness report generation."""
    # Create sample interactions data
    np.random.seed(42)
    n_interactions = 1000
    
    # Create imbalanced data: top 5 pathogens have most interactions
    pathogens = [f'pathogen_{i}' for i in range(20)]
    weights = [0.15, 0.12, 0.10, 0.08, 0.05] + [0.015] * 15  # Top 5 dominate
    weights = [w / sum(weights) for w in weights]  # Normalize
    
    pathogen_ids = np.random.choice(pathogens, size=n_interactions, p=weights)
    hosts = [f'host_{i}' for i in range(50)]
    host_ids = np.random.choice(hosts, size=n_interactions)
    
    interactions_df = pd.DataFrame({
        'pathogen_id': pathogen_ids,
        'host_id': host_ids,
        'interaction': np.random.choice([0, 1], size=n_interactions, p=[0.7, 0.3])
    })
    
    # Save interactions
    interactions_path = temp_output_dir / "interactions.csv"
    interactions_df.to_csv(interactions_path, index=False)
    
    # Generate report
    output_path = temp_output_dir / "bias_report.json"
    report = generate_bias_awareness_report(interactions_path, output_path)
    
    # Assertions
    assert output_path.exists()
    assert 'total_interactions' in report
    assert 'unique_pathogens' in report
    assert 'top_10_percentage' in report
    assert 'is_biased' in report
    assert 'flag' in report
    
    # Check that bias was detected (top pathogens should dominate)
    assert report['is_biased'] is True
    assert report['flag'] == 'WARNING'

def test_generate_bias_awareness_report_balanced(temp_output_dir):
    """Test bias awareness report with balanced data."""
    # Create balanced interactions data
    np.random.seed(42)
    n_interactions = 1000
    
    # Create balanced data: all pathogens have similar interactions
    pathogens = [f'pathogen_{i}' for i in range(20)]
    pathogen_ids = np.random.choice(pathogens, size=n_interactions)
    hosts = [f'host_{i}' for i in range(50)]
    host_ids = np.random.choice(hosts, size=n_interactions)
    
    interactions_df = pd.DataFrame({
        'pathogen_id': pathogen_ids,
        'host_id': host_ids,
        'interaction': np.random.choice([0, 1], size=n_interactions, p=[0.7, 0.3])
    })
    
    # Save interactions
    interactions_path = temp_output_dir / "interactions_balanced.csv"
    interactions_df.to_csv(interactions_path, index=False)
    
    # Generate report
    output_path = temp_output_dir / "bias_report_balanced.json"
    report = generate_bias_awareness_report(interactions_path, output_path)
    
    # Assertions
    assert output_path.exists()
    assert 'top_10_percentage' in report
    assert 'is_biased' in report
    
    # With balanced data, top 10 should not dominate
    assert report['is_biased'] is False
    assert report['flag'] == 'OK'

def test_calculate_shap_values_empty_input(sample_model_and_data):
    """Test SHAP calculation with empty feature matrix."""
    model = sample_model_and_data['model']
    feature_names = sample_model_and_data['feature_names']
    
    # Empty DataFrame
    empty_X = pd.DataFrame(columns=feature_names)
    
    with pytest.raises(ValueError, match="Feature matrix cannot be empty"):
        calculate_shap_values(model, empty_X, feature_names)

def test_calculate_shap_values_none_model(sample_model_and_data):
    """Test SHAP calculation with None model."""
    X = sample_model_and_data['X']
    feature_names = sample_model_and_data['feature_names']
    
    with pytest.raises(ValueError, match="Model cannot be None"):
        calculate_shap_values(None, X, feature_names)