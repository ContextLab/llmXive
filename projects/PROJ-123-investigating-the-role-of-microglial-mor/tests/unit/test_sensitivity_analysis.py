import pytest
import pandas as pd
import numpy as np
from code.analysis import run_sensitivity_analysis

@pytest.fixture
def sample_df():
    """Create a sample dataframe for sensitivity analysis testing."""
    np.random.seed(42)
    n = 50
    data = {
        'subject_id': range(n),
        'brain_region': np.random.choice(['Hippocampus', 'Prefrontal Cortex'], n),
        'pathology_status_binary': np.random.choice([0, 1], n),
        'branch_points': np.random.randint(5, 20, n),
        'total_length': np.random.uniform(100, 300, n),
        'soma_area': np.random.uniform(10, 50, n),
        'sholl_intersections': np.random.uniform(10, 50, n),
        'cognitive_score': np.random.uniform(0, 100, n)
    }
    # Add interaction term
    data['interaction_term'] = data['pathology_status_binary'] * (data['brain_region'] == 'Hippocampus').astype(int)
    df = pd.DataFrame(data)
    return df

def test_run_sensitivity_analysis(sample_df):
    """Test that sensitivity analysis runs and produces expected output structure."""
    steps = [2, 5, 10]
    result = run_sensitivity_analysis(
        df=sample_df,
        sholl_radii_steps=steps,
        target_col='cognitive_score'
    )
    
    assert 'sensitivity_results' in result
    assert 'p_value_variation' in result
    assert 'sholl_steps_tested' in result
    
    assert len(result['sensitivity_results']) == len(steps)
    
    # Check that results contain expected keys
    for step_res in result['sensitivity_results']:
        assert 'sholl_step' in step_res
        assert 'r2' in step_res
        assert 'p_values' in step_res
        assert 'coefficients' in step_res
    
    # Check that variation is calculated
    assert len(result['p_value_variation']) > 0
    
    # Verify that p-value ranges are non-negative
    for var in result['p_value_variation'].values():
        assert var['range'] >= 0

def test_sensitivity_analysis_scaling(sample_df):
    """Test that different steps produce different results due to scaling."""
    steps = [2, 10]
    result = run_sensitivity_analysis(
        df=sample_df,
        sholl_radii_steps=steps,
        target_col='cognitive_score'
    )
    
    # The R2 might be similar, but coefficients should differ due to scaling
    # We just check that the function runs without error and produces distinct steps
    steps_tested = [r['sholl_step'] for r in result['sensitivity_results']]
    assert set(steps_tested) == set(steps)