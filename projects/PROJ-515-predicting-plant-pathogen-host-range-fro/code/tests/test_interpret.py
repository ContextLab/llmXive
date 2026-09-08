import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.models.interpret import (
    calculate_shap_values,
    generate_feature_importance_report,
    run_shap_analysis,
    generate_bias_awareness_report
)

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_model_and_data():
    # Create a mock model
    model = MagicMock()
    model.predict_proba.return_value = np.array([[0.9, 0.1], [0.2, 0.8], [0.8, 0.2]])
    
    # Create sample data
    data = pd.DataFrame({
        'feat1': [1.0, 2.0, 3.0],
        'feat2': [4.0, 5.0, 6.0],
        'feat3': [7.0, 8.0, 9.0]
    })
    
    return model, data

def test_calculate_shap_values_basic(sample_model_and_data, temp_output_dir):
    model, data = sample_model_and_data
    
    # Mock shap to avoid actual dependency issues in test environment
    with patch('src.models.interpret.shap') as mock_shap:
        mock_explainer = MagicMock()
        mock_shap.KernelExplainer.return_value = mock_explainer
        # Return a 2D array for shap values (samples x features)
        mock_shap_values = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        mock_explainer.shap_values.return_value = mock_shap_values
        
        shap_df = calculate_shap_values(model, data)
        
        assert isinstance(shap_df, pd.DataFrame)
        assert shap_df.shape[0] == 2  # 2 samples
        assert shap_df.shape[1] == 3  # 3 features
        assert list(shap_df.columns) == ['feat1', 'feat2', 'feat3']

def test_generate_feature_importance_report(sample_model_and_data, temp_output_dir):
    model, data = sample_model_and_data
    
    # Create dummy SHAP values
    shap_df = pd.DataFrame({
        'feat1': [0.1, 0.2],
        'feat2': [0.3, 0.4],
        'feat3': [0.5, 0.6]
    })
    
    output_path = temp_output_dir / "feature_importance.csv"
    
    importance_df = generate_feature_importance_report(shap_df, data, output_path)
    
    assert isinstance(importance_df, pd.DataFrame)
    assert 'feature' in importance_df.columns
    assert 'mean_abs_shap' in importance_df.columns
    assert 'std_shap' in importance_df.columns
    assert output_path.exists()
    
    # Check content
    loaded_df = pd.read_csv(output_path)
    assert len(loaded_df) == 3

def test_run_shap_analysis_integration(sample_model_and_data, temp_output_dir):
    model, data = sample_model_and_data
    
    with patch('src.models.interpret.shap') as mock_shap:
        mock_explainer = MagicMock()
        mock_shap.KernelExplainer.return_value = mock_explainer
        mock_shap_values = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        mock_explainer.shap_values.return_value = mock_shap_values
        
        result_df = run_shap_analysis(model, data, temp_output_dir)
        
        assert isinstance(result_df, pd.DataFrame)
        assert (temp_output_dir / "feature_importance.csv").exists()

def test_generate_bias_awareness_report(temp_output_dir):
    # Create sample interactions
    interactions = pd.DataFrame({
        'pathogen': ['P1', 'P1', 'P1', 'P1', 'P2', 'P2', 'P3'],
        'host': ['H1', 'H2', 'H3', 'H4', 'H1', 'H2', 'H1']
    })
    
    output_path = temp_output_dir / "bias_awareness.json"
    
    report = generate_bias_awareness_report(interactions, output_path)
    
    assert isinstance(report, dict)
    assert 'total_interactions' in report
    assert 'is_biased' in report
    assert 'top_pathogens' in report
    assert output_path.exists()
    
    # Check specific values
    assert report['total_interactions'] == 7
    # P1 has 4, P2 has 2, P3 has 1. Top 10 (or top 3 here) sum = 7.
    # 7/7 = 1.0 > 0.8, so should be biased
    assert report['is_biased'] is True

def test_generate_bias_awareness_report_balanced(temp_output_dir):
    # Create balanced interactions
    interactions = pd.DataFrame({
        'pathogen': ['P1', 'P2', 'P3'],
        'host': ['H1', 'H2', 'H3']
    })
    
    output_path = temp_output_dir / "bias_awareness_balanced.json"
    
    report = generate_bias_awareness_report(interactions, output_path, top_n=1, threshold=0.8)
    
    # P1 has 1/3 = 0.33 < 0.8
    assert report['is_biased'] is False

def test_calculate_shap_values_empty_input(sample_model_and_data, temp_output_dir):
    model, _ = sample_model_and_data
    empty_data = pd.DataFrame()
    
    with pytest.raises((IndexError, ValueError, KeyError)):
        calculate_shap_values(model, empty_data)

def test_calculate_shap_values_none_model(temp_output_dir):
    data = pd.DataFrame({'a': [1, 2]})
    
    with patch('src.models.interpret.shap') as mock_shap:
        mock_shap.KernelExplainer.side_effect = AttributeError("NoneType has no attribute")
        with pytest.raises((AttributeError, TypeError)):
            calculate_shap_values(None, data)
