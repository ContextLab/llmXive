"""
Integration tests for the full data pipeline and analysis.
"""
import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import tempfile
import os

# Import from project modules using absolute imports relative to project root
# Note: We assume the test runner adds the project root to sys.path
from code.ingestion import (
    generate_delay_discounting_data,
    generate_procrastination_data,
    generate_nback_data,
    harmonize_datasets,
    calculate_cronbach_alpha
)
from code.modeling import (
    transform_and_center,
    run_regression,
    calculate_vif,
    fit_hyperbolic_model
)
from code.robustness import (
    bootstrap_interaction,
    sensitivity_analysis,
    calculate_instability_ratio
)
from code.config import get_random_state

@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_raw = os.path.join(tmpdir, "data", "raw")
        data_processed = os.path.join(tmpdir, "data", "processed")
        os.makedirs(data_raw)
        os.makedirs(data_processed)
        yield {
            'tmpdir': tmpdir,
            'data_raw': data_raw,
            'data_processed': data_processed
        }

def test_full_pipeline(temp_project_dir):
    """Test the complete pipeline from data generation to analysis."""
    data_raw = temp_project_dir['data_raw']
    data_processed = temp_project_dir['data_processed']
    
    # Step 1: Generate raw data
    dd_path = os.path.join(data_raw, "delay_discounting.csv")
    proc_path = os.path.join(data_raw, "procrastination.csv")
    nback_path = os.path.join(data_raw, "nback.csv")
    
    # Use a fixed seed for reproducibility in tests
    seed = get_random_state().integers(0, 2**31 - 1)
    
    generate_delay_discounting_data(100, dd_path, seed=seed)
    generate_procrastination_data(100, proc_path, seed=seed)
    generate_nback_data(100, nback_path, seed=seed)
    
    # Step 2: Verify reliability of generated data (T014b requirement)
    dd_alpha = calculate_cronbach_alpha(dd_path, 'indifference_point')
    proc_alpha = calculate_cronbach_alpha(proc_path, 'procrastination_score')
    nback_alpha = calculate_cronbach_alpha(nback_path, 'accuracy')
    
    assert dd_alpha >= 0.7, f"Delay discounting reliability too low: {dd_alpha}"
    assert proc_alpha >= 0.7, f"Procrastination reliability too low: {proc_alpha}"
    assert nback_alpha >= 0.7, f"N-back reliability too low: {nback_alpha}"
    
    # Step 3: Harmonize data
    harmonized_df = harmonize_datasets(dd_path, proc_path, nback_path)
    
    # Verify harmonized data
    assert 'procrastination_score' in harmonized_df.columns
    assert 'wm_accuracy' in harmonized_df.columns
    assert 'discount_rate_k' in harmonized_df.columns
    assert len(harmonized_df) == 100
    
    # Step 4: Fit hyperbolic model to calculate discount rates (T015c requirement)
    # This is implicitly done in harmonization but we verify the column exists
    assert 'discount_rate_k' in harmonized_df.columns
    assert not harmonized_df['discount_rate_k'].isna().any()
    
    # Step 5: Prepare data for modeling
    harmonized_df['log_k'] = np.log(harmonized_df['discount_rate_k'] + 1e-6)
    prepared_df = transform_and_center(
        harmonized_df, 
        ['log_k', 'wm_accuracy', 'age']
    )
    
    # Create interaction term
    prepared_df['interaction'] = (
        prepared_df['log_k_centered'] * 
        prepared_df['wm_accuracy_centered']
    )
    
    # Step 6: Run regression
    regression_results = run_regression(
        prepared_df,
        'procrastination_score',
        ['log_k_centered', 'wm_accuracy_centered', 'age_centered', 'interaction']
    )
    
    # Verify regression results structure
    assert 'coefficients' in regression_results
    assert 'interaction' in regression_results['coefficients']
    assert 'p_values' in regression_results
    assert 'interaction' in regression_results['p_values']
    
    # Step 7: Run robustness checks
    robustness_results = sensitivity_analysis(
        prepared_df,
        n_bootstrap=50,  # Reduced for faster test execution
        seed=seed
    )
    
    # Verify robustness results structure
    assert 'instability_ratio' in robustness_results
    assert 0 <= robustness_results['instability_ratio'] <= 1
    assert 'bootstrap_ci' in robustness_results
    assert 'sensitivity_results' in robustness_results

