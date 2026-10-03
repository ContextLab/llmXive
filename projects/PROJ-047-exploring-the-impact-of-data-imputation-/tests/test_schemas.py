"""
Unit tests for schema validation (T053).
"""
import pytest
import pandas as pd
import numpy as np
from pydantic import ValidationError
from code.analysis.schemas import (
    SimulationSummarySchema,
    StatisticalTestResult,
    validate_simulation_summary,
    validate_statistical_test_results
)


def create_valid_summary_df():
    """Create a valid DataFrame for simulation_summary.csv"""
    data = {
        'beta': [0.0, 0.2, 0.5],
        'method': ['mean', 'knn', 'mice'],
        'estimator': ['ipw', 'psm', 'ipw'],
        'ate': [0.5, 0.48, 0.52],
        'bias': [0.0, 0.02, 0.02],
        'rmse': [0.01, 0.015, 0.012],
        'coverage_rate': [0.95, 0.93, 0.94],
        'seed': [42, 43, 44],
        'run_id': ['hash1', 'hash2', 'hash3'],
        'ground_truth_ate': [0.5, 0.5, 0.5],
        'status': ['success', 'success', 'success'],
        'vif': [1.2, 1.3, 1.1],
        'mnar_correlation': [0.1, 0.3, 0.5],
        'mnar_p_value': [0.8, 0.4, 0.1]
    }
    return pd.DataFrame(data)


def test_valid_summary_schema():
    """Test that a valid DataFrame passes validation"""
    df = create_valid_summary_df()
    schema = validate_simulation_summary(df)
    assert len(schema.data) == 3
    assert schema.data[0].beta == 0.0
    assert schema.data[0].method == 'mean'


def test_missing_column_raises_error():
    """Test that missing a required column raises ValidationError"""
    df = create_valid_summary_df()
    df = df.drop(columns=['bias'])
    
    with pytest.raises(ValueError) as exc_info:
        validate_simulation_summary(df)
    
    assert "Missing required columns" in str(exc_info.value)


def test_invalid_beta_raises_error():
    """Test that beta outside [0, 1] raises ValidationError"""
    df = create_valid_summary_df()
    df.loc[0, 'beta'] = 1.5
    
    with pytest.raises(ValueError) as exc_info:
        validate_simulation_summary(df)
    
    assert "beta must be between 0.0 and 1.0" in str(exc_info.value)


def test_invalid_coverage_raises_error():
    """Test that coverage_rate outside [0, 1] raises ValidationError"""
    df = create_valid_summary_df()
    df.loc[0, 'coverage_rate'] = 1.5
    
    with pytest.raises(ValueError) as exc_info:
        validate_simulation_summary(df)
    
    assert "coverage_rate must be between 0.0 and 1.0" in str(exc_info.value)


def test_valid_statistical_test_result():
    """Test that a valid statistical test result passes"""
    data = {
        'test_type': 'anova',
        'p_value': 0.03,
        'test_statistic': 4.5,
        'skewness': 0.2,
        'bootstrap_ci_diff': 0.0
    }
    result = validate_statistical_test_results(data)
    assert result.test_type == 'anova'
    assert result.p_value == 0.03


def test_statistical_test_with_extreme_skew():
    """Test that extreme skewness allows non-zero bootstrap_ci_diff"""
    data = {
        'test_type': 'bootstrap',
        'p_value': 0.02,
        'test_statistic': 3.2,
        'skewness': 1.5,
        'bootstrap_ci_diff': 0.05
    }
    result = validate_statistical_test_results(data)
    assert result.skewness == 1.5
    assert result.bootstrap_ci_diff == 0.05


def test_invalid_p_value_raises_error():
    """Test that p_value outside [0, 1] raises ValidationError"""
    data = {
        'test_type': 'anova',
        'p_value': 1.5,
        'test_statistic': 4.5,
        'skewness': 0.2,
        'bootstrap_ci_diff': 0.0
    }
    
    with pytest.raises(ValidationError) as exc_info:
        validate_statistical_test_results(data)
    
    assert "p_value must be between 0.0 and 1.0" in str(exc_info.value)


def test_invalid_test_type_raises_error():
    """Test that invalid test_type raises ValidationError"""
    data = {
        'test_type': 'invalid_type',
        'p_value': 0.05,
        'test_statistic': 4.5,
        'skewness': 0.2,
        'bootstrap_ci_diff': 0.0
    }
    
    with pytest.raises(ValidationError) as exc_info:
        validate_statistical_test_results(data)
    
    assert "Input should be 'anova', 'friedman' or 'bootstrap'" in str(exc_info.value)
