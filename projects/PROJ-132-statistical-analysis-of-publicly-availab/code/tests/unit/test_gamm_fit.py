"""
Unit tests for GAMM fitting module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from src.models.gamm_fit import (
    _prepare_gamm_formula,
    _fit_single_gamm,
    fit_species_year_gamm,
    apply_fdr_correction
)

@pytest.fixture
def sample_gamm_data():
    """Create sample data for GAMM testing."""
    np.random.seed(42)
    n = 500
    
    data = pd.DataFrame({
        'species': np.random.choice(['Species_A', 'Species_B', 'Species_C'], n),
        'year': np.random.choice([2018, 2019, 2020], n),
        'phenology_metric': np.random.normal(100, 10, n),
        'temp': np.random.normal(15, 5, n),
        'precip': np.random.normal(50, 20, n),
        'effort': np.random.normal(10, 3, n)
    })
    
    return data

def test_prepare_gamm_formula(sample_gamm_data):
    """Test formula preparation."""
    formula, prepared_data = _prepare_gamm_formula(sample_gamm_data)
    
    assert 'phenology_metric' in formula
    assert 'temp' in formula
    assert 'precip' in formula
    assert 'effort' in formula
    assert 'species_year' in formula
    assert 'species_year' in prepared_data.columns
    
def test_fit_single_gamm(sample_gamm_data):
    """Test single GAMM fitting."""
    # Filter to a single group
    group_data = sample_gamm_data[sample_gamm_data['species'] == 'Species_A'].copy()
    
    formula, _ = _prepare_gamm_formula(sample_gamm_data)
    result = _fit_single_gamm(formula, group_data, 'Species_A', 2018)
    
    assert 'species' in result
    assert 'coefficients' in result
    assert 'p_values' in result
    assert 'converged' in result

def test_fit_species_year_gamm(sample_gamm_data):
    """Test full GAMM fitting with species-year random effects."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_results.json")
        results = fit_species_year_gamm(sample_gamm_data, output_path=output_path)
        
        assert 'total_models' in results
        assert 'converged_models' in results
        assert 'results' in results
        assert len(results['results']) > 0

def test_apply_fdr_correction(sample_gamm_data):
    """Test FDR correction application."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_results.json")
        results = fit_species_year_gamm(sample_gamm_data, output_path=output_path)
        
        corrected_results = apply_fdr_correction(results)
        
        assert 'fdr_adjusted' in corrected_results
        assert len(corrected_results['fdr_adjusted']) > 0