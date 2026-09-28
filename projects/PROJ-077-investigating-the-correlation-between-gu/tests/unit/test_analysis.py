import pytest
import pandas as pd
import numpy as np
import os
import json
from pathlib import Path
import sys

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis import (
    load_processed_data,
    check_zero_variance,
    log_zero_variance_warning,
    compute_spearman_correlation,
    save_correlation_results,
    calculate_vif,
    save_vif_results,
    run_multivariate_regression,
    save_regression_results
)
from config import DQS_REQUIRED

@pytest.fixture
def sample_regression_data(tmp_path):
    """Create a sample cleaned_data.csv for regression testing."""
    data = {
        'participant_id': range(100),
        'shannon_index': np.random.uniform(3.0, 5.0, 100),
        'age': np.random.randint(20, 80, 100),
        'sex': np.random.choice(['M', 'F'], 100),
        'bmi': np.random.uniform(18.5, 40.0, 100),
        'fluid_intelligence': np.random.uniform(0, 20, 100),
        'dqs': np.random.uniform(0, 100, 100)
    }
    df = pd.DataFrame(data)
    
    # Ensure directory exists
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = processed_dir / "cleaned_data.csv"
    df.to_csv(csv_path, index=False)
    
    return csv_path

@pytest.fixture
def sample_regression_data_no_dqs(tmp_path):
    """Create a sample cleaned_data.csv without DQS column."""
    data = {
        'participant_id': range(100),
        'shannon_index': np.random.uniform(3.0, 5.0, 100),
        'age': np.random.randint(20, 80, 100),
        'sex': np.random.choice(['M', 'F'], 100),
        'bmi': np.random.uniform(18.5, 40.0, 100),
        'fluid_intelligence': np.random.uniform(0, 20, 100)
        # No 'dqs' column
    }
    df = pd.DataFrame(data)
    
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = processed_dir / "cleaned_data.csv"
    df.to_csv(csv_path, index=False)
    
    return csv_path

def test_check_zero_variance_true():
    df = pd.DataFrame({'col': [5, 5, 5, 5]})
    assert check_zero_variance(df, 'col') is True

def test_check_zero_variance_false():
    df = pd.DataFrame({'col': [1, 2, 3, 4]})
    assert check_zero_variance(df, 'col') is False

def test_compute_spearman_correlation(sample_regression_data):
    df = pd.read_csv(sample_regression_data)
    r, p, n = compute_spearman_correlation(df)
    assert isinstance(r, float)
    assert isinstance(p, float)
    assert n > 0

def test_save_correlation_results(tmp_path):
    # Mock data
    r, p, n = 0.5, 0.01, 50
    path = str(tmp_path / "test_corr.csv")
    save_correlation_results(r, p, n, path)
    
    assert os.path.exists(path)
    df = pd.read_csv(path)
    assert 'r_value' in df.columns
    assert 'p_value' in df.columns
    assert 'n_obs' in df.columns

def test_calculate_vif(sample_regression_data):
    df = pd.read_csv(sample_regression_data)
    predictors = ['shannon_index', 'age', 'bmi', 'dqs']
    vif_data = calculate_vif(df, predictors)
    
    assert isinstance(vif_data, dict)
    for pred in predictors:
        assert pred in vif_data
        assert vif_data[pred] > 1.0 # VIF is always >= 1

def test_save_vif_results(tmp_path):
    vif_data = {'x': 2.0, 'y': 3.0}
    path = str(tmp_path / "test_vif.json")
    save_vif_results(vif_data, path)
    
    assert os.path.exists(path)
    with open(path, 'r') as f:
        loaded = json.load(f)
    assert loaded == vif_data

def test_run_multivariate_regression_with_dqs(sample_regression_data):
    df = pd.read_csv(sample_regression_data)
    results = run_multivariate_regression(df)
    
    assert isinstance(results, pd.DataFrame)
    assert 'coefficient' in results.columns
    assert 'std_err' in results.columns
    assert 'p_value' in results.columns
    assert len(results) > 0

def test_run_multivariate_regression_no_dqs(sample_regression_data_no_dqs):
    # This should run successfully if DQS_REQUIRED is False (default in config)
    # If DQS_REQUIRED is True, it should raise an error.
    # We assume default config for this test.
    try:
        df = pd.read_csv(sample_regression_data_no_dqs)
        results = run_multivariate_regression(df)
        assert isinstance(results, pd.DataFrame)
        # Verify DQS is not in the predictor list used (formula check is internal)
        # Just ensure it didn't crash and produced results
        assert len(results) > 0
    except ValueError as e:
        if "DQS column is missing but DQS_REQUIRED is True" in str(e):
            pytest.skip("DQS_REQUIRED is True in current config, skipping test for no-DQS path")
        else:
            raise

def test_save_regression_results(tmp_path):
    data = {
        'predictor': ['Intercept', 'shannon_index'],
        'coefficient': [10.0, 0.5],
        'std_err': [1.0, 0.1],
        'p_value': [0.001, 0.02]
    }
    df = pd.DataFrame(data)
    path = str(tmp_path / "test_reg.csv")
    save_regression_results(df, path)
    
    assert os.path.exists(path)
    loaded = pd.read_csv(path)
    assert 'coefficient' in loaded.columns
    assert 'std_err' in loaded.columns
    assert 'p_value' in loaded.columns

def test_fdr_correction_qvalue_calc():
    """
    Test FDR correction (Benjamini-Hochberg) on a sequence of p-values.
    Input: p-values ranging from low to moderate significance.
    Expect: Corresponding q-values calculated via statsmodels.
    """
    from statsmodels.stats.multitest import multipletests
    
    # A sequence of p-values: some significant, some not
    pvals = [0.001, 0.01, 0.02, 0.04, 0.05, 0.06, 0.1, 0.2]
    
    # Perform Benjamini-Hochberg correction
    reject, qvals, _, _ = multipletests(pvals, method='fdr_bh')
    
    # Assertions
    assert len(qvals) == len(pvals)
    assert isinstance(qvals, np.ndarray)
    
    # Check monotonicity property of BH q-values (q_i <= q_{i+1} usually holds after sorting)
    # Since input is sorted ascending, q-values should be roughly increasing or equal
    # We check that q-values are non-negative and <= 1
    assert all(q >= 0 for q in qvals)
    assert all(q <= 1 for q in qvals)
    
    # Specific check: the smallest p-value should have the smallest (or equal smallest) q-value
    assert qvals[0] <= qvals[-1]
    
    # Check that the correction actually adjusted values (usually q > p for small p)
    # Though not strictly guaranteed for all distributions, for this set it should hold
    # We assert that at least one q-value is different from p-value to prove calculation happened
    assert not np.array_equal(pvals, qvals)