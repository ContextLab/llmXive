import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from code.data.modeling import compute_external_validation_correlation, load_processed_data

@pytest.fixture
def sample_data_with_correlation():
    """Create a sample dataframe with known correlation."""
    np.random.seed(42)
    n = 100
    # Generate correlated data
    external_score = np.random.normal(0.5, 0.1, n)
    # Create a positive correlation with external_score
    contagion_index = external_score * 2 + np.random.normal(0, 0.05, n)
    agreement_prop = external_score * 1.5 + np.random.normal(0, 0.05, n)
    
    df = pd.DataFrame({
        'thread_id': range(n),
        'external_validation_score': external_score,
        'contagion_index': contagion_index,
        'agreement_proportion': agreement_prop,
        'entropy': np.random.uniform(0, 1, n),
        'time_to_decision': np.random.uniform(10, 100, n)
    })
    return df

@pytest.fixture
def temp_processed_dir(sample_data_with_correlation):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        # Save sample data
        file_path = tmpdir_path / "thread_metrics.csv"
        sample_data_with_correlation.to_csv(file_path, index=False)
        yield tmpdir_path

def test_compute_external_validation_correlation_positive(sample_data_with_correlation):
    """Test that correlation is computed correctly for positive relationship."""
    metrics = ['contagion_index', 'agreement_proportion']
    result = compute_external_validation_correlation(sample_data_with_correlation, metrics=metrics)
    
    assert not result.empty
    assert 'correlation_coefficient' in result.columns
    assert 'p_value' in result.columns
    
    # Check that correlation is positive and significant for our generated data
    corr_contagion = result[result['metric'] == 'contagion_index']['correlation_coefficient'].values[0]
    assert corr_contagion > 0.5, f"Expected strong positive correlation, got {corr_contagion}"
    
    corr_agreement = result[result['metric'] == 'agreement_proportion']['correlation_coefficient'].values[0]
    assert corr_agreement > 0.5, f"Expected strong positive correlation, got {corr_agreement}"

def test_compute_external_validation_correlation_missing_column(sample_data_with_correlation):
    """Test behavior when a metric column is missing."""
    metrics = ['contagion_index', 'non_existent_metric']
    result = compute_external_validation_correlation(sample_data_with_correlation, metrics=metrics)
    
    assert not result.empty
    # Should have 2 rows, one for each metric requested
    assert len(result) == 2
    # The non-existent metric should have NaN values
    missing_row = result[result['metric'] == 'non_existent_metric']
    assert missing_row['correlation_coefficient'].isna().all()

def test_compute_external_validation_correlation_no_data(sample_data_with_correlation):
    """Test behavior when external_validation_score is missing."""
    df = sample_data_with_correlation.drop(columns=['external_validation_score'])
    result = compute_external_validation_correlation(df, metrics=['contagion_index'])
    
    assert result.empty

def test_compute_external_validation_correlation_small_sample():
    """Test with very small sample size."""
    df = pd.DataFrame({
        'external_validation_score': [0.5, 0.6, 0.7],
        'contagion_index': [1.0, 2.0, 3.0]
    })
    result = compute_external_validation_correlation(df, metrics=['contagion_index'])
    
    assert not result.empty
    # Correlation should be 1.0 for perfectly linear 3 points
    assert abs(result['correlation_coefficient'].values[0] - 1.0) < 1e-5

def test_run_correlation_analysis_integration(temp_processed_dir):
    """Integration test: run the analysis function on a file."""
    input_file = temp_processed_dir / "thread_metrics.csv"
    output_file = temp_processed_dir / "output_correlation.csv"
    
    df = load_processed_data(str(input_file))
    result = compute_external_validation_correlation(df, metrics=['contagion_index', 'agreement_proportion'])
    
    result.to_csv(output_file, index=False)
    
    assert output_file.exists()
    output_df = pd.read_csv(output_file)
    assert len(output_df) == 2
    assert 'correlation_coefficient' in output_df.columns