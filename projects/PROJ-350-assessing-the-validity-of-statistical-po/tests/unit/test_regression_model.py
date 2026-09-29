"""
Unit tests for T032: Regression modeling module.

Verifies that:
- sample_size_category is excluded from predictors
- Model fits correctly with statsmodels.OLS
- Results are written to correct output file
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from regression_model import (
    RegressionModelError,
    load_preprocessed_data,
    build_regression_model,
    run_regression_analysis,
    write_results
)

@pytest.fixture
def mock_power_data():
    """Mock power analysis data with valid records."""
    data = {
        'records': [
            {
                'study_id': '1',
                'power_gap': 0.2,
                'field': 'Psychology',
                'effect_size_domain': 'Small',
                'sample_size_category': 'Medium'  # This should be excluded
            },
            {
                'study_id': '2',
                'power_gap': 0.15,
                'field': 'Neuroscience',
                'effect_size_domain': 'Medium',
                'sample_size_category': 'Large'
            },
            {
                'study_id': '3',
                'power_gap': 0.25,
                'field': 'Psychology',
                'effect_size_domain': 'Small',
                'sample_size_category': 'Small'
            },
            {
                'study_id': '4',
                'power_gap': 0.1,
                'field': 'Economics',
                'effect_size_domain': 'Large',
                'sample_size_category': 'Large'
            },
            {
                'study_id': '5',
                'power_gap': 0.3,
                'field': 'Neuroscience',
                'effect_size_domain': 'Medium',
                'sample_size_category': 'Medium'
            },
            {
                'study_id': '6',
                'power_gap': 0.22,
                'field': 'Psychology',
                'effect_size_domain': 'Small',
                'sample_size_category': 'Small'
            },
            {
                'study_id': '7',
                'power_gap': 0.18,
                'field': 'Economics',
                'effect_size_domain': 'Large',
                'sample_size_category': 'Large'
            },
            {
                'study_id': '8',
                'power_gap': 0.28,
                'field': 'Neuroscience',
                'effect_size_domain': 'Medium',
                'sample_size_category': 'Medium'
            },
            {
                'study_id': '9',
                'power_gap': 0.12,
                'field': 'Psychology',
                'effect_size_domain': 'Small',
                'sample_size_category': 'Small'
            },
            {
                'study_id': '10',
                'power_gap': 0.21,
                'field': 'Economics',
                'effect_size_domain': 'Large',
                'sample_size_category': 'Large'
            },
            {
                'study_id': '11',
                'power_gap': 0.19,
                'field': 'Neuroscience',
                'effect_size_domain': 'Medium',
                'sample_size_category': 'Medium'
            },
            {
                'study_id': '12',
                'power_gap': 0.23,
                'field': 'Psychology',
                'effect_size_domain': 'Small',
                'sample_size_category': 'Small'
            },
            {
                'study_id': '13',
                'power_gap': 0.14,
                'field': 'Economics',
                'effect_size_domain': 'Large',
                'sample_size_category': 'Large'
            },
            {
                'study_id': '14',
                'power_gap': 0.26,
                'field': 'Neuroscience',
                'effect_size_domain': 'Medium',
                'sample_size_category': 'Medium'
            },
            {
                'study_id': '15',
                'power_gap': 0.17,
                'field': 'Psychology',
                'effect_size_domain': 'Small',
                'sample_size_category': 'Small'
            },
            {
                'study_id': '16',
                'power_gap': 0.24,
                'field': 'Economics',
                'effect_size_domain': 'Large',
                'sample_size_category': 'Large'
            },
            {
                'study_id': '17',
                'power_gap': 0.11,
                'field': 'Neuroscience',
                'effect_size_domain': 'Medium',
                'sample_size_category': 'Medium'
            },
            {
                'study_id': '18',
                'power_gap': 0.29,
                'field': 'Psychology',
                'effect_size_domain': 'Small',
                'sample_size_category': 'Small'
            },
            {
                'study_id': '19',
                'power_gap': 0.13,
                'field': 'Economics',
                'effect_size_domain': 'Large',
                'sample_size_category': 'Large'
            },
            {
                'study_id': '20',
                'power_gap': 0.27,
                'field': 'Neuroscience',
                'effect_size_domain': 'Medium',
                'sample_size_category': 'Medium'
            },
            {
                'study_id': '21',
                'power_gap': 0.16,
                'field': 'Psychology',
                'effect_size_domain': 'Small',
                'sample_size_category': 'Small'
            },
            {
                'study_id': '22',
                'power_gap': 0.31,
                'field': 'Economics',
                'effect_size_domain': 'Large',
                'sample_size_category': 'Large'
            },
            {
                'study_id': '23',
                'power_gap': 0.09,
                'field': 'Neuroscience',
                'effect_size_domain': 'Medium',
                'sample_size_category': 'Medium'
            },
            {
                'study_id': '24',
                'power_gap': 0.32,
                'field': 'Psychology',
                'effect_size_domain': 'Small',
                'sample_size_category': 'Small'
            },
            {
                'study_id': '25',
                'power_gap': 0.08,
                'field': 'Economics',
                'effect_size_domain': 'Large',
                'sample_size_category': 'Large'
            },
            {
                'study_id': '26',
                'power_gap': 0.33,
                'field': 'Neuroscience',
                'effect_size_domain': 'Medium',
                'sample_size_category': 'Medium'
            },
            {
                'study_id': '27',
                'power_gap': 0.07,
                'field': 'Psychology',
                'effect_size_domain': 'Small',
                'sample_size_category': 'Small'
            },
            {
                'study_id': '28',
                'power_gap': 0.34,
                'field': 'Economics',
                'effect_size_domain': 'Large',
                'sample_size_category': 'Large'
            },
            {
                'study_id': '29',
                'power_gap': 0.06,
                'field': 'Neuroscience',
                'effect_size_domain': 'Medium',
                'sample_size_category': 'Medium'
            },
            {
                'study_id': '30',
                'power_gap': 0.35,
                'field': 'Psychology',
                'effect_size_domain': 'Small',
                'sample_size_category': 'Small'
            }
        ]
    }
    return data

@patch('regression_model.load_power_analysis')
@patch('regression_model.filter_valid_records')
@patch('regression_model.preprocess_for_regression')
def test_load_preprocessed_data_excludes_sample_size_category(
    mock_preprocess,
    mock_filter,
    mock_load,
    mock_power_data
):
    """Verify sample_size_category is excluded from predictors."""
    # Setup mocks
    mock_load.return_value = mock_power_data
    mock_filter.return_value = mock_power_data['records']
    
    # Mock preprocessed DataFrame
    df = pd.DataFrame([
        {'study_id': '1', 'power_gap': 0.2, 'field': 'Psychology', 'effect_size_domain': 'Small'},
        {'study_id': '2', 'power_gap': 0.15, 'field': 'Neuroscience', 'effect_size_domain': 'Medium'}
    ])
    mock_preprocess.return_value = df
    
    # Run function
    result_df = load_preprocessed_data()
    
    # Verify sample_size_category is not in columns
    assert 'sample_size_category' not in result_df.columns
    assert 'field' in result_df.columns
    assert 'effect_size_domain' in result_df.columns

@patch('regression_model.load_power_analysis')
@patch('regression_model.filter_valid_records')
@patch('regression_model.preprocess_for_regression')
def test_build_regression_model_correct_predictors(
    mock_preprocess,
    mock_filter,
    mock_load,
    mock_power_data
):
    """Verify model uses correct predictors (field, effect_size_domain)."""
    # Setup mocks
    mock_load.return_value = mock_power_data
    mock_filter.return_value = mock_power_data['records']
    
    # Mock preprocessed DataFrame
    df = pd.DataFrame([
        {'study_id': '1', 'power_gap': 0.2, 'field_P': 1, 'field_N': 0, 'effect_size_S': 1, 'effect_size_M': 0},
        {'study_id': '2', 'power_gap': 0.15, 'field_P': 0, 'field_N': 1, 'effect_size_S': 0, 'effect_size_M': 1}
    ] * 15)  # Repeat to have enough samples
    mock_preprocess.return_value = df
    
    # Run function
    model, results_df = build_regression_model(df)
    
    # Verify model is OLS
    assert isinstance(model, sm.OLS)
    
    # Verify predictors (should include const, field dummies, effect_size dummies)
    expected_predictors = ['const', 'field_P', 'field_N', 'effect_size_S', 'effect_size_M']
    assert list(results_df['predictor']) == expected_predictors
    
    # Verify sample_size_category is not in predictors
    assert 'sample_size_category' not in results_df['predictor'].values

@patch('regression_model.load_power_analysis')
@patch('regression_model.filter_valid_records')
@patch('regression_model.preprocess_for_regression')
def test_run_regression_analysis_returns_valid_structure(
    mock_preprocess,
    mock_filter,
    mock_load,
    mock_power_data
):
    """Verify output structure is correct."""
    # Setup mocks
    mock_load.return_value = mock_power_data
    mock_filter.return_value = mock_power_data['records']
    
    # Mock preprocessed DataFrame
    df = pd.DataFrame([
        {'study_id': '1', 'power_gap': 0.2, 'field_P': 1, 'field_N': 0, 'effect_size_S': 1, 'effect_size_M': 0},
        {'study_id': '2', 'power_gap': 0.15, 'field_P': 0, 'field_N': 1, 'effect_size_S': 0, 'effect_size_M': 1}
    ] * 15)
    mock_preprocess.return_value = df
    
    # Run function
    output = run_regression_analysis()
    
    # Verify structure
    assert 'metadata' in output
    assert 'coefficients' in output
    assert 'model_summary' in output
    
    # Verify metadata
    assert output['metadata']['model_type'] == 'OLS'
    assert output['metadata']['target'] == 'power_gap'
    assert 'sample_size_category' not in output['metadata']['predictors']
    assert output['metadata']['excluded_predictors'] == ['sample_size_category']

def test_write_results_creates_file(tmp_path):
    """Verify write_results creates output file."""
    output = {
        'metadata': {'test': 'data'},
        'coefficients': [],
        'model_summary': 'summary'
    }
    output_path = tmp_path / 'test_results.json'
    
    write_results(output, output_path)
    
    assert output_path.exists()
    
    with open(output_path) as f:
        result = json.load(f)
    
    assert result == output

if __name__ == '__main__':
    pytest.main([__file__, '-v'])