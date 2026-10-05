"""
Unit tests for T019: Linear Regression Analysis with Covariates.

Tests the regression analysis implementation including:
- Basic regression functionality
- Covariate handling
- R-squared calculation
- Benjamini-Hochberg FDR correction
"""

import pytest
import pandas as pd
import numpy as np
from code.src.analysis.correlation import (
    run_regression_analysis,
    run_multiple_regressions,
    apply_benjamini_hochberg
)

@pytest.fixture
def sample_regression_data():
    """Create a sample dataset for regression testing."""
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        'cognitive_flexibility_score': np.random.normal(50, 10, n),
        'shannon_diversity': np.random.normal(3.5, 0.5, n),
        'simpson_diversity': np.random.normal(0.85, 0.1, n),
        'chao1': np.random.normal(20, 5, n),
        'age': np.random.randint(65, 90, n),
        'sex': np.random.choice(['M', 'F'], n),
        'bmi': np.random.normal(25, 4, n),
        'dietary_fiber_intake': np.random.normal(25, 5, n),
        'antibiotic_use_history': np.random.choice([True, False], n)
    })
    return data

def test_regression_analysis_basic(sample_regression_data):
    """Test basic regression analysis functionality."""
    result = run_regression_analysis(
        sample_regression_data,
        dependent_var='cognitive_flexibility_score',
        independent_var='shannon_diversity',
        covariates=['age', 'sex', 'bmi', 'dietary_fiber_intake', 'antibiotic_use_history']
    )
    
    # Check that results are returned
    assert 'r_squared' in result
    assert 'coefficient' in result
    assert 'p_value' in result
    assert 'confidence_interval' in result
    assert 'formula' in result
    
    # R-squared should be between 0 and 1 (or NaN if failed)
    if not np.isnan(result['r_squared']):
        assert 0 <= result['r_squared'] <= 1
    
    # Should have run on the expected number of observations
    assert result['n_observations'] > 10

def test_regression_analysis_missing_column(sample_regression_data):
    """Test regression with missing required column."""
    # Remove a required column
    data = sample_regression_data.drop(columns=['age'])
    
    with pytest.raises(KeyError):
        run_regression_analysis(
            data,
            dependent_var='cognitive_flexibility_score',
            independent_var='shannon_diversity',
            covariates=['age', 'sex', 'bmi', 'dietary_fiber_intake', 'antibiotic_use_history']
        )

def test_benjamini_hochberg_correction():
    """Test Benjamini-Hochberg FDR correction implementation."""
    # Create a list of p-values
    p_values = [0.01, 0.03, 0.04, 0.06, 0.10, 0.20, 0.50, 0.80]
    
    adjusted = apply_benjamini_hochberg(p_values)
    
    # Check that we get the same number of results
    assert len(adjusted) == len(p_values)
    
    # Check that adjusted p-values are monotonically increasing
    # (after sorting, they should be non-decreasing from the end)
    valid_adjusted = [p for p in adjusted if not np.isnan(p)]
    for i in range(len(valid_adjusted) - 1):
        assert valid_adjusted[i] <= valid_adjusted[i + 1]
    
    # Check that adjusted p-values are <= 1.0
    for p in adjusted:
        if not np.isnan(p):
            assert p <= 1.0

def test_multiple_regressions(sample_regression_data):
    """Test running multiple regressions at once."""
    diversity_metrics = ['shannon_diversity', 'simpson_diversity', 'chao1']
    covariates = ['age', 'sex', 'bmi', 'dietary_fiber_intake', 'antibiotic_use_history']
    
    results = run_multiple_regressions(
        sample_regression_data,
        diversity_metrics,
        'cognitive_flexibility_score',
        covariates
    )
    
    # Check that we got results for all metrics
    assert len(results) == len(diversity_metrics)
    
    # Check that each result has the expected structure
    for result in results:
        assert 'metric_name' in result
        assert result['metric_name'] in diversity_metrics
        assert 'r_squared' in result
        assert 'coefficient' in result
        assert 'p_value' in result
        assert 'adjusted_p_value' in result

def test_regression_with_nan_handling(sample_regression_data):
    """Test that regression handles NaN values correctly."""
    # Introduce some NaN values
    data = sample_regression_data.copy()
    data.loc[data.index[:10], 'shannon_diversity'] = np.nan
    
    result = run_regression_analysis(
        data,
        dependent_var='cognitive_flexibility_score',
        independent_var='shannon_diversity',
        covariates=['age', 'sex', 'bmi', 'dietary_fiber_intake', 'antibiotic_use_history']
    )
    
    # Should still run but with fewer observations
    assert result['n_observations'] < len(sample_regression_data)
    assert result['n_observations'] > 0

def test_regression_formula_construction(sample_regression_data):
    """Test that the regression formula is constructed correctly."""
    result = run_regression_analysis(
        sample_regression_data,
        dependent_var='cognitive_flexibility_score',
        independent_var='shannon_diversity',
        covariates=['age', 'sex', 'bmi', 'dietary_fiber_intake', 'antibiotic_use_history']
    )
    
    expected_vars = ['cognitive_flexibility_score', 'shannon_diversity', 
                    'age', 'sex', 'bmi', 'dietary_fiber_intake', 'antibiotic_use_history']
    for var in expected_vars:
        assert var in result['formula']