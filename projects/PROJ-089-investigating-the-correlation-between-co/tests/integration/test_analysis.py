import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Import functions from analysis module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis import (
    check_vif,
    fit_mixed_effects_model,
    calculate_partial_correlations,
    run_meta_analysis,
    run_sensitivity_analysis,
    run_analysis
)

@pytest.fixture
def sample_data():
    """Generate a synthetic dataset with known correlation for testing."""
    np.random.seed(42)
    n = 100
    repo_ids = np.random.choice(['repo_A', 'repo_B', 'repo_C'], n)
    
    # Create variables with a known correlation
    # Let's say total_lines_changed and debt_score have a true correlation of 0.5
    total_lines = np.random.normal(100, 50, n)
    debt_score = 0.5 * total_lines + np.random.normal(0, 20, n)
    avg_loc = np.random.normal(50, 10, n)
    project_age = np.random.normal(5, 2, n)
    contributor_count = np.random.randint(1, 10, n)
    language = np.random.choice(['Python', 'Java', 'JS'], n)
    
    df = pd.DataFrame({
        'repo_id': repo_ids,
        'total_lines_changed': total_lines,
        'debt_score': debt_score,
        'avg_loc': avg_loc,
        'project_age': project_age,
        'contributor_count': contributor_count,
        'language': language
    })
    return df

def test_vif_check(sample_data):
    """Test VIF calculation on known data."""
    covariates = ['project_age', 'contributor_count'] # language is object, skip for now or encode
    vif_results, high_coll = check_vif(sample_data, covariates)
    
    assert isinstance(vif_results, dict)
    assert 'project_age' in vif_results or 'contributor_count' in vif_results
    # With random data, VIF should be low (< 5)
    assert high_coll == False, "Random data should not trigger high collinearity"

def test_partial_correlation_known(sample_data):
    """Test partial correlation with a dataset that has a known correlation."""
    # We expect a positive correlation between total_lines_changed and debt_score
    # controlling for avg_loc
    result = calculate_partial_correlations(
        sample_data,
        x_col='total_lines_changed',
        y_col='debt_score',
        control_cols=['avg_loc']
    )
    
    assert 'pearson_r' in result
    assert 'pearson_p' in result
    # Check that correlation is positive and significant (p < 0.05)
    assert result['pearson_r'] > 0.3, f"Expected positive correlation, got {result['pearson_r']}"
    assert result['pearson_p'] < 0.05, f"Expected significant p-value, got {result['pearson_p']}"

def test_mixed_effects_model(sample_data):
    """Test mixed-effects model fitting."""
    fixed_effects = ['total_lines_changed', 'avg_loc', 'contributor_count']
    result = fit_mixed_effects_model(
        sample_data,
        fixed_effects=fixed_effects,
        random_group='repo_id'
    )
    
    assert 'coefficients' in result
    assert 'pvalues' in result
    assert 'summary' in result
    # Check that the coefficient for total_lines_changed is present
    assert 'total_lines_changed' in result['coefficients']

def test_meta_analysis():
    """Test meta-analysis function."""
    # Create fake correlation results
    mock_results = [
        {'r': 0.3, 'n': 50},
        {'r': 0.4, 'n': 60},
        {'r': 0.35, 'n': 55}
    ]
    
    result = run_meta_analysis(mock_results)
    
    assert 'pooled_r' in result
    assert 'p_value' in result
    assert result['k_studies'] == 3
    # Pooled r should be around the average of the inputs
    assert 0.3 < result['pooled_r'] < 0.45

def test_sensitivity_analysis(sample_data):
    """Test sensitivity analysis with different thresholds."""
    result_df = run_sensitivity_analysis(sample_data, thresholds=[10, 50])
    
    assert isinstance(result_df, pd.DataFrame)
    assert 'threshold' in result_df.columns
    assert len(result_df) == 2
    # Check that results are generated for each threshold
    assert not result_df['pearson_r'].isna().all()

def test_full_run_analysis(sample_data, tmp_path):
    """Test the full run_analysis pipeline."""
    # Save sample data to a temp CSV
    input_file = tmp_path / "unified_metrics.csv"
    sample_data.to_csv(input_file, index=False)
    
    output_dir = tmp_path / "results"
    
    results = run_analysis(str(input_file), str(output_dir))
    
    assert 'vif' in results
    assert 'mixed_effects' in results
    assert 'partial_correlations' in results
    assert 'meta_analysis' in results
    assert 'sensitivity' in results
    
    # Check output files exist
    assert (output_dir / 'correlation_results.csv').exists()
    assert (output_dir / 'sensitivity_analysis.csv').exists()
    assert (output_dir / 'meta_analysis_results.csv').exists()
    assert (output_dir / 'mixed_model_summary.txt').exists()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])