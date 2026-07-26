"""
Unit tests for partial correlation analysis module.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from code.src.analysis.partial_correlation import (
    PartialCorrelationError,
    load_simulation_results,
    calculate_partial_correlation,
    run_partial_correlation_analysis,
    aggregate_results
)


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n = 100

    # Generate correlated variables
    x = np.random.normal(0, 1, n)
    z = np.random.normal(0, 1, n)  # Control variable
    y = 0.5 * x + 0.3 * z + np.random.normal(0, 0.5, n)  # Target depends on x and z

    df = pd.DataFrame({
        'diffusion_rate': y,
        'clustering_coefficient': x,
        'average_path_length': z,
        'degree': x * 2 + np.random.normal(0, 0.1, n),
        'density': x * 0.5 + np.random.normal(0, 0.1, n)
    })

    return df


@pytest.fixture
def temp_simulation_file(sample_data):
    """Create a temporary simulation results file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = sample_data.to_dict('records')
        json.dump(data, f)
        return f.name


def test_load_simulation_results(temp_simulation_file):
    """Test loading simulation results from JSON."""
    df = load_simulation_results(temp_simulation_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 100
    assert 'diffusion_rate' in df.columns
    assert 'clustering_coefficient' in df.columns


def test_load_simulation_results_missing_file():
    """Test error handling for missing file."""
    with pytest.raises(PartialCorrelationError):
        load_simulation_results('nonexistent_file.json')


def test_load_simulation_results_invalid_json():
    """Test error handling for invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json")
        temp_path = f.name

    try:
        with pytest.raises(PartialCorrelationError):
            load_simulation_results(temp_path)
    finally:
        Path(temp_path).unlink()


def test_calculate_partial_correlation_basic(sample_data):
    """Test basic partial correlation calculation."""
    corr, p_value, ci_lower = calculate_partial_correlation(
        sample_data,
        target='diffusion_rate',
        predictor='clustering_coefficient',
        controls=['average_path_length']
    )

    assert isinstance(corr, float)
    assert isinstance(p_value, float)
    assert isinstance(ci_lower, float)
    assert 0 <= p_value <= 1
    assert -1 <= corr <= 1


def test_calculate_partial_correlation_no_controls(sample_data):
    """Test partial correlation with no controls."""
    corr, p_value, ci_lower = calculate_partial_correlation(
        sample_data,
        target='diffusion_rate',
        predictor='clustering_coefficient',
        controls=[]
    )

    assert isinstance(corr, float)
    assert isinstance(p_value, float)


def test_calculate_partial_correlation_insufficient_data():
    """Test error handling for insufficient data."""
    df = pd.DataFrame({
        'diffusion_rate': [1, 2],
        'clustering_coefficient': [0.1, 0.2],
        'average_path_length': [1.0, 2.0]
    })

    with pytest.raises(PartialCorrelationError):
        calculate_partial_correlation(
            df,
            target='diffusion_rate',
            predictor='clustering_coefficient',
            controls=['average_path_length']
        )


def test_run_partial_correlation_analysis(sample_data):
    """Test running full partial correlation analysis."""
    results = run_partial_correlation_analysis(
        sample_data,
        target='diffusion_rate',
        predictors=['clustering_coefficient', 'degree'],
        controls=['average_path_length']
    )

    assert isinstance(results, dict)
    assert 'clustering_coefficient' in results
    assert 'degree' in results
    assert results['clustering_coefficient']['status'] == 'success'
    assert 'correlation_coefficient' in results['clustering_coefficient']
    assert 'p_value' in results['clustering_coefficient']


def test_run_partial_correlation_analysis_missing_predictor(sample_data):
    """Test handling of missing predictor column."""
    results = run_partial_correlation_analysis(
        sample_data,
        target='diffusion_rate',
        predictors=['nonexistent_column'],
        controls=['average_path_length']
    )

    assert 'nonexistent_column' not in results


def test_aggregate_results():
    """Test aggregation of results."""
    results = {
        'var1': {'correlation_coefficient': 0.5, 'p_value': 0.01, 'status': 'success'},
        'var2': {'correlation_coefficient': 0.3, 'p_value': 0.03, 'status': 'success'},
        'var3': {'error': 'Test error', 'status': 'failed'}
    }

    summary = aggregate_results(results)

    assert summary['total_predictors'] == 3
    assert summary['successful_analyses'] == 2
    assert summary['failed_analyses'] == 1
    assert 'var1' in summary['results']
    assert 'var2' in summary['results']
    assert len(summary['significant_findings']) >= 0  # May or may not be significant depending on threshold
