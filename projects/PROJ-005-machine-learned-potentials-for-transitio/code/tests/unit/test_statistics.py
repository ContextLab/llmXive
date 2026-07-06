"""
Unit tests for statistical analysis module.
"""
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from scipy import stats
from src.analysis.statistics import (
    load_residuals_with_ligand_labels,
    perform_welch_ttest,
    run_statistical_analysis
)

@pytest.fixture
def mock_residuals_data():
    """Create mock residuals data with ligand classes."""
    np.random.seed(42)
    n_group13 = 50
    n_conventional = 75
    
    # Generate mock errors with different distributions
    errors_group13 = np.random.normal(loc=0.5, scale=0.2, size=n_group13)
    errors_conventional = np.random.normal(loc=0.3, scale=0.25, size=n_conventional)
    
    # Create DataFrame
    data = {
        'sample_id': list(range(n_group13 + n_conventional)),
        'error': np.concatenate([errors_group13, errors_conventional]),
        'ligand_class': ['Group 13'] * n_group13 + ['Conventional'] * n_conventional
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_residuals_file(mock_residuals_data):
    """Create a temporary parquet file with mock data."""
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
        mock_residuals_data.to_parquet(f.name)
        yield Path(f.name)
        Path(f.name).unlink()

def test_load_residuals_with_ligand_labels(mock_residuals_file):
    """Test loading residuals and ligand labels."""
    df, labels = load_residuals_with_ligand_labels(mock_residuals_file)
    
    assert 'error' in df.columns
    assert 'ligand_class' in df.columns
    assert len(df) == 125
    assert set(df['ligand_class'].unique()) == {'Group 13', 'Conventional'}

def test_perform_welch_ttest_basic(mock_residuals_data):
    """Test basic Welch's t-test execution."""
    result = perform_welch_ttest(
        mock_residuals_data,
        group_col='ligand_class',
        error_col='error',
        group1_name='Group 13',
        group2_name='Conventional'
    )
    
    assert 't_statistic' in result
    assert 'p_value' in result
    assert 'degrees_of_freedom' in result
    assert 'mean_difference' in result
    assert 'confidence_interval_95' in result
    assert result['group1_count'] == 50
    assert result['group2_count'] == 75
    assert result['test_type'] == 'unpaired_welch_ttest'

def test_welch_ttest_statistical_correctness(mock_residuals_data):
    """Verify that our implementation matches scipy's result."""
    group1 = mock_residuals_data[mock_residuals_data['ligand_class'] == 'Group 13']['error']
    group2 = mock_residuals_data[mock_residuals_data['ligand_class'] == 'Conventional']['error']
    
    # Scipy's Welch's t-test
    t_stat_expected, p_value_expected = stats.ttest_ind(group1, group2, equal_var=False)
    
    # Our implementation
    result = perform_welch_ttest(
        mock_residuals_data,
        group_col='ligand_class',
        error_col='error',
        group1_name='Group 13',
        group2_name='Conventional'
    )
    
    assert np.isclose(result['t_statistic'], t_stat_expected, rtol=1e-5)
    assert np.isclose(result['p_value'], p_value_expected, rtol=1e-5)

def test_run_statistical_analysis(mock_residuals_file):
    """Test full analysis pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'statistical_tests.json'
        
        result = run_statistical_analysis(mock_residuals_file, output_path)
        
        # Verify output file exists
        assert output_path.exists()
        
        # Verify result structure
        assert 't_statistic' in result
        assert 'p_value' in result
        assert 'deviation_note' in result
        assert 'analysis_timestamp' in result
        
        # Verify JSON can be loaded
        with open(output_path, 'r') as f:
            loaded = json.load(f)
            assert loaded == result

def test_empty_group_raises_error(mock_residuals_data):
    """Test that empty groups raise appropriate errors."""
    # Filter to only one group
    single_group = mock_residuals_data[mock_residuals_data['ligand_class'] == 'Group 13']
    
    with pytest.raises(ValueError, match="One of the groups has no data"):
        perform_welch_ttest(
            single_group,
            group_col='ligand_class',
            error_col='error',
            group1_name='Group 13',
            group2_name='Conventional'
        )

def test_missing_ligand_class_raises_error():
    """Test that missing ligand class raises appropriate errors."""
    df = pd.DataFrame({'error': [1, 2, 3]})
    
    with pytest.raises(ValueError, match="Ligand class information not found"):
        perform_welch_ttest(
            df,
            group_col='ligand_class',
            error_col='error'
        )

def test_confidence_interval_logic(mock_residuals_data):
    """Test that confidence intervals are computed correctly."""
    result = perform_welch_ttest(
        mock_residuals_data,
        group_col='ligand_class',
        error_col='error',
        group1_name='Group 13',
        group2_name='Conventional'
    )
    
    ci = result['confidence_interval_95']
    assert len(ci) == 2
    assert ci[0] <= ci[1]
    
    # Mean difference should be between the bounds
    mean_diff = result['mean_difference']
    assert ci[0] <= mean_diff <= ci[1]