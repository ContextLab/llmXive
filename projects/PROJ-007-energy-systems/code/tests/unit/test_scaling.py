"""
Unit tests for the scaling law analysis module.

These tests verify the power-law regression logic and exponent calculation
without making any causal claims.
"""

import pytest
import pandas as pd
import numpy as np
from src.scaling.scaling import (
    ScalingAnalysisError,
    aggregate_tract,
    fit_scaling_law,
    get_scaling_exponent_statistics,
    compare_to_universal_exponent,
    generate_scaling_report,
    UNIVERSAL_SCALING_EXPONENT
)

@pytest.fixture
def sample_tract_data():
    """Create sample tract-level data for testing."""
    np.random.seed(42)
    n_tracts = 50
    population = np.random.lognormal(mean=4, sigma=1, size=n_tracts)
    # Generate energy with a true scaling exponent of 0.85
    beta_true = 0.85
    energy = 100 * (population ** beta_true) * np.random.lognormal(sigma=0.2, size=n_tracts)

    return pd.DataFrame({
        'tract_id': [f'TR_{i:03d}' for i in range(n_tracts)],
        'total_energy_cost': energy,
        'total_population': population,
        'num_households': np.random.randint(5, 50, size=n_tracts)
    })

@pytest.fixture
def sample_household_data():
    """Create sample household-level data for testing aggregation."""
    np.random.seed(42)
    n_households = 500
    tract_ids = [f'TR_{i:03d}' for i in range(50)]

    return pd.DataFrame({
        'tract_id': np.random.choice(tract_ids, size=n_households),
        'energy_cost': np.random.lognormal(mean=3, sigma=0.5, size=n_households),
        'household_size': np.random.randint(1, 6, size=n_households)
    })

def test_aggregate_tract_basic(sample_household_data):
    """Test basic tract aggregation functionality."""
    result = aggregate_tract(sample_household_data)

    assert 'tract_id' in result.columns
    assert 'total_energy_cost' in result.columns
    assert 'total_population' in result.columns
    assert 'num_households' in result.columns
    assert len(result) > 0
    assert all(result['num_households'] >= 5)

def test_aggregate_tract_missing_columns(sample_household_data):
    """Test that missing columns raise an error."""
    df = sample_household_data.drop(columns=['energy_cost'])
    with pytest.raises(ScalingAnalysisError, match="Missing required columns"):
        aggregate_tract(df)

def test_aggregate_tract_insufficient_data():
    """Test that insufficient data raises an error."""
    df = pd.DataFrame({
        'tract_id': ['TR_001', 'TR_002'],
        'energy_cost': [100, 200],
        'household_size': [2, 3]
    })
    with pytest.raises(ScalingAnalysisError, match="No valid data after filtering"):
        aggregate_tract(df)

def test_fit_scaling_law_basic(sample_tract_data):
    """Test basic scaling law fitting."""
    beta = fit_scaling_law(sample_tract_data)

    assert isinstance(beta, float)
    assert 0 < beta < 2  # Reasonable range for scaling exponents
    assert abs(beta - 0.85) < 0.15  # Should be close to true value

def test_fit_scaling_law_missing_columns(sample_tract_data):
    """Test that missing columns raise an error."""
    df = sample_tract_data.drop(columns=['total_energy_cost'])
    with pytest.raises(ScalingAnalysisError, match="Missing required columns"):
        fit_scaling_law(df)

def test_fit_scaling_law_insufficient_data():
    """Test that insufficient data raises an error."""
    df = pd.DataFrame({
        'total_energy_cost': [100, 200, 300],
        'total_population': [10, 20, 30]
    })
    with pytest.raises(ScalingAnalysisError, match="Insufficient data"):
        fit_scaling_law(df)