def test_vif_check_in_pipeline(temp_project_dir):
    """Test that VIF calculation is integrated in the pipeline."""
    data_raw = temp_project_dir['data_raw']
    
    # Generate data
    seed = get_random_state().integers(0, 2**31 - 1)
    dd_path = os.path.join(data_raw, "delay_discounting.csv")
    proc_path = os.path.join(data_raw, "procrastination.csv")
    nback_path = os.path.join(data_raw, "nback.csv")
    
    generate_delay_discounting_data(100, dd_path, seed=seed)
    generate_procrastination_data(100, proc_path, seed=seed)
    generate_nback_data(100, nback_path, seed=seed)
    
    # Harmonize
    harmonized_df = harmonize_datasets(dd_path, proc_path, nback_path)
    
    # Prepare features
    features = ['wm_accuracy', 'wm_rt', 'age', 'education']
    X = harmonized_df[features].dropna()
    
    if len(X) > 0:
        # Calculate VIF
        vif_scores = calculate_vif(X)
        
        # All VIF scores should be reasonable (< 10) for synthetic data
        for feature, vif in vif_scores.items():
            assert vif < 10, f"VIF too high for {feature}: {vif}"

def test_data_harmonization_edge_cases(temp_project_dir):
    """Test harmonization with missing participant IDs."""
    data_raw = temp_project_dir['data_raw']
    
    # Generate data with different seeds to simulate potential mismatches
    seed1 = get_random_state().integers(0, 2**31 - 1)
    seed2 = get_random_state().integers(0, 2**31 - 1)
    seed3 = get_random_state().integers(0, 2**31 - 1)
    
    dd_path = os.path.join(data_raw, "delay_discounting.csv")
    proc_path = os.path.join(data_raw, "procrastination.csv")
    nback_path = os.path.join(data_raw, "nback.csv")
    
    generate_delay_discounting_data(100, dd_path, seed=seed1)
    generate_procrastination_data(100, proc_path, seed=seed2)
    generate_nback_data(100, nback_path, seed=seed3)
    
    # Harmonize - should handle mismatches gracefully
    harmonized_df = harmonize_datasets(dd_path, proc_path, nback_path)
    
    # Verify we still have data (inner join on participant_id)
    assert len(harmonized_df) > 0
    assert 'participant_id' in harmonized_df.columns
    # Check that all required columns are present
    required_cols = ['discount_rate_k', 'procrastination_score', 'wm_accuracy', 'wm_rt']
    for col in required_cols:
        assert col in harmonized_df.columns, f"Missing required column: {col}"

def test_model_fitting_integration(temp_project_dir):
    """Test that model fitting works correctly within the pipeline."""
    data_raw = temp_project_dir['data_raw']
    
    seed = get_random_state().integers(0, 2**31 - 1)
    dd_path = os.path.join(data_raw, "delay_discounting.csv")
    proc_path = os.path.join(data_raw, "procrastination.csv")
    nback_path = os.path.join(data_raw, "nback.csv")
    
    generate_delay_discounting_data(100, dd_path, seed=seed)
    generate_procrastination_data(100, proc_path, seed=seed)
    generate_nback_data(100, nback_path, seed=seed)
    
    harmonized_df = harmonize_datasets(dd_path, proc_path, nback_path)
    
    # Verify discount rates are reasonable (positive, not too large)
    assert (harmonized_df['discount_rate_k'] > 0).all()
    assert (harmonized_df['discount_rate_k'] < 100).all()  # Reasonable upper bound
    
    # Verify procrastination scores are in expected range
    assert (harmonized_df['procrastination_score'] >= 0).all()
    assert (harmonized_df['procrastination_score'] <= 1).all()
    
    # Verify WM accuracy is in expected range
    assert (harmonized_df['wm_accuracy'] >= 0).all()
    assert (harmonized_df['wm_accuracy'] <= 1).all()