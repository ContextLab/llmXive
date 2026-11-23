import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.matching import (
    calculate_smd,
    estimate_propensity_scores,
    perform_matching,
    check_balance,
    run_propensity_matching
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n = 200
    
    data = {
        'pr_id': range(n),
        'file_size': np.random.normal(100, 30, n),
        'complexity_score': np.random.normal(10, 3, n),
        'review_duration': np.random.normal(50, 15, n),
        'is_llm_generated': np.random.choice([0, 1], n, p=[0.5, 0.5])
    }
    
    # Add some correlation to make matching realistic
    data['file_size'] = data['file_size'] + data['is_llm_generated'] * 20
    data['complexity_score'] = data['complexity_score'] + data['is_llm_generated'] * 2
    
    return pd.DataFrame(data)

@pytest.fixture
def temp_parquet_path(sample_data):
    """Create a temporary parquet file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
        temp_path = f.name
        sample_data.to_parquet(temp_path)
    yield temp_path
    os.unlink(temp_path)

def test_calculate_smd():
    """Test SMD calculation with known values."""
    group1 = pd.Series([1, 2, 3, 4, 5])
    group2 = pd.Series([2, 3, 4, 5, 6])
    
    smd = calculate_smd(group1, group2)
    
    # Mean difference = -1
    # Pooled std = sqrt((2.5 + 2.5)/2) = sqrt(2.5) ≈ 1.58
    # SMD = -1 / 1.58 ≈ -0.63
    
    assert abs(smd - (-0.632)) < 0.01

def test_estimate_propensity_scores(sample_data):
    """Test propensity score estimation."""
    df = sample_data.copy()
    covariates = ['file_size', 'complexity_score']
    
    result_df, model, scaler = estimate_propensity_scores(df, covariates)
    
    assert 'propensity_score' in result_df.columns
    assert len(result_df) == len(df)
    
    # Propensity scores should be between 0 and 1
    assert result_df['propensity_score'].min() >= 0
    assert result_df['propensity_score'].max() <= 1

def test_perform_matching(sample_data):
    """Test matching algorithm."""
    df = sample_data.copy()
    covariates = ['file_size', 'complexity_score']
    
    # Estimate propensity scores first
    df, _, _ = estimate_propensity_scores(df, covariates)
    
    # Perform matching
    matched_treatment, matched_control = perform_matching(
        df,
        propensity_col='propensity_score',
        treatment_col='is_llm_generated',
        ratio=1,
        caliper=0.2
    )
    
    # Check that matching occurred
    assert len(matched_treatment) > 0
    assert len(matched_control) > 0
    
    # Check that matched groups are equal size (1:1 matching)
    assert len(matched_treatment) == len(matched_control)
    
    # Check that all matched records have correct treatment labels
    assert all(matched_treatment['is_llm_generated'] == 1)
    assert all(matched_control['is_llm_generated'] == 0)

def test_check_balance(sample_data):
    """Test balance checking after matching."""
    df = sample_data.copy()
    covariates = ['file_size', 'complexity_score']
    
    # Estimate propensity scores
    df, _, _ = estimate_propensity_scores(df, covariates)
    
    # Perform matching
    matched_treatment, matched_control = perform_matching(
        df,
        propensity_col='propensity_score',
        treatment_col='is_llm_generated',
        ratio=1,
        caliper=0.2
    )
    
    # Check balance
    balance = check_balance(df, matched_treatment, matched_control, covariates)
    
    # Balance should be a dictionary
    assert isinstance(balance, dict)
    
    # All covariates should have SMD values
    for cov in covariates:
        assert cov in balance
        assert isinstance(balance[cov], float)

def test_run_propensity_matching(temp_parquet_path):
    """Test full propensity matching pipeline."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, 'matched_data.parquet')
        
        # Run matching
        result = run_propensity_matching(
            input_path=temp_parquet_path,
            output_path=output_path,
            covariates=['file_size', 'complexity', 'activity'],
            max_retries=3
        )
        
        # Check result structure
        assert result['status'] == 'success'
        assert 'matched_treatment_size' in result
        assert 'matched_control_size' in result
        assert 'covariate_balance' in result
        assert 'max_smd' in result
        
        # Check that output file was created
        assert os.path.exists(output_path)
        
        # Check balance report was created
        balance_report_path = os.path.join(temp_dir, 'covariate_balance_report.json')
        assert os.path.exists(balance_report_path)
        
        # Load and verify balance report
        with open(balance_report_path, 'r') as f:
            balance_report = json.load(f)
        
        assert 'balance' in balance_report
        assert 'max_smd' in balance_report
        assert balance_report['max_smd'] <= 0.1  # Should achieve balance

def test_excluded_covariates(temp_parquet_path):
    """Test that semantic similarity is excluded from matching."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, 'matched_data.parquet')
        
        result = run_propensity_matching(
            input_path=temp_parquet_path,
            output_path=output_path,
            covariates=['file_size', 'complexity', 'activity', 'semantic_similarity_score'],
            max_retries=3
        )
        
        # Check that semantic similarity was excluded
        assert 'semantic_similarity_score' not in result['used_covariates']
        assert 'semantic_similarity_score' in result['excluded_covariates']

def test_matching_failure_report(temp_parquet_path):
    """Test that failure report is generated when matching fails."""
    # Create data that will definitely fail to match
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create extreme imbalance
        data = pd.DataFrame({
            'pr_id': range(100),
            'file_size': [100] * 50 + [1000] * 50,  # Bimodal distribution
            'complexity_score': [5] * 50 + [50] * 50,
            'review_duration': [10] * 50 + [100] * 50,
            'is_llm_generated': [1] * 50 + [0] * 50  # Perfect separation
        })
        
        input_path = os.path.join(temp_dir, 'extreme_data.parquet')
        data.to_parquet(input_path)
        
        output_path = os.path.join(temp_dir, 'matched_data.parquet')
        
        # This should fail and generate a failure report
        with pytest.raises(RuntimeError):
            run_propensity_matching(
                input_path=input_path,
                output_path=output_path,
                covariates=['file_size', 'complexity', 'activity'],
                max_retries=0  # No retries to force failure
            )
        
        # Check that failure report was created
        failure_report_path = os.path.join(temp_dir, 'matching_failure_report.json')
        assert os.path.exists(failure_report_path)
        
        with open(failure_report_path, 'r') as f:
            failure_report = json.load(f)
        
        assert failure_report['status'] == 'failed'
        assert 'max_smd' in failure_report
        assert 'covariate_smd' in failure_report
        assert 'retry_count' in failure_report