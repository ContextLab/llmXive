"""
Integration test for the full analysis pipeline (T022a).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import json

from analysis import run_analysis_pipeline, load_transformed_diversity_data

@pytest.fixture
def temp_analysis_dir(tmp_path):
    """Create a temporary directory structure for analysis."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    return processed_dir

def test_full_analysis_pipeline(temp_analysis_dir):
    """Test the full analysis pipeline from input to output."""
    # Create mock input data
    np.random.seed(42)
    n_samples = 100
    sites = [f"Site_{i}" for i in range(5)]
    
    input_df = pd.DataFrame({
        'sample_id': [f"Sample_{i}" for i in range(n_samples)],
        'site': np.random.choice(sites, n_samples),
        'pH': np.random.uniform(6.0, 9.0, n_samples),
        'shannon_diversity': np.random.uniform(2.0, 5.0, n_samples),
        'simpson_diversity': np.random.uniform(0.5, 0.9, n_samples)
    })
    
    input_file = temp_analysis_dir / "diversity_transformed.csv"
    input_df.to_csv(input_file, index=False)
    
    output_file = temp_analysis_dir / "lme_results.csv"
    
    # Run the pipeline
    run_analysis_pipeline(
        input_file=str(input_file),
        output_file=str(output_file)
    )
    
    # Verify output file exists
    assert output_file.exists(), "Output file was not created"
    
    # Verify output content
    results_df = pd.read_csv(output_file)
    assert len(results_df) == 2, "Expected 2 rows (Shannon and Simpson)"
    assert 'estimate' in results_df.columns
    assert 'se' in results_df.columns
    assert 'p_value' in results_df.columns
    assert 'model_type' in results_df.columns
    assert 'metric' in results_df.columns
    
    # Verify metrics
    assert 'shannon_diversity' in results_df['metric'].values
    assert 'simpson_diversity' in results_df['metric'].values
    
    # Verify non-linearity check file
    nonlinearity_file = temp_analysis_dir.parent / "nonlinearity_check.json"
    assert nonlinearity_file.exists(), "Non-linearity check file was not created"
    
    with open(nonlinearity_file, 'r') as f:
        nl_data = json.load(f)
    assert 'is_nonlinear' in nl_data
    assert 'p_value_quadratic' in nl_data

def test_pipeline_with_single_site(temp_analysis_dir):
    """Test pipeline with only one site (should fallback to OLS)."""
    input_df = pd.DataFrame({
        'sample_id': [f"Sample_{i}" for i in range(20)],
        'site': ['Site_A'] * 20,
        'pH': np.random.uniform(6.0, 9.0, 20),
        'shannon_diversity': np.random.uniform(2.0, 5.0, 20),
        'simpson_diversity': np.random.uniform(0.5, 0.9, 20)
    })
    
    input_file = temp_analysis_dir / "diversity_transformed.csv"
    input_df.to_csv(input_file, index=False)
    
    output_file = temp_analysis_dir / "lme_results.csv"
    
    run_analysis_pipeline(
        input_file=str(input_file),
        output_file=str(output_file)
    )
    
    results_df = pd.read_csv(output_file)
    # All models should be OLS
    assert all(results_df['model_type'] == 'OLS'), "Expected all OLS models"

def test_pipeline_with_nonlinear_data(temp_analysis_dir):
    """Test pipeline with data that has a non-linear relationship."""
    np.random.seed(42)
    n_samples = 100
    pH = np.linspace(6, 9, n_samples)
    diversity = -0.5 * (pH - 7.5)**2 + 4.0 + np.random.normal(0, 0.2, n_samples)
    
    input_df = pd.DataFrame({
        'sample_id': [f"Sample_{i}" for i in range(n_samples)],
        'site': ['Site_A'] * n_samples,
        'pH': pH,
        'shannon_diversity': diversity,
        'simpson_diversity': diversity * 0.2
    })
    
    input_file = temp_analysis_dir / "diversity_transformed.csv"
    input_df.to_csv(input_file, index=False)
    
    output_file = temp_analysis_dir / "lme_results.csv"
    
    run_analysis_pipeline(
        input_file=str(input_file),
        output_file=str(output_file)
    )
    
    # Check non-linearity file
    nonlinearity_file = temp_analysis_dir.parent / "nonlinearity_check.json"
    with open(nonlinearity_file, 'r') as f:
        nl_data = json.load(f)
    
    # The quadratic term should be significant
    assert nl_data['is_nonlinear'] is True
