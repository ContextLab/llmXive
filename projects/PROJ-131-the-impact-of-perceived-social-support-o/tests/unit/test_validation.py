import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import tempfile
import os

# Import the functions to test
from code.analysis.validation import (
    check_harassment_variance,
    check_social_support_variance,
    check_vif,
    validate_synthetic_cohort
)

def create_test_dataframe():
    """Create a mock dataframe that should pass validation."""
    n = 200
    np.random.seed(42)
    
    # Create variables with reasonable variance
    data = {
        'harassment_exposure': np.random.binomial(1, 0.4, n), # SD ~ 0.49, N_exposed ~ 80
        'social_support': np.random.normal(50, 10, n),       # SD ~ 10
        'age': np.random.normal(30, 10, n),
        'gender': np.random.binomial(1, 0.5, n),
        'education': np.random.normal(14, 2, n),
        'income': np.random.normal(50000, 15000, n),
    }
    
    # Ensure harassment_exposure has enough variance
    if data['harassment_exposure'].std() < 0.2:
        data['harassment_exposure'] = np.random.binomial(1, 0.5, n)
    
    return pd.DataFrame(data)

def test_check_harassment_variance_pass():
    df = create_test_dataframe()
    result = check_harassment_variance(df, threshold_sd=0.2, min_exposed_n=30)
    assert result['passed'] is True
    assert result['details']['n_exposed'] >= 30
    assert result['details']['sd'] > 0.2

def test_check_harassment_variance_fail_sd():
    df = create_test_dataframe()
    # Force low SD
    df['harassment_exposure'] = 1  # All 1s -> SD = 0
    result = check_harassment_variance(df, threshold_sd=0.2)
    assert result['passed'] is False

def test_check_harassment_variance_fail_n():
    df = create_test_dataframe()
    # Force low N exposed
    df.loc[df.index[:190], 'harassment_exposure'] = 0
    result = check_harassment_variance(df, min_exposed_n=30)
    assert result['passed'] is False

def test_check_social_support_variance_pass():
    df = create_test_dataframe()
    result = check_social_support_variance(df, threshold_sd=0.5)
    assert result['passed'] is True
    assert result['details']['sd'] > 0.5

def test_check_social_support_variance_fail():
    df = create_test_dataframe()
    df['social_support'] = 50  # SD = 0
    result = check_social_support_variance(df, threshold_sd=0.5)
    assert result['passed'] is False

def test_check_vif_pass():
    df = create_test_dataframe()
    result = check_vif(df, covariates=['age', 'gender', 'education', 'income'])
    assert result['passed'] is True
    assert result['details']['max_vif'] < 5.0

def test_validate_synthetic_cohort_full_flow():
    df = create_test_dataframe()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "intermediate_cohort.csv"
        output_path = Path(tmpdir) / "validation_report.json"
        
        df.to_csv(input_path, index=False)
        
        # Should not raise
        validate_synthetic_cohort(input_path, output_path)
        
        assert output_path.exists()
        
        with open(output_path) as f:
            report = json.load(f)
        
        assert report['overall_passed'] is True
        assert len(report['checks']) == 3
        assert all(c['passed'] for c in report['checks'])

def test_validate_synthetic_cohort_fail():
    df = create_test_dataframe()
    # Corrupt data to fail VIF (perfect multicollinearity)
    df['harassment_exposure'] = df['social_support'] # Perfect correlation with interaction logic likely to spike VIF or fail
    # Actually, let's just force low variance to fail the first check
    df['harassment_exposure'] = 0 
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "intermediate_cohort.csv"
        output_path = Path(tmpdir) / "validation_report.json"
        
        df.to_csv(input_path, index=False)
        
        with pytest.raises(Exception) as exc_info:
            validate_synthetic_cohort(input_path, output_path)
        
        assert "E-VALIDATION-001" in str(exc_info.value)