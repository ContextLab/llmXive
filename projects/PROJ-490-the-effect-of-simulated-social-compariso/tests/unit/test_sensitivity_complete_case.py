import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.sensitivity import run_threshold_sensitivity_sweep, run_sensitivity_analysis

@pytest.fixture
def sample_df():
    """Create a sample dataframe with some missing values."""
    np.random.seed(42)
    n = 200
    df = pd.DataFrame({
        'pre_self_esteem': np.random.normal(5, 1, n),
        'post_self_esteem': np.random.normal(5, 1, n),
        'avatar_condition': np.random.choice([0, 1], n),
        'comparison_tendency': np.random.normal(0, 1, n)
    })
    
    # Introduce some missing values (10% missingness)
    mask = np.random.random(df.shape) < 0.10
    df[mask] = np.nan
    
    return df

def test_complete_case_baseline_exists(sample_df):
    """Test that complete case baseline is included in sensitivity sweep."""
    formula = "post_self_esteem ~ pre_self_esteem + C(avatar_condition) + comparison_tendency + C(avatar_condition):comparison_tendency"
    
    results = run_threshold_sensitivity_sweep(sample_df, formula)
    
    # Assert complete case condition exists
    assert 'complete_case' in results, "Complete case baseline must be included"
    assert results['complete_case']['status'] == 'success', "Complete case should succeed with sufficient data"
    assert results['complete_case']['method'] == 'complete_case'
    assert 'coefficients' in results['complete_case']

def test_complete_case_has_fewer_rows(sample_df):
    """Test that complete case has fewer rows than other conditions (due to dropping NaN)."""
    formula = "post_self_esteem ~ pre_self_esteem + C(avatar_condition) + comparison_tendency + C(avatar_condition):comparison_tendency"
    
    results = run_threshold_sensitivity_sweep(sample_df, formula)
    
    if 'complete_case' in results and results['complete_case']['status'] == 'success':
        cc_rows = results['complete_case']['n_rows']
        
        # Check that 0.20 condition has more or equal rows
        if '0.20' in results and results['0.20']['status'] == 'success':
            assert results['0.20']['n_rows'] >= cc_rows, "Complete case should have fewer rows than imputed"

def test_bias_calculation_relative_to_baseline(sample_df):
    """Test that bias is calculated relative to complete case baseline."""
    formula = "post_self_esteem ~ pre_self_esteem + C(avatar_condition) + comparison_tendency + C(avatar_condition):comparison_tendency"
    
    results = run_threshold_sensitivity_sweep(sample_df, formula)
    
    if 'complete_case' in results and results['complete_case']['status'] == 'success':
        # Check that other conditions have bias_vs_baseline
        for condition in ['low', '0.15', '0.20']:
            if condition in results and results[condition]['status'] == 'success':
                assert 'bias_vs_baseline' in results[condition], f"{condition} should have bias_vs_baseline"
                if results[condition]['bias_vs_baseline']:
                    assert 'interaction_bias' in results[condition]['bias_vs_baseline']

def test_sensitivity_analysis_includes_complete_case(sample_df):
    """Integration test: full sensitivity analysis includes complete case."""
    # Mock config to avoid file I/O issues in test
    import analysis.sensitivity as sens_module
    original_get_config = sens_module.get_config
    
    def mock_get_config():
        return {
            'data_source_type': 'synthetic',
            'paths': {
                'imputed_data_csv': '/tmp/fake_imputed.csv',
                'sensitivity_results_json': '/tmp/fake_sensitivity.json'
            }
        }
    
    sens_module.get_config = mock_get_config
    
    try:
        # Save original df and write to temp
        temp_path = '/tmp/fake_imputed.csv'
        sample_df.to_csv(temp_path)
        
        results = run_sensitivity_analysis()
        
        assert 'threshold_sweep' in results
        assert 'complete_case' in results['threshold_sweep']
        assert results['threshold_sweep']['complete_case']['status'] == 'success'
        assert results['baseline_condition'] == 'complete_case'
        
        # Clean up
        os.remove(temp_path)
    finally:
        sens_module.get_config = original_get_config
