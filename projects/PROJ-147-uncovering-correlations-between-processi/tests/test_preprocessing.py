"""
Unit tests for code/data/processor.py.

Validates mathematical correctness of derived features (Strain Rate, Zener-Hollomon)
against spec definitions.

Mathematical Formulas (Spec Definitions):
---------------------------------------------------------
1. Strain Rate (epsilon_dot):
   epsilon_dot = d(epsilon) / dt
   Units: 1/s (s^-1)
   (Note: In this pipeline, strain rate is an input feature provided in 1/s.
    The validation here ensures it is passed through correctly and used in Z).

2. Zener-Hollomon Parameter (Z):
   Z = epsilon_dot * exp(Q / (R * T))

   Where:
   - epsilon_dot: Strain rate (1/s)
   - Q: Activation Energy (J/mol)
     * Default for Al alloys: ~140,000 J/mol (140 kJ/mol)
     * Default for Cu alloys: ~200,000 J/mol (200 kJ/mol)
     * Can be overridden via config or alloy-specific lookup.
   - R: Universal Gas Constant = 8.314 J/(mol*K)
   - T: Absolute Temperature (Kelvin)

   Units of Z: 1/s (same as strain rate, as the exponential term is dimensionless)
---------------------------------------------------------
"""

import os
import sys
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.processor import (
    standardize_units,
    impute_median,
    remove_outliers_3sigma,
    derive_physics_features,
    process_dataset
)

# --- Spec Constants for Validation ---
R_GAS_CONSTANT = 8.314  # J/(mol*K)
Q_AL_ALLOY = 140000.0   # J/mol (140 kJ/mol)
Q_CU_ALLOY = 200000.0   # J/mol (200 kJ/mol)


@pytest.fixture
def sample_df():
    """Create a sample dataframe for testing."""
    data = {
        'strain_rate': [0.1, 1.0, 10.0, 100.0, 50.0],
        'temperature_c': [300.0, 400.0, 500.0, 600.0, 350.0], # Celsius
        'stress_mpa': [100.0, 200.0, np.nan, 400.0, 150.0],
        'alloy_family': ['Al', 'Al', 'Cu', 'Cu', 'Al']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_with_outliers():
    """Create a dataframe with known outliers."""
    data = {
        'strain_rate': [0.1, 0.2, 0.3, 1000.0], # 1000 is an outlier
        'temperature': [500.0, 500.0, 500.0, 500.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_with_nans():
    """Create a dataframe with NaNs for imputation."""
    data = {
        'strain_rate': [0.1, np.nan, 0.3, 0.4, 0.5],
        'temperature': [500.0, 500.0, np.nan, 500.0, 500.0]
    }
    return pd.DataFrame(data)

def test_standardize_units_temperature(sample_df):
    """
    Test Celsius to Kelvin conversion.
    Formula: T_K = T_C + 273.15
    """
    df_std = standardize_units(sample_df)
    # Check that temperature_c was converted to Kelvin (approx)
    # Input: 300 -> 573.15
    expected_300 = 300.0 + 273.15
    assert abs(df_std['temperature_c'].iloc[0] - expected_300) < 0.01

def test_impute_median(sample_df_with_nans):
    """Test median imputation logic."""
    df_imp, stats = impute_median(sample_df_with_nans)
    # Check no NaNs remain
    assert df_imp.isnull().sum().sum() == 0
    # Check median calculation
    # strain_rate median of [0.1, 0.3, 0.4, 0.5] -> (0.3+0.4)/2 = 0.35
    expected_median_sr = 0.35
    assert abs(df_imp['strain_rate'].iloc[1] - expected_median_sr) < 0.01

def test_impute_median_threshold_exceeded(sample_df_with_nans):
    """Test that imputation fails if NaN > 20%."""
    # Create a column with > 20% NaN (e.g., 2 out of 5 = 40%)
    df = pd.DataFrame({'col1': [1.0, np.nan, np.nan, 4.0, 5.0]})
    with pytest.raises(ValueError, match="Imputation failed"):
        impute_median(df, max_nan_fraction=0.20)

def test_remove_outliers_3sigma(sample_df_with_outliers):
    """Test 3-sigma outlier removal."""
    df_clean, stats = remove_outliers_3sigma(sample_df_with_outliers)
    # The outlier (1000.0) should be removed
    assert len(df_clean) == 3
    assert 1000.0 not in df_clean['strain_rate'].values

def test_derive_physics_features_zener_hollomon():
    """
    Validate Zener-Hollomon calculation against Spec Formula.
    Formula: Z = epsilon_dot * exp(Q / (R * T))

    Test Case:
    epsilon_dot = 1.0 1/s
    T = 500.0 K
    Q = 140,000 J/mol (Al)
    R = 8.314 J/(mol*K)

    Expected Z = 1.0 * exp(140000 / (8.314 * 500))
    """
    Q_test = Q_AL_ALLOY
    R = R_GAS_CONSTANT
    epsilon_dot = 1.0
    T_kelvin = 500.0

    df_k = pd.DataFrame({
        'strain_rate': [epsilon_dot],
        'temperature': [T_kelvin]
    })

    # Derive features
    df_result = derive_physics_features(df_k, activation_energy=Q_test)

    # Calculate expected Z manually
    expected_Z = epsilon_dot * np.exp(Q_test / (R * T_kelvin))
    calculated_Z = df_result['zener_hollomon'].iloc[0]

    assert abs(calculated_Z - expected_Z) < 1e-5, \
        f"Zener-Hollomon mismatch. Expected {expected_Z}, got {calculated_Z}"

def test_derive_physics_features_strain_rate_passthrough():
    """
    Validate that strain rate is correctly identified and passed through.
    Spec: Strain Rate (epsilon_dot) is an input feature in 1/s.
    """
    input_rates = [0.01, 1.0, 100.0]
    df = pd.DataFrame({
        'strain_rate': input_rates,
        'temperature': [500.0] * 3
    })

    df_result = derive_physics_features(df)

    # Check that strain_rate column exists and matches input
    for i, rate in enumerate(input_rates):
        assert df_result['strain_rate'].iloc[i] == rate

def test_process_dataset_integration(tmp_path):
    """Test the full pipeline integration."""
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"

    data = {
        'strain_rate': [0.1, 0.2, 0.3],
        'temperature_c': [300.0, 400.0, 500.0],
        'stress': [100.0, 200.0, 300.0]
    }
    df = pd.DataFrame(data)
    df.to_csv(input_file, index=False)

    report = process_dataset(str(input_file), str(output_file))

    assert os.path.exists(output_file)
    assert os.path.exists(output_file.parent / "output_report.json")
    assert report['final_row_count'] == 3