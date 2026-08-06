import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.lme_model import (
    calculate_vif, 
    mitigate_collinearity, 
    handle_unfulfillable_predictors, 
    validate_sufficient_trials, 
    fit_lme_model, 
    likelihood_ratio_test, 
    save_model_summary,
    run_lme_pipeline
)

@pytest.fixture
def sample_data():
    """Generate a small sample dataframe for testing."""
    np.random.seed(42)
    n = 100
    data = {
        'subject_id': ['sub_01'] * 50 + ['sub_02'] * 50,
        'search_time': np.random.normal(10, 2, n),
        'fixation_count': np.random.normal(5, 1, n),
        'target_salience': np.random.normal(0.5, 0.1, n),
        'pupil_diameter': np.random.normal(4.5, 0.5, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_data_unfulfillable(sample_data):
    """Data where target_salience is all NaN or marked unfulfillable."""
    df = sample_data.copy()
    df['target_salience'] = np.nan
    return df

@pytest.fixture
def sample_data_collinear(sample_data):
    """Data with high collinearity between predictors."""
    df = sample_data.copy()
    # Make fixation_count highly correlated with search_time
    df['fixation_count'] = df['search_time'] * 0.9 + np.random.normal(0, 0.01, len(df))
    return df

@pytest.fixture
def sample_data_low_trials():
    """Data with insufficient trials per subject."""
    data = {
        'subject_id': ['sub_01'] * 5 + ['sub_02'] * 5,
        'search_time': [1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
        'fixation_count': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        'target_salience': [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
        'pupil_diameter': [4.0, 4.1, 4.2, 4.3, 4.4, 4.0, 4.1, 4.2, 4.3, 4.4]
    }
    return pd.DataFrame(data)

def test_calculate_vif_no_collinearity(sample_data):
    predictors = ['search_time', 'fixation_count', 'target_salience']
    vifs = calculate_vif(sample_data, predictors)
    assert len(vifs) == 3
    # With random data, VIFs should be low (< 5)
    for v in vifs.values():
        assert v < 5.0

def test_calculate_vif_collinear(sample_data_collinear):
    predictors = ['search_time', 'fixation_count']
    vifs = calculate_vif(sample_data_collinear, predictors)
    # One of these should have a high VIF
    assert max(vifs.values()) > 5.0

def test_mitigate_collinearity_drops_high_vif(sample_data_collinear):
    predictors = ['search_time', 'fixation_count']
    remaining, dropped = mitigate_collinearity(sample_data_collinear, predictors, threshold=5.0)
    assert len(remaining) == 1
    assert len(dropped) == 1
    assert remaining[0] != dropped[0]

def test_handle_unfulfillable_predictors(sample_data_unfulfillable):
    predictors = ['search_time', 'fixation_count', 'target_salience']
    used, excluded = handle_unfulfillable_predictors(sample_data_unfulfillable, predictors)
    assert 'target_salience' in excluded
    assert 'search_time' in used
    assert 'fixation_count' in used

def test_validate_sufficient_trials_pass(sample_data):
    # Default min_trials is 20, we have 50 per subject
    assert validate_sufficient_trials(sample_data) is True

def test_validate_sufficient_trials_fail(sample_data_low_trials):
    # We have 5 trials per subject, default min is 20
    with pytest.raises(RuntimeError, match="Subject.*has < 20 trials"):
        validate_sufficient_trials(sample_data_low_trials)

def test_fit_lme_model(sample_data):
    formula = "pupil_diameter ~ search_time + fixation_count"
    result = fit_lme_model(sample_data, formula)
    assert result is not None
    assert hasattr(result, 'params')
    assert len(result.params) > 1

def test_likelihood_ratio_test(sample_data):
    formula_full = "pupil_diameter ~ search_time"
    formula_reduced = "pupil_diameter ~ 1"
    
    model_full = fit_lme_model(sample_data, formula_full)
    model_reduced = fit_lme_model(sample_data, formula_reduced)
    
    lrt_res = likelihood_ratio_test(model_full, model_reduced)
    assert 'chi2_statistic' in lrt_res
    assert 'p_value' in lrt_res
    assert lrt_res['chi2_statistic'] >= 0

def test_save_model_summary_creates_file(sample_data, tmp_path):
    formula = "pupil_diameter ~ search_time"
    result = fit_lme_model(sample_data, formula)
    output_path = tmp_path / "model_summary.csv"
    
    save_model_summary(result, ['search_time'], output_path)
    
    assert output_path.exists()
    df_out = pd.read_csv(output_path)
    assert 'term' in df_out.columns
    assert 'estimate' in df_out.columns
    assert 'std_error' in df_out.columns
    assert 'p_value' in df_out.columns

def test_run_lme_pipeline_integration(sample_data, tmp_path):
    input_path = tmp_path / "processed_features.csv"
    output_path = tmp_path / "model_summary.csv"
    
    sample_data.to_csv(input_path, index=False)
    
    config = {
        'thresholds': {
            'min_trials_per_subject': 10,
            'vif_threshold': 5.0
        }
    }
    
    run_lme_pipeline(input_path, output_path, config)
    
    assert output_path.exists()
    df_out = pd.read_csv(output_path)
    assert not df_out.empty
    assert 'term' in df_out.columns
    assert 'estimate' in df_out.columns
    assert 'std_error' in df_out.columns
    assert 'p_value' in df_out.columns
