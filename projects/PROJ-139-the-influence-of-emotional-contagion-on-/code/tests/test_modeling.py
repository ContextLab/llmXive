import os
import json
import tempfile
import warnings
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from code.data.modeling import (
    run_sensitivity_analysis,
    load_processed_data,
    fit_glmm_with_random_intercepts,
    run_wald_tests,
    apply_multiple_comparison_correction
)

# Mock data fixture for integration testing
@pytest.fixture
def sample_thread_data():
    """Generate synthetic data for testing modeling functions."""
    np.random.seed(42)
    n = 200
    # Create data that mimics real output structure from metrics/validation
    data = {
        'thread_id': range(n),
        'agreement_proportion': np.random.uniform(0.1, 0.95, n),
        'entropy': np.random.uniform(0.2, 2.5, n),
        'contagion_correlation': np.random.uniform(-0.5, 0.8, n),
        'time_to_decision': np.random.exponential(100, n), # Gamma-like
        'seed_sentiment': np.random.uniform(-1, 1, n),
        'contagion_slope': np.random.uniform(-0.5, 0.5, n),
        'reply_count': np.random.randint(5, 50, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_processed_dir(sample_thread_data):
    """Create a temporary directory with valid_threads.csv."""
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_path = Path(tmpdir) / "processed"
        processed_path.mkdir()
        csv_path = processed_path / "valid_threads.csv"
        sample_thread_data.to_csv(csv_path, index=False)
        yield csv_path

def test_run_sensitivity_analysis_direct(sample_thread_data):
    """Test sensitivity analysis function directly with a dataframe."""
    # Run analysis
    result_df = run_sensitivity_analysis(
        sample_thread_data,
        agreement_cutoffs=[0.2, 0.5],
        entropy_thresholds=[1.0, 2.0]
    )
    
    # Assertions
    assert isinstance(result_df, pd.DataFrame)
    assert 'agreement_cutoff' in result_df.columns
    assert 'entropy_threshold' in result_df.columns
    assert 'correlation_coefficient' in result_df.columns
    assert len(result_df) == 4 # 2 cutoffs * 2 thresholds
    
    # Check that correlation coefficients are numeric (or NaN)
    assert result_df['correlation_coefficient'].apply(lambda x: isinstance(x, (float, int)) or pd.isna(x)).all()

def test_run_sensitivity_analysis_empty_subset(sample_thread_data):
    """Test when filters result in empty dataset."""
    # Use extreme cutoffs that should result in empty set
    result_df = run_sensitivity_analysis(
        sample_thread_data,
        agreement_cutoffs=[0.99],
        entropy_thresholds=[0.0] 
    )
    
    # Should still return a row, but with NaN correlation and n=0
    assert len(result_df) > 0

def test_run_sensitivity_analysis_missing_columns(sample_thread_data):
    """Test handling of missing columns."""
    df_missing = sample_thread_data.drop(columns=['agreement_proportion'])
    with pytest.raises(ValueError, match="agreement_proportion"):
        run_sensitivity_analysis(df_missing)

def test_fit_glmm_convergence(sample_thread_data):
    """Integration test: Verify GLMM fitting converges on synthetic data."""
    # Prepare data for beta regression (bounded outcome)
    # Beta regression requires outcome in (0, 1)
    df = sample_thread_data.copy()
    # Ensure agreement_proportion is strictly within (0, 1)
    df['agreement_proportion'] = df['agreement_proportion'].clip(0.01, 0.99)
    
    # Fit the model
    # We expect this to return a statsmodels GLM object (beta family)
    model_result = fit_glmm_with_random_intercepts(
        df,
        outcome='agreement_proportion',
        predictors=['seed_sentiment', 'contagion_slope'],
        random_effect='thread_id',
        family='beta'
    )
    
    # Verify the result object exists and has expected attributes
    assert model_result is not None
    assert hasattr(model_result, 'converged')
    assert model_result.converged is True, "GLMM did not converge on valid synthetic data"
    
    # Verify coefficients exist
    assert hasattr(model_result, 'params')
    assert len(model_result.params) > 0

def test_fit_gamma_regression_convergence(sample_thread_data):
    """Integration test: Verify Gamma GLM convergence for time-to-decision."""
    df = sample_thread_data.copy()
    # Ensure positive values for Gamma
    df['time_to_decision'] = df['time_to_decision'].clip(lower=1.0)
    
    model_result = fit_glmm_with_random_intercepts(
        df,
        outcome='time_to_decision',
        predictors=['seed_sentiment'],
        random_effect='thread_id',
        family='gamma'
    )
    
    assert model_result is not None
    assert model_result.converged is True

def test_run_wald_tests(sample_thread_data):
    """Integration test: Verify Wald tests run and return p-values."""
    df = sample_thread_data.copy()
    df['agreement_proportion'] = df['agreement_proportion'].clip(0.01, 0.99)
    
    model_result = fit_glmm_with_random_intercepts(
        df,
        outcome='agreement_proportion',
        predictors=['seed_sentiment', 'contagion_slope'],
        random_effect='thread_id',
        family='beta'
    )
    
    # Run Wald tests
    wald_results = run_wald_tests(model_result)
    
    assert isinstance(wald_results, pd.DataFrame)
    assert 'term' in wald_results.columns
    assert 'p_value' in wald_results.columns
    assert len(wald_results) > 0
    # P-values should be between 0 and 1
    assert (wald_results['p_value'] >= 0).all()
    assert (wald_results['p_value'] <= 1).all()

def test_multiple_comparison_correction_applied(sample_thread_data):
    """Integration test: Verify multiple comparison correction is applied."""
    # Create a scenario with multiple p-values
    df = sample_thread_data.copy()
    df['agreement_proportion'] = df['agreement_proportion'].clip(0.01, 0.99)
    
    model_result = fit_glmm_with_random_intercepts(
        df,
        outcome='agreement_proportion',
        predictors=['seed_sentiment', 'contagion_slope', 'entropy'],
        random_effect='thread_id',
        family='beta'
    )
    
    wald_results = run_wald_tests(model_result)
    
    # Apply correction (Benjamini-Hochberg FDR)
    corrected_results = apply_multiple_comparison_correction(wald_results)
    
    assert isinstance(corrected_results, pd.DataFrame)
    assert 'p_value_corrected' in corrected_results.columns
    
    # Check that corrected p-values are monotonic or at least valid
    # (FDR correction ensures adjusted p-values are non-decreasing when sorted)
    assert (corrected_results['p_value_corrected'] >= 0).all()
    assert (corrected_results['p_value_corrected'] <= 1).all()
    
    # Verify that if we have 3+ tests, correction was actually applied
    # (corrected values should generally be >= original values)
    original_p = wald_results['p_value']
    corrected_p = corrected_results['p_value_corrected']
    
    # At least some corrected values should be different or equal (never smaller than original)
    assert (corrected_p >= original_p).all(), "Corrected p-values should not be smaller than original"

def test_modeling_pipeline_integration(temp_processed_dir):
    """End-to-end integration test: Run full modeling pipeline on valid threads."""
    # This test verifies that the pipeline can load data, fit models, and output results
    # without crashing, assuming the data file exists.
    
    # Note: We cannot easily test the full pipeline without mocking the config
    # to point to our temp directory, so we test the core functions that compose it.
    
    df = load_processed_data(temp_processed_dir.parent.parent / "processed" / "valid_threads.csv")
    
    # Verify data loaded
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    
    # Run a simplified version of the modeling pipeline steps
    # 1. Fit Beta Regression
    df['agreement_proportion'] = df['agreement_proportion'].clip(0.01, 0.99)
    beta_model = fit_glmm_with_random_intercepts(
        df, 'agreement_proportion', ['seed_sentiment'], 'thread_id', 'beta'
    )
    assert beta_model.converged
    
    # 2. Run Wald Tests
    wald_results = run_wald_tests(beta_model)
    assert len(wald_results) > 0
    
    # 3. Apply Correction
    corrected = apply_multiple_comparison_correction(wald_results)
    assert 'p_value_corrected' in corrected.columns

def test_empty_dataframe_handling():
    """Test that modeling functions handle empty dataframes gracefully."""
    empty_df = pd.DataFrame(columns=['thread_id', 'agreement_proportion', 'seed_sentiment'])
    
    with pytest.raises(ValueError, match="Empty dataset"):
        fit_glmm_with_random_intercepts(
            empty_df, 'agreement_proportion', ['seed_sentiment'], 'thread_id', 'beta'
        )