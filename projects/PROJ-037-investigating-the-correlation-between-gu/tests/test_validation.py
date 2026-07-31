import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from code.validation import (
    load_correlation_results,
    bootstrap_resample,
    get_top_correlations,
    run_bootstrap_analysis,
    save_validation_status,
    run_sensitivity_analysis
)

@pytest.fixture
def sample_correlation_results():
    """Create sample correlation results for testing."""
    data = {
        'taxon': ['Bacteroides', 'Firmicutes', 'Actinobacteria', 'Proteobacteria', 'Verrucomicrobia'],
        'sleep_variable': ['duration', 'quality', 'chronotype', 'duration', 'quality'],
        'correlation': [0.45, -0.32, 0.18, -0.51, 0.29],
        'p_value': [0.001, 0.023, 0.156, 0.0003, 0.045],
        'p_value_fdr': [0.003, 0.046, 0.234, 0.001, 0.067]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_correlation_results(sample_correlation_results, temp_output_dir):
    """Test loading correlation results from CSV."""
    # Save sample data to temp file
    results_path = temp_output_dir / 'correlation_results.csv'
    sample_correlation_results.to_csv(results_path, index=False)
    
    # Load and verify
    loaded_df = load_correlation_results(str(results_path))
    assert len(loaded_df) == len(sample_correlation_results)
    assert set(loaded_df.columns) == set(sample_correlation_results.columns)
    assert list(loaded_df['taxon']) == list(sample_correlation_results['taxon'])

def test_load_correlation_results_file_not_found():
    """Test that FileNotFoundError is raised when file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_correlation_results('nonexistent_file.csv')

def test_bootstrap_resample(sample_correlation_results):
    """Test bootstrap resampling logic."""
    # Perform resampling
    bootstrap_df = bootstrap_resample(sample_correlation_results, n_samples=100, seed=42)
    
    # Verify output
    assert len(bootstrap_df) == 100 * len(sample_correlation_results)
    assert set(bootstrap_df.columns) == set(sample_correlation_results.columns)
    
    # Verify that resampling includes duplicates (with replacement)
    unique_rows = bootstrap_df.drop_duplicates()
    assert len(unique_rows) < len(bootstrap_df)  # Should have duplicates

def test_get_top_correlations(sample_correlation_results):
    """Test getting top correlations."""
    top_3 = get_top_correlations(sample_correlation_results, n=3)
    
    assert len(top_3) == 3
    # Verify they are sorted by absolute correlation
    abs_corrs = top_3['correlation'].abs().values
    assert all(abs_corrs[i] >= abs_corrs[i+1] for i in range(len(abs_corrs)-1))

def test_get_top_correlations_invalid_column(sample_correlation_results):
    """Test that ValueError is raised when 'correlation' column is missing."""
    df_no_corr = sample_correlation_results.drop(columns=['correlation'])
    with pytest.raises(ValueError):
        get_top_correlations(df_no_corr)

def test_save_validation_status(temp_output_dir):
    """Test saving validation status."""
    save_validation_status(str(temp_output_dir), resampling_skipped=True, reason="Test reason")
    
    status_path = temp_output_dir / 'validation_status.json'
    assert status_path.exists()
    
    with open(status_path, 'r') as f:
        status = json.load(f)
    
    assert status['resampling_skipped'] is True
    assert status['reason'] == "Test reason"

def test_save_validation_status_not_skipped(temp_output_dir):
    """Test saving validation status when not skipped."""
    save_validation_status(str(temp_output_dir), resampling_skipped=False)
    
    status_path = temp_output_dir / 'validation_status.json'
    with open(status_path, 'r') as f:
        status = json.load(f)
    
    assert status['resampling_skipped'] is False
    assert status['reason'] == ""

def test_run_sensitivity_analysis(sample_correlation_results, temp_output_dir):
    """Test sensitivity analysis with different thresholds."""
    thresholds = [0.01, 0.05, 0.1]
    sensitivity_df = run_sensitivity_analysis(
        str(temp_output_dir / 'correlation_results.csv'),
        str(temp_output_dir),
        thresholds
    )
    
    # The function should create the results file first
    results_path = temp_output_dir / 'correlation_results.csv'
    sample_correlation_results.to_csv(results_path, index=False)
    
    # Run again with actual file
    sensitivity_df = run_sensitivity_analysis(
        str(results_path),
        str(temp_output_dir),
        thresholds
    )
    
    assert len(sensitivity_df) == len(thresholds)
    assert list(sensitivity_df['threshold']) == thresholds
    assert 'significant_count' in sensitivity_df.columns
    assert 'significant_count_fdr' in sensitivity_df.columns
    
    # Verify sensitivity report file was created
    report_path = temp_output_dir / 'sensitivity_report.csv'
    assert report_path.exists()

def test_run_sensitivity_analysis_missing_pvalue(sample_correlation_results, temp_output_dir):
    """Test that ValueError is raised when p_value column is missing."""
    df_no_pval = sample_correlation_results.drop(columns=['p_value'])
    results_path = temp_output_dir / 'correlation_results.csv'
    df_no_pval.to_csv(results_path, index=False)
    
    with pytest.raises(ValueError):
        run_sensitivity_analysis(str(results_path), str(temp_output_dir))

def test_run_bootstrap_analysis(sample_correlation_results, temp_output_dir):
    """Test bootstrap analysis execution."""
    # Save sample data
    results_path = temp_output_dir / 'correlation_results.csv'
    sample_correlation_results.to_csv(results_path, index=False)
    
    # Run bootstrap analysis
    results = run_bootstrap_analysis(
        str(results_path),
        str(temp_output_dir),
        n_iterations=100,
        seed=42
    )
    
    # Verify results structure
    assert len(results) == 5  # 5 taxa in sample data
    
    # Verify each result has required fields
    for key, value in results.items():
        assert 'taxon' in value
        assert 'sleep_variable' in value
        assert 'correlation' in value
        assert 'ci_lower' in value
        assert 'ci_upper' in value
        assert 'includes_zero' in value
    
    # Verify bootstrap results file was created
    bootstrap_path = temp_output_dir / 'bootstrap_results.json'
    assert bootstrap_path.exists()

def test_sensitivity_analysis_thresholds(sample_correlation_results, temp_output_dir):
    """Test that sensitivity analysis correctly counts significant results at different thresholds."""
    # Save sample data
    results_path = temp_output_dir / 'correlation_results.csv'
    sample_correlation_results.to_csv(results_path, index=False)
    
    # Run sensitivity analysis
    sensitivity_df = run_sensitivity_analysis(
        str(results_path),
        str(temp_output_dir),
        thresholds=[0.01, 0.05, 0.1]
    )
    
    # Verify counts match expected values from sample data
    # p_values: [0.001, 0.023, 0.156, 0.0003, 0.045]
    # At 0.01: 2 significant (0.001, 0.0003)
    # At 0.05: 4 significant (0.001, 0.023, 0.0003, 0.045)
    # At 0.1: 4 significant (same as 0.05 since 0.156 > 0.1)
    
    row_0_01 = sensitivity_df[sensitivity_df['threshold'] == 0.01].iloc[0]
    row_0_05 = sensitivity_df[sensitivity_df['threshold'] == 0.05].iloc[0]
    row_0_1 = sensitivity_df[sensitivity_df['threshold'] == 0.1].iloc[0]
    
    assert row_0_01['significant_count'] == 2
    assert row_0_05['significant_count'] == 4
    assert row_0_1['significant_count'] == 4