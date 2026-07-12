import pytest
import pandas as pd
import numpy as np
import os
import json
import tempfile
from code.analyze import (
    load_experiment_data,
    perform_piecewise_regression,
    calculate_vif,
    fit_logistic_quadratic,
    find_tipping_point_logistic,
    run_analysis
)

@pytest.fixture
def sample_data_csv(tmp_path):
    """Create a temporary CSV file with sample experiment data."""
    data = {
        'library_size': [10, 30, 50, 70, 100] * 10,
        'success': [1, 1, 1, 0, 0] * 10,
        'total_redundancy': [0.1, 0.2, 0.3, 0.4, 0.5] * 10,
        'task_id': [f"task_{i}" for i in range(50)],
        'skill_id': [f"skill_{i%10}" for i in range(50)],
        'latency': [0.5] * 50,
        'tokens': [100] * 50,
        'retrieval_precision': [0.8] * 50,
        'retrieval_diversity': [0.2] * 50,
        'pruning_risk_count': [0] * 50,
        'pruning_enabled': [True] * 50
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "experiment_log.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)

def test_load_experiment_data(sample_data_csv):
    df = load_experiment_data(sample_data_csv)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 50
    assert 'library_size' in df.columns
    assert 'success' in df.columns

def test_piecewise_regression(sample_data_csv):
    df = load_experiment_data(sample_data_csv)
    result = perform_piecewise_regression(df)
    assert 'breakpoint' in result
    assert 'slope_pre' in result
    assert 'slope_post' in result
    assert 10 <= result['breakpoint'] <= 100

def test_calculate_vif(sample_data_csv):
    df = load_experiment_data(sample_data_csv)
    vif_result = calculate_vif(df)
    assert 'library_size' in vif_result
    assert 'total_redundancy' in vif_result
    # VIF should be finite for uncorrelated enough data
    assert np.isfinite(vif_result['library_size'])
    assert np.isfinite(vif_result['total_redundancy'])

def test_find_tipping_point_logistic():
    # Test case: beta1 = -2, beta2 = 0.5 -> x = -(-2)/(2*0.5) = 2
    beta0, beta1, beta2 = 0.0, -2.0, 0.5
    x0 = find_tipping_point_logistic(beta0, beta1, beta2)
    assert np.isclose(x0, 2.0)

    # Test case: beta1 = 4, beta2 = -1 -> x = -4/(2*-1) = 2
    beta0, beta1, beta2 = 0.0, 4.0, -1.0
    x0 = find_tipping_point_logistic(beta0, beta1, beta2)
    assert np.isclose(x0, 2.0)

def test_fit_logistic_quadratic(sample_data_csv):
    df = load_experiment_data(sample_data_csv)
    result = fit_logistic_quadratic(df)
    assert 'beta0' in result
    assert 'beta1' in result
    assert 'beta2' in result
    assert 'tipping_point_original' in result
    # The optimization should converge (or at least attempt)
    assert isinstance(result['tipping_point_original'], (float, type(None)))

def test_run_analysis(sample_data_csv):
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = os.path.join(tmp_dir, "analysis.json")
        results = run_analysis(sample_data_csv)
        
        assert 'piecewise_regression' in results
        assert 'logistic_regression_quadratic' in results
        assert 'tipping_point_from_logistic' in results
        assert 'vif_metrics' in results
        
        # Verify the output file would be written correctly if we ran the main block
        # (Here we just check the structure returned by the function)
        assert results['tipping_point_from_logistic'] is not None or \
               results['logistic_regression_quadratic']['success'] is False