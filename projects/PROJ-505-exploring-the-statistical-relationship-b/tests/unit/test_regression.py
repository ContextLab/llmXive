import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import tempfile
import os

# Add project root to path for imports
sys_path = Path(__file__).parent.parent.parent
if str(sys_path) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(sys_path))

from analysis.regression import (
    run_regression_analysis, 
    _prepare_features, 
    _calculate_vif, 
    _fit_model,
    _check_multicollinearity,
    VIF_THRESHOLD
)
from utils.logging import AnalysisError

@pytest.fixture
def sample_data():
    """Create a small synthetic dataset for testing."""
    np.random.seed(42)
    n = 100
    data = {
        'timestamp': pd.date_range('2020-01-01', periods=n, freq='H'),
        'epsilon': np.random.rand(n) * 10,
        'newell': np.random.rand(n) * 5,
        'v_bs': np.random.rand(n) * 50,
        'v_bt': np.random.rand(n) * 50,
        'O_Fe': np.random.rand(n) * 0.1,
        'He_H': np.random.rand(n) * 0.05,
        'C_O': np.random.rand(n) * 0.02,
        'Dst': np.random.randn(n) * 20,
        'Kp': np.random.rand(n) * 9
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_prepare_features(sample_data):
    """Test feature preparation logic."""
    coupling = ['epsilon', 'newell', 'v_bs', 'v_bt']
    composition = ['O_Fe', 'He_H', 'C_O']
    
    X_base, X_full, y_dst, y_kp, clean_df = _prepare_features(
        sample_data, coupling, composition
    )
    
    assert len(X_base) == len(sample_data)
    assert len(X_full) == len(sample_data)
    assert 'const' in X_base.columns
    assert 'const' in X_full.columns
    assert all(c in X_full.columns for c in composition)
    assert len(y_dst) == len(sample_data)
    assert len(y_kp) == len(sample_data)

def test_calculate_vif(sample_data):
    """Test VIF calculation."""
    X = sample_data[['epsilon', 'newell', 'v_bs', 'v_bt']].copy()
    import statsmodels.api as sm
    X = sm.add_constant(X)
    
    vif_df = _calculate_vif(X)
    
    assert 'feature' in vif_df.columns
    assert 'vif' in vif_df.columns
    assert len(vif_df) == 4 # 4 predictors
    assert not vif_df['vif'].isna().all()

def test_fit_model(sample_data):
    """Test model fitting."""
    coupling = ['epsilon', 'newell']
    composition = ['O_Fe']
    
    X_base, X_full, y_dst, y_kp, _ = _prepare_features(
        sample_data, coupling, composition
    )
    
    results = _fit_model(X_base, y_dst, "Test_Baseline")
    
    assert 'r_squared' in results
    assert 'coefficients' in results
    assert 'pvalues' in results
    assert 'vif' in results
    assert results['model_name'] == "Test_Baseline"
    assert 'epsilon' in results['coefficients']

def test_check_multicollinearity_warning(sample_data, temp_output_dir):
    """Test that high VIF triggers a warning artifact."""
    # Create data with high multicollinearity
    n = 50
    x1 = np.random.randn(n)
    x2 = x1 * 0.99 + np.random.randn(n) * 0.01 # Highly correlated
    
    df = pd.DataFrame({
        'epsilon': x1,
        'newell': x2, # VIF will be high
        'v_bs': np.random.randn(n),
        'v_bt': np.random.randn(n),
        'O_Fe': np.random.randn(n),
        'He_H': np.random.randn(n),
        'C_O': np.random.randn(n),
        'Dst': np.random.randn(n),
        'Kp': np.random.randn(n)
    })
    
    X = sm.add_constant(df[['epsilon', 'newell']])
    vif_df = _calculate_vif(X)
    
    # Verify we actually have high VIF
    high_vif_rows = vif_df[vif_df['vif'] >= VIF_THRESHOLD]
    assert len(high_vif_rows) > 0, "Test data does not have high VIF as expected"
    
    output_path = Path(temp_output_dir) / "test.json"
    _check_multicollinearity(vif_df.to_dict('records'), "Test_Model", output_path)
    
    # Check artifact file
    warning_file = Path(temp_output_dir) / "vif_warning_Test_Model.json"
    assert warning_file.exists(), "Warning artifact not created for high VIF"
    
    with open(warning_file) as f:
        content = json.load(f)
    
    assert 'highly_collinear_features' in content
    assert len(content['highly_collinear_features']) > 0

def test_run_regression_analysis(sample_data, temp_output_dir):
    """End-to-end test of regression analysis."""
    # Save sample data to parquet
    data_path = Path(temp_output_dir) / "aligned_data.parquet"
    sample_data.to_parquet(data_path)
    
    results = run_regression_analysis(str(data_path), temp_output_dir)
    
    # Check results structure
    assert 'Baseline_Dst' in results
    assert 'Full_Dst' in results
    assert 'Baseline_Kp' in results
    assert 'Full_Kp' in results
    assert 'Delta_R2_Dst' in results
    assert 'Delta_R2_Kp' in results
    
    # Check output files
    results_file = Path(temp_output_dir) / "regression_results.json"
    assert results_file.exists()
    
    coeff_file = Path(temp_output_dir) / "regression_coefficients.csv"
    assert coeff_file.exists()
    
    # Check VIF warnings if applicable (might not trigger with random data)
    # Just ensure the function didn't crash

def test_missing_columns_raises_error(sample_data, temp_output_dir):
    """Test that missing required columns raise an error."""
    # Remove a required column
    bad_data = sample_data.drop(columns=['epsilon'])
    data_path = Path(temp_output_dir) / "bad_data.parquet"
    bad_data.to_parquet(data_path)
    
    with pytest.raises(AnalysisError):
        run_regression_analysis(str(data_path), temp_output_dir)

def test_nan_handling(sample_data, temp_output_dir):
    """Test that rows with NaN are dropped."""
    # Introduce NaN
    sample_data.loc[0, 'epsilon'] = np.nan
    
    data_path = Path(temp_output_dir) / "nan_data.parquet"
    sample_data.to_parquet(data_path)
    
    # Should not raise, just drop the row
    results = run_regression_analysis(str(data_path), temp_output_dir)
    assert results['Baseline_Dst']['n_obs'] < len(sample_data)
