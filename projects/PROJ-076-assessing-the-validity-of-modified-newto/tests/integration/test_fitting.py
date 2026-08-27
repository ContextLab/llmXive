"""
Integration test for the fitting pipeline on a sample galaxy.

This test verifies the end-to-end workflow of:
1. Loading a real filtered galaxy from data/processed/filtered_galaxies.csv
2. Fitting the MOND 'simple' model (T021) and NFW model (T022)
3. Calculating reduced chi-squared, AIC, and BIC (T024)
4. Asserting that metrics are computed and within reasonable bounds.

Prerequisites:
- T015 must have generated data/processed/filtered_galaxies.csv
- T021 (code/models/mond.py) and T022 (code/models/nfw.py) must be implemented.
- T023 (code/fit.py) and T024 (code/metrics.py) must be implemented.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.models import mond
from code.models import nfw
from code import fit
from code import metrics
from code import preprocess
from code import utils

# Constants
DATA_PATH = "data/processed/filtered_galaxies.csv"
MIN_GALAXIES_REQUIRED = 1
MAX_FIT_TIME_PER_GALAXY_S = 30.0  # Performance constraint from spec

@pytest.fixture(scope="module")
def sample_galaxy_df():
    """
    Loads the first available galaxy from the filtered dataset.
    Raises FileNotFoundError or ValueError if data is missing or empty.
    """
    data_file = project_root / DATA_PATH
    if not data_file.exists():
        raise FileNotFoundError(
            f"Required data file not found: {data_file}. "
            "Please ensure T015 (data generation) has been completed."
        )
    
    df = pd.read_csv(data_file)
    
    if df.empty:
        raise ValueError(
            f"Data file {data_file} is empty. "
            "Preprocessing pipeline (T014) may have filtered out all galaxies."
        )
    
    # Take the first galaxy ID present in the dataset
    galaxy_id = df['galaxy_id'].iloc[0]
    galaxy_data = df[df['galaxy_id'] == galaxy_id].reset_index(drop=True)
    
    if len(galaxy_data) < 15:
        # Safety check against the quality filter constraint
        raise ValueError(
            f"Galaxy {galaxy_id} has fewer than 15 points after filtering. "
            "This suggests a data integrity issue."
        )
        
    return galaxy_data

def test_mond_simple_fit(sample_galaxy_df):
    """
    Integration test for MOND 'simple' model fitting.
    Verifies that the model converges and produces valid metrics.
    """
    galaxy_id = sample_galaxy_df['galaxy_id'].iloc[0]
    r = sample_galaxy_df['radius'].values
    v_obs = sample_galaxy_df['velocity'].values
    v_err = sample_galaxy_df['velocity_err'].values

    # Ensure arrays are not empty
    assert len(r) > 0, "Radius array is empty."
    assert len(v_obs) == len(v_err), "Velocity and error arrays length mismatch."

    # Initial guess for M/L (mass-to-light ratio)
    # Typical values for disk galaxies are often between 0.5 and 2.0
    initial_m_l = 1.0
    
    # Fit the model
    # We wrap in try/except to catch convergence issues without failing the test
    # unless the error is fundamental (e.g., missing function)
    try:
        result = fit.fit_galaxy_mond_simple(
            r, v_obs, v_err, 
            initial_m_l=initial_m_l
        )
    except Exception as e:
        pytest.fail(f"Mond simple fitting failed for galaxy {galaxy_id}: {e}")

    # Assertions
    assert result is not None, "Fitting returned None."
    assert 'params' in result, "Result missing 'params' key."
    assert 'metrics' in result, "Result missing 'metrics' key."
    
    fitted_m_l = result['params'].get('M_L')
    assert fitted_m_l is not None, "M/L parameter not found in result."
    assert fitted_m_l > 0, f"M/L parameter must be positive, got {fitted_m_l}."
    
    # Check metrics exist
    chi2_red = result['metrics'].get('reduced_chi2')
    aic = result['metrics'].get('aic')
    bic = result['metrics'].get('bic')
    
    assert chi2_red is not None, "Reduced chi2 missing."
    assert aic is not None, "AIC missing."
    assert bic is not None, "BIC missing."
    
    # Reasonable bounds check (chi2_red should ideally be near 1.0, but < 10.0 for a fit to exist)
    assert chi2_red > 0, "Reduced chi2 must be positive."
    assert chi2_red < 100.0, f"Reduced chi2 ({chi2_red}) is unreasonably high."

def test_nfw_fit(sample_galaxy_df):
    """
    Integration test for NFW model fitting.
    Verifies convergence and metric calculation.
    """
    galaxy_id = sample_galaxy_df['galaxy_id'].iloc[0]
    r = sample_galaxy_df['radius'].values
    v_obs = sample_galaxy_df['velocity'].values
    v_err = sample_galaxy_df['velocity_err'].values

    # Initial guess for concentration parameter
    # Typical values are between 5 and 20
    initial_c = 10.0
    # Initial guess for virial mass (in solar masses, log scale often used, but we use linear here for simplicity if model supports)
    # Assuming the NFW model expects M_vir in solar masses
    initial_m_vir = 1e11 

    try:
        result = fit.fit_galaxy_nfw(
            r, v_obs, v_err,
            initial_c=initial_c,
            initial_m_vir=initial_m_vir
        )
    except Exception as e:
        # NFW fitting can be tricky; if it fails, we check if it's a missing dependency issue
        # or a real data issue. For integration test, we expect it to run.
        pytest.fail(f"NFW fitting failed for galaxy {galaxy_id}: {e}")

    assert result is not None, "Fitting returned None."
    assert 'params' in result, "Result missing 'params' key."
    assert 'metrics' in result, "Result missing 'metrics' key."

    fitted_c = result['params'].get('c')
    assert fitted_c is not None, "Concentration parameter 'c' not found."
    assert fitted_c > 0, f"Concentration must be positive, got {fitted_c}."

    chi2_red = result['metrics'].get('reduced_chi2')
    assert chi2_red is not None, "Reduced chi2 missing."
    assert chi2_red > 0, "Reduced chi2 must be positive."

def test_metrics_calculation_consistency(sample_galaxy_df):
    """
    Verifies that the metrics calculated by the pipeline match the definitions.
    We manually calculate chi2 and compare with the result from fit.py.
    """
    galaxy_id = sample_galaxy_df['galaxy_id'].iloc[0]
    r = sample_galaxy_df['radius'].values
    v_obs = sample_galaxy_df['velocity'].values
    v_err = sample_galaxy_df['velocity_err'].values

    # Fit MOND
    result = fit.fit_galaxy_mond_simple(r, v_obs, v_err, initial_m_l=1.0)
    fitted_v = mond.predict_velocity(r, result['params']['M_L'])
    
    # Manual calculation
    manual_chi2 = np.sum(((v_obs - fitted_v) / v_err) ** 2)
    dof = len(v_obs) - 1 # 1 free parameter (M/L)
    manual_chi2_red = manual_chi2 / dof

    pipeline_chi2_red = result['metrics']['reduced_chi2']

    # Allow small floating point differences
    assert np.isclose(manual_chi2_red, pipeline_chi2_red, rtol=1e-5), \
        f"Manual chi2 ({manual_chi2_red}) != Pipeline chi2 ({pipeline_chi2_red})"

def test_performance_constraint(sample_galaxy_df):
    """
    Ensures fitting completes within the 30s/galaxy constraint (T023).
    """
    import time
    
    r = sample_galaxy_df['radius'].values
    v_obs = sample_galaxy_df['velocity'].values
    v_err = sample_galaxy_df['velocity_err'].values

    start_time = time.time()
    fit.fit_galaxy_mond_simple(r, v_obs, v_err, initial_m_l=1.0)
    end_time = time.time()

    elapsed = end_time - start_time
    assert elapsed < MAX_FIT_TIME_PER_GALAXY_S, \
        f"Fitting took {elapsed:.2f}s, exceeding limit of {MAX_FIT_TIME_PER_GALAXY_S}s"