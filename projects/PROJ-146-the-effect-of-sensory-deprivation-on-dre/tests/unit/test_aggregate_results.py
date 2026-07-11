"""
Unit tests for result aggregation functionality (T033).

Tests the creation of variation tables and aggregation of sensitivity results.
"""
import os
import json
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import numpy as np

# Import functions to test
from code.aggregate_results import (
    load_model_results,
    extract_odds_ratios,
    create_variation_table,
    aggregate_sensitivity_results
)

@pytest.fixture
def mock_model_results():
    """Fixture providing mock model results data."""
    return {
        "fixed_effects": {
            "condition": {
                "estimate": 0.5,
                "std_err": 0.15,
                "pvalue": 0.001
            }
        },
        "metadata": {
            "threshold": "strict",
            "model_type": "logistic"
        }
    }

@pytest.fixture
def mock_threshold_data():
    """Fixture providing mock data for multiple thresholds."""
    return {
        "strict": {
            "fixed_effects": {
                "condition": {"estimate": 0.5, "std_err": 0.15, "pvalue": 0.001}
            }
        },
        "moderate": {
            "fixed_effects": {
                "condition": {"estimate": 0.3, "std_err": 0.12, "pvalue": 0.01}
            }
        },
        "partial": {
            "fixed_effects": {
                "condition": {"estimate": 0.1, "std_err": 0.10, "pvalue": 0.30}
            }
        }
    }

def test_extract_odds_ratios_logistic(mock_model_results):
    """Test extraction of odds ratios from logistic model results."""
    metrics = extract_odds_ratios(mock_model_results, model_type="logistic")
    
    assert 'odds_ratio' in metrics
    assert 'ci_lower' in metrics
    assert 'ci_upper' in metrics
    assert 'p_value' in metrics
    
    # Verify calculation: exp(0.5) ≈ 1.6487
    expected_or = np.exp(0.5)
    assert abs(metrics['odds_ratio'] - expected_or) < 0.001

def test_extract_odds_ratios_linear(mock_model_results):
    """Test extraction of coefficients from linear model results."""
    metrics = extract_odds_ratios(mock_model_results, model_type="linear")
    
    assert 'coefficient' in metrics
    assert 'ci_lower' in metrics
    assert 'ci_upper' in metrics
    
    # Verify calculation: 0.5
    assert abs(metrics['coefficient'] - 0.5) < 0.001

def test_extract_odds_ratios_empty():
    """Test extraction with empty results."""
    metrics = extract_odds_ratios({}, model_type="logistic")
    assert metrics == {}

def test_create_variation_table(mock_threshold_data):
    """Test creation of variation table across thresholds."""
    df = create_variation_table(mock_threshold_data)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert 'threshold' in df.columns
    assert 'odds_ratio' in df.columns
    assert 'p_value' in df.columns
    
    # Verify strict threshold has highest OR
    strict_row = df[df['threshold'] == 'strict'].iloc[0]
    assert strict_row['odds_ratio'] > df['odds_ratio'].min()

def test_create_variation_table_empty():
    """Test creation of variation table with empty input."""
    df = create_variation_table({})
    assert df.empty

def test_create_variation_table_with_missing_data():
    """Test creation of variation table with partial missing data."""
    data = {
        "strict": {"fixed_effects": {"condition": {"estimate": 0.5, "std_err": 0.1, "pvalue": 0.01}}},
        "moderate": None,
        "partial": {}
    }
    
    df = create_variation_table(data)
    
    # Should only have one row for strict
    assert len(df) == 1
    assert df.iloc[0]['threshold'] == 'strict'

@patch('code.aggregate_results.os.makedirs')
@patch('code.aggregate_results.open')
def test_aggregate_sensitivity_results(mock_open, mock_makedirs, mock_threshold_data):
    """Test full aggregation of sensitivity results."""
    bootstrap_data = {
        "strict": {"stable": True, "ci_width_variance": 0.001, "n_resamples": 1000},
        "moderate": {"stable": True, "ci_width_variance": 0.002, "n_resamples": 1000},
        "partial": {"stable": False, "ci_width_variance": 0.05, "n_resamples": 5000}
    }
    
    output_path = "results/models/test_variation.json"
    
    # This will fail if the path doesn't exist in real execution, 
    # but the mock handles the file operations
    result_path = aggregate_sensitivity_results(
        mock_threshold_data,
        bootstrap_data,
        output_path
    )
    
    assert result_path == output_path
    mock_makedirs.assert_called_once()
    mock_open.assert_called_once()

def test_aggregate_sensitivity_results_structure(mock_threshold_data):
    """Test that aggregated results have correct structure."""
    bootstrap_data = {
        "strict": {"stable": True, "ci_width_variance": 0.001, "n_resamples": 1000}
    }
    
    # Create a temporary file for testing
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        result_path = aggregate_sensitivity_results(
            mock_threshold_data,
            bootstrap_data,
            temp_path
        )
        
        with open(result_path, 'r') as f:
            report = json.load(f)
        
        assert 'metadata' in report
        assert 'variation_table' in report
        assert 'stability_analysis' in report
        assert 'summary_statistics' in report
        
        # Verify summary statistics
        assert report['summary_statistics']['n_thresholds'] == 3
        assert report['summary_statistics']['n_stable_thresholds'] == 1
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_load_model_results_not_found(tmp_path):
    """Test loading model results when file doesn't exist."""
    result = load_model_results(str(tmp_path), "strict")
    assert result is None

def test_load_model_results_invalid_json(tmp_path):
    """Test loading model results with invalid JSON."""
    file_path = tmp_path / "model_results_strict.json"
    file_path.write_text("invalid json content")
    
    result = load_model_results(str(tmp_path), "strict")
    assert result is None

def test_load_model_results_success(tmp_path):
    """Test successful loading of model results."""
    file_path = tmp_path / "model_results_strict.json"
    test_data = {"fixed_effects": {"condition": {"estimate": 0.5, "std_err": 0.1, "pvalue": 0.01}}}
    file_path.write_text(json.dumps(test_data))
    
    result = load_model_results(str(tmp_path), "strict")
    assert result is not None
    assert 'fixed_effects' in result
    assert result['fixed_effects']['condition']['estimate'] == 0.5