def test_get_scaling_exponent_statistics(sample_tract_data):
    """Test comprehensive statistics calculation."""
    stats = get_scaling_exponent_statistics(sample_tract_data)

    assert 'beta' in stats
    assert 'beta_ci_lower' in stats
    assert 'beta_ci_upper' in stats
    assert 'r_squared' in stats
    assert 'p_value' in stats
    assert 'n_tracts' in stats
    assert 'model' in stats

    assert stats['beta_ci_lower'] < stats['beta'] < stats['beta_ci_upper']
    assert 0 <= stats['r_squared'] <= 1
    assert stats['n_tracts'] >= 10

def test_compare_to_universal_exponent(sample_tract_data):
    """Test comparison to universal exponent."""
    comparison = compare_to_universal_exponent(sample_tract_data)

    assert 'estimated_beta' in comparison
    assert 'universal_beta' in comparison
    assert 'difference' in comparison
    assert 'within_universal_ci' in comparison
    assert 't_statistic' in comparison
    assert 'p_value' in comparison
    assert 'interpretation' in comparison
    assert 'disclaimer' in comparison

    assert comparison['universal_beta'] == UNIVERSAL_SCALING_EXPONENT
    assert isinstance(comparison['interpretation'], str)
    assert 'DESCRIPTIVE' in comparison['disclaimer'] or 'descriptive' in comparison['disclaimer'].lower()

def test_compare_to_universal_exponent_missing_columns(sample_tract_data):
    """Test that missing columns raise an error in comparison."""
    df = sample_tract_data.drop(columns=['total_energy_cost'])
    with pytest.raises(ScalingAnalysisError, match="Missing required columns"):
        compare_to_universal_exponent(df)

def test_generate_scaling_report(sample_tract_data, tmp_path):
    """Test report generation."""
    output_path = tmp_path / "scaling_report.json"
    report = generate_scaling_report(sample_tract_data, str(output_path))

    assert 'title' in report
    assert 'methodology' in report
    assert 'scaling_statistics' in report
    assert 'universal_comparison' in report
    assert 'disclaimer' in report
    assert 'generated_at' in report

    # Verify file was created
    assert output_path.exists()

    # Verify disclaimer content
    assert 'DESCRIPTIVE' in report['disclaimer'] or 'descriptive' in report['disclaimer'].lower()
    assert 'causal' in report['disclaimer'].lower()

def test_generate_scaling_report_without_output_path(sample_tract_data):
    """Test report generation without file output."""
    report = generate_scaling_report(sample_tract_data)

    assert 'title' in report
    assert 'disclaimer' in report

def test_scaling_exponent_reasonable_range(sample_tract_data):
    """Test that estimated exponent is in a reasonable range."""
    stats = get_scaling_exponent_statistics(sample_tract_data)
    beta = stats['beta']

    # Scaling exponents for infrastructure are typically between 0.7 and 1.2
    assert 0.5 < beta < 1.5, f"Scaling exponent {beta} is outside reasonable range"

def test_scaling_report_includes_disclaimer(sample_tract_data):
    """Test that the report explicitly includes a disclaimer about causality."""
    report = generate_scaling_report(sample_tract_data)

    disclaimer = report['disclaimer'].lower()
    assert 'descriptive' in disclaimer
    assert 'causal' in disclaimer
    assert 'not' in disclaimer

def test_aggregate_tract_filters_small_tracts(sample_household_data):
    """Test that tracts with fewer than 5 households are filtered."""
    # Create data with some small tracts
    df = sample_household_data.copy()
    df.loc[0:3, 'tract_id'] = 'TR_SMALL'  # Only 4 households

    result = aggregate_tract(df)
    small_tracts = result[result['tract_id'] == 'TR_SMALL']

    assert len(small_tracts) == 0, "Small tracts should be filtered out"

def test_fit_scaling_law_handles_zeros():
    """Test that zero values are handled correctly."""
    df = pd.DataFrame({
        'total_energy_cost': [0, 100, 200, 300],
        'total_population': [10, 20, 30, 40]
    })
    # Should filter out zero energy and still work with remaining data
    beta = fit_scaling_law(df)
    assert isinstance(beta, float)