import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from sensitivity_analysis import run_sensitivity_sweep, calculate_deviation_report, report_sensitivity_results

@pytest.fixture
def sample_csv():
    """Create a temporary CSV file with sample simulation results."""
    data = [
        ['seed', 'N', 'p', 'avg_degree', 'conductivity', 'percolation_flag', 'scaling_factor'],
        [42, 50, 0.1, 4.0, 100.0, 1, 0.8],
        [123, 50, 0.1, 4.0, 120.0, 1, 0.8],
        [456, 100, 0.1, 4.0, 150.0, 1, 0.8]
    ]
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        writer = csv.writer(f)
        writer.writerows(data)
        return f.name

def test_sensitivity_sweep(sample_csv):
    """Verify that sensitivity sweep runs and produces expected deviations."""
    # Mock config (not strictly needed for this function but good practice)
    class MockConfig:
        pass
        
    result_df = run_sensitivity_sweep(sample_csv, MockConfig())
    
    assert not result_df.empty
    assert 'perturbation' in result_df.columns
    assert 'deviation' in result_df.columns
    
    # Check that perturbations are -0.1, 0.0, 0.1
    unique_perturbations = set(result_df['perturbation'].unique())
    assert unique_perturbations == {-0.1, 0.0, 0.1}
    
    # Check that deviation for 0.0 perturbation is 0
    zero_perturbation_rows = result_df[result_df['perturbation'] == 0.0]
    assert all(zero_perturbation_rows['deviation'] == 0.0)
    
    # Check that deviations for +/- 0.1 are approx 0.1 (linear model)
    pos_pert = result_df[result_df['perturbation'] == 0.1]['deviation'].values
    neg_pert = result_df[result_df['perturbation'] == -0.1]['deviation'].values
    
    assert np.allclose(pos_pert, 0.1, atol=0.01)
    assert np.allclose(neg_pert, 0.1, atol=0.01)
    
    os.unlink(sample_csv)

def test_deviation_report(sample_csv):
    """Verify deviation report calculation."""
    class MockConfig:
        pass
        
    result_df = run_sensitivity_sweep(sample_csv, MockConfig())
    report = calculate_deviation_report(result_df)
    
    assert 'mean_deviation' in report
    assert 'max_deviation' in report
    assert 'min_deviation' in report
    
    # In our linear model, max deviation should be 0.1
    assert report['max_deviation'] == 0.1
    assert report['min_deviation'] == 0.0
    
    os.unlink(sample_csv)
    
def test_report_sensitivity_results(sample_csv):
    """Verify that sensitivity results are appended to CSV."""
    class MockConfig:
        pass
        
    result_df = run_sensitivity_sweep(sample_csv, MockConfig())
    report = calculate_deviation_report(result_df)
    
    report_sensitivity_results(sample_csv, result_df, report)
    
    # Read back and check columns
    df = pd.read_csv(sample_csv)
    assert 'sensitivity_deviation' in df.columns
    assert 'sensitivity_min' in df.columns
    assert 'sensitivity_max' in df.columns
    
    # Check values are populated
    assert not df['sensitivity_deviation'].isna().all()
    
    os.unlink(sample_csv)