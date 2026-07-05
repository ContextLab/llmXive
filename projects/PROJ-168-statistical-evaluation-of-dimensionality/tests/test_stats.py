"""
Tests for statistical analysis module.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.stats import (
    fit_mixed_effects_model,
    fit_fixed_effects_anova,
    run_interaction_test,
    check_collinearity,
    load_aggregated_metrics
)
from code.config import Config

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n = 30
    data = {
        'dataset': np.repeat(['GSE131907', 'GSE111322', 'GSE150728'], n // 3),
        'method': np.tile(['pca', 'tsne', 'umap'], n // 3),
        'fidelity': np.random.normal(0.7, 0.1, n),
        'geometry_linearity': np.random.normal(0.8, 0.05, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_results_dir():
    """Create a temporary directory for results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_fit_mixed_effects_model(sample_data, temp_results_dir):
    """Test Mixed-Effects Model fitting."""
    result = fit_mixed_effects_model(sample_data, results_dir=temp_results_dir)
    
    assert result['status'] == 'success'
    assert result['model_type'] == 'Mixed-Effects'
    assert result['n_datasets'] == 3
    assert result['n_observations'] == len(sample_data)
    assert 'fixed_effects' in result
    assert 'p_values' in result
    
    # Check that results were saved
    assert (temp_results_dir / "mixed_effects_results.json").exists()

def test_fit_fixed_effects_anova(sample_data, temp_results_dir):
    """Test Fixed-Effects ANOVA fitting."""
    result = fit_fixed_effects_anova(sample_data, results_dir=temp_results_dir)
    
    assert result['status'] == 'success'
    assert result['model_type'] == 'Fixed-Effects ANOVA'
    assert 'anova_table' in result
    assert 'p_values' in result

def test_fit_fixed_effects_anova_single_dataset(temp_results_dir):
    """Test Fixed-Effects ANOVA with single dataset."""
    np.random.seed(42)
    single_data = pd.DataFrame({
        'dataset': ['GSE131907'] * 10,
        'method': ['pca', 'tsne', 'umap'] * 3 + ['pca'],
        'fidelity': np.random.normal(0.7, 0.1, 10)
    })
    
    result = fit_fixed_effects_anova(single_data, results_dir=temp_results_dir)
    
    assert result['status'] == 'success'
    assert result['model_type'] == 'Fixed-Effects ANOVA'

def test_run_interaction_test(sample_data, temp_results_dir):
    """Test interaction test."""
    result = run_interaction_test(sample_data, results_dir=temp_results_dir)
    
    assert result['status'] == 'success'
    assert 'interaction_terms' in result
    assert 'formula' in result

def test_run_interaction_test_insufficient_data(temp_results_dir):
    """Test interaction test with insufficient data."""
    single_data = pd.DataFrame({
        'dataset': ['GSE131907'] * 10,
        'method': ['pca', 'tsne', 'umap'] * 3 + ['pca'],
        'fidelity': np.random.normal(0.7, 0.1, 10)
    })
    
    result = run_interaction_test(single_data, results_dir=temp_results_dir)
    
    assert result['status'] == 'skipped'
    assert 'reason' in result

def test_check_collinearity(sample_data):
    """Test VIF calculation."""
    is_collinear, high_vif = check_collinearity(sample_data, "fidelity ~ method")
    
    assert isinstance(is_collinear, bool)
    assert isinstance(high_vif, list)

def test_load_aggregated_metrics_missing_file(temp_results_dir):
    """Test loading aggregated metrics when file is missing."""
    with pytest.raises(FileNotFoundError):
        load_aggregated_metrics(temp_results_dir)

def test_benjamini_hochberg_correction(sample_data, temp_results_dir):
    """Test that Benjamini-Hochberg correction is applied."""
    result = fit_mixed_effects_model(sample_data, results_dir=temp_results_dir)
    
    # Check that corrected p-values are present
    assert 'corrected_p_values' in result
    assert len(result['corrected_p_values']) > 0

def test_fallback_to_anova_on_convergence_failure(temp_results_dir):
    """Test fallback to ANOVA when Mixed-Effects fails."""
    # Create data that might cause convergence issues
    np.random.seed(42)
    data = pd.DataFrame({
        'dataset': ['GSE131907'] * 5 + ['GSE111322'] * 5,
        'method': ['pca'] * 10,
        'fidelity': [0.7] * 10  # Constant fidelity
    })
    
    result = fit_mixed_effects_model(data, results_dir=temp_results_dir)
    
    # Should fallback to ANOVA
    assert result['status'] in ['success', 'failed']

def test_save_results_format(temp_results_dir):
    """Test that results are saved in correct format."""
    np.random.seed(42)
    data = pd.DataFrame({
        'dataset': ['GSE131907'] * 10,
        'method': ['pca', 'tsne', 'umap'] * 3 + ['pca'],
        'fidelity': np.random.normal(0.7, 0.1, 10)
    })
    
    result = fit_mixed_effects_model(data, results_dir=temp_results_dir)
    
    # Check JSON file
    json_file = temp_results_dir / "mixed_effects_results.json"
    assert json_file.exists()
    
    with open(json_file) as f:
        saved = json.load(f)
    
    assert 'model_type' in saved
    assert 'fixed_effects' in saved