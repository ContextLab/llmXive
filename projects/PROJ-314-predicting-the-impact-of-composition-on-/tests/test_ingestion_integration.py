"""
Integration tests for ingestion pipeline components.
These tests verify that the validation logic works correctly 
in the context of a simulated pipeline flow.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from code.ingestion import (
    validate_no_missing_predictors, 
    clean_data, 
    compute_descriptors,
    validate_data_gap
)

def test_pipeline_validation_flow():
    """
    Simulates the flow: Clean -> Compute Descriptors -> Validate.
    Ensures that if descriptors are computed with NaN, validation catches it.
    """
    # 1. Create a "clean" dataset (simulating output of clean_data)
    # Note: clean_data in the current implementation fillsna with median,
    # but we simulate a case where compute_descriptors might introduce NaN
    # or where the input to descriptors was incomplete.
    df_clean = pd.DataFrame({
        'composition': ['Mg2SiO4', 'Al2O3', 'SiO2'],
        'weibull_modulus': [10.0, 15.0, 20.0],
        'is_range_flag': [False, False, False],
        'range_original': [None, None, None],
        'sample_count': [10, 10, 10],
        'sintering_temp': [1500, 1600, 1700]
    })

    # 2. Simulate compute_descriptors that produces NaN (e.g., if calculation fails)
    # In a real scenario, this might happen if a composition is unparseable.
    df_descriptors = df_clean.copy()
    df_descriptors['mean_atomic_radius'] = [1.5, np.nan, 1.7]
    df_descriptors['electronegativity_std'] = [0.5, 0.6, 0.7]
    df_descriptors['valence_electron_concentration'] = [2.0, 2.1, 2.2]

    # 3. Verify that validation fails
    with pytest.raises(ValueError) as excinfo:
        validate_no_missing_predictors(df_descriptors)
    
    assert "mean_atomic_radius" in str(excinfo.value)

def test_pipeline_validation_pass():
    """
    Simulates a successful pipeline flow where all descriptors are valid.
    """
    df_clean = pd.DataFrame({
        'composition': ['Mg2SiO4', 'Al2O3', 'SiO2'],
        'weibull_modulus': [10.0, 15.0, 20.0],
        'is_range_flag': [False, False, False],
        'range_original': [None, None, None],
        'sample_count': [10, 10, 10],
        'sintering_temp': [1500, 1600, 1700]
    })

    # Simulate successful descriptor computation
    df_descriptors = df_clean.copy()
    df_descriptors['mean_atomic_radius'] = [1.5, 1.4, 1.7]
    df_descriptors['electronegativity_std'] = [0.5, 0.6, 0.7]
    df_descriptors['valence_electron_concentration'] = [2.0, 2.1, 2.2]

    # Should pass without exception
    try:
        validate_no_missing_predictors(df_descriptors)
    except ValueError:
        pytest.fail("Validation should not raise ValueError for valid data")