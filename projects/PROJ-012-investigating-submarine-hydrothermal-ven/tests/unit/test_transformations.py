"""
Unit tests for diversity transformation logic.
"""
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from transformations import (
    add_pseudocount,
    log_transform,
    clr_transform,
    check_normality,
    select_transformation,
    run_diversity_transformation
)


@pytest.fixture
def sample_diversity_data():
    """Create sample diversity data for testing."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'shannon': [2.5, 3.1, 2.8, 3.5, 2.9],
        'simpson': [0.85, 0.92, 0.88, 0.95, 0.90],
        'pH': [7.2, 6.8, 7.0, 6.5, 7.1]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_diversity_with_zeros():
    """Create sample diversity data with zero values."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'shannon': [0.0, 3.1, 0.0, 3.5, 2.9],
        'simpson': [0.85, 0.0, 0.88, 0.95, 0.0],
        'pH': [7.2, 6.8, 7.0, 6.5, 7.1]
    }
    return pd.DataFrame(data)


def test_add_pseudocount(sample_diversity_data):
    """Test pseudocount addition."""
    df = sample_diversity_data.copy()
    result = add_pseudocount(df, 'shannon', pseudocount=1e-6)
    
    assert result['shannon'].min() > 0
    assert result['shannon'].iloc[0] == 2.5 + 1e-6
    assert 'sample_id' in result.columns


def test_add_pseudocount_invalid_column(sample_diversity_data):
    """Test error on invalid column."""
    df = sample_diversity_data.copy()
    with pytest.raises(ValueError, match="Column 'invalid' not found"):
        add_pseudocount(df, 'invalid', pseudocount=1e-6)


def test_log_transform(sample_diversity_data):
    """Test log transformation."""
    df = sample_diversity_data.copy()
    result = log_transform(df, 'shannon', base=np.e)
    
    assert 'shannon_log' in result.columns
    assert result['shannon_log'].iloc[0] == np.log(2.5)
    assert result['shannon_log'].iloc[0] > 0  # log(2.5) is positive


def test_log_transform_with_zeros(sample_diversity_with_zeros):
    """Test log transformation handles zeros with pseudocount."""
    df = sample_diversity_with_zeros.copy()
    result = log_transform(df, 'shannon', pseudocount=1e-6)
    
    assert 'shannon_log' in result.columns
    # Zero + pseudocount should be positive
    assert result['shannon_log'].iloc[0] > 0
    assert not np.isnan(result['shannon_log']).any()


def test_log_transform_base10(sample_diversity_data):
    """Test log transformation with base 10."""
    df = sample_diversity_data.copy()
    result = log_transform(df, 'shannon', base=10)
    
    assert 'shannon_log' in result.columns
    expected = np.log10(2.5)
    assert np.isclose(result['shannon_log'].iloc[0], expected)


def test_clr_transform(sample_diversity_data):
    """Test CLR transformation."""
    df = sample_diversity_data.copy()
    result = clr_transform(df, ['shannon', 'simpson'])
    
    assert 'shannon_clr' in result.columns
    assert 'simpson_clr' in result.columns
    
    # CLR values should sum to approximately 0 across the transformed columns for each row
    clr_sum = result['shannon_clr'] + result['simpson_clr']
    assert np.allclose(clr_sum, 0, atol=1e-6)


def test_clr_transform_invalid_columns(sample_diversity_data):
    """Test CLR transformation with invalid columns."""
    df = sample_diversity_data.copy()
    with pytest.raises(ValueError, match="Columns not found"):
        clr_transform(df, ['shannon', 'invalid_col'])


def test_check_normality(sample_diversity_data):
    """Test normality check."""
    df = sample_diversity_data.copy()
    stat, p_val = check_normality(df, 'shannon')
    
    assert isinstance(stat, float)
    assert isinstance(p_val, float)
    assert 0 <= p_val <= 1


def test_check_normality_insufficient_data():
    """Test normality check with insufficient data."""
    df = pd.DataFrame({'shannon': [1.0, 2.0]})  # Only 2 points
    stat, p_val = check_normality(df, 'shannon')
    
    assert stat == 0.0
    assert p_val == 1.0


def test_select_transformation(sample_diversity_data):
    """Test automatic transformation selection."""
    df = sample_diversity_data.copy()
    recommendations = select_transformation(df, ['shannon', 'simpson'])
    
    assert 'shannon' in recommendations
    assert 'simpson' in recommendations
    assert recommendations['shannon'] in ['none', 'log', 'sqrt']


def test_run_diversity_transformation(sample_diversity_data):
    """Test full transformation pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        sample_diversity_data.to_csv(input_path, index=False)
        
        result = run_diversity_transformation(
            input_path=input_path,
            output_path=output_path,
            diversity_columns=['shannon', 'simpson'],
            method='log'
        )
        
        assert output_path.exists()
        assert 'shannon_log' in result.columns
        assert 'simpson_log' in result.columns
        
        # Verify output file content
        output_df = pd.read_csv(output_path)
        assert len(output_df) == len(sample_diversity_data)


def test_run_diversity_transformation_auto(sample_diversity_data):
    """Test auto transformation method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        sample_diversity_data.to_csv(input_path, index=False)
        
        result = run_diversity_transformation(
            input_path=input_path,
            output_path=output_path,
            diversity_columns=['shannon', 'simpson'],
            method='auto'
        )
        
        assert output_path.exists()
        # Should have at least one transformed column
        assert any('_log' in col or '_clr' in col or '_sqrt' in col 
                  for col in result.columns)


def test_run_diversity_transformation_file_not_found():
    """Test error when input file not found."""
    with pytest.raises(FileNotFoundError):
        run_diversity_transformation(
            input_path=Path("/nonexistent/path.csv"),
            output_path=Path("/tmp/output.csv"),
            diversity_columns=['shannon']
        )


def test_run_diversity_transformation_no_diversity_columns():
    """Test error when no diversity columns found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        # Create CSV without diversity columns
        pd.DataFrame({'id': [1, 2], 'value': [10, 20]}).to_csv(input_path, index=False)
        
        with pytest.raises(ValueError, match="No diversity columns found"):
            run_diversity_transformation(
                input_path=input_path,
                output_path=output_path,
                diversity_columns=None,
                method='auto'
            )
