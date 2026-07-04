import pytest
import pandas as pd
import numpy as np
import sys
import os
import logging

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis import run_tobit_regression

def test_tobit_regression_basic():
    """
    Test Tobit regression with a small synthetic dataset that mimics censored data.
    Since we cannot rely on real data files existing in the test environment,
    we generate synthetic data in-memory to verify the function logic.
    """
    # Create synthetic data
    np.random.seed(42)
    n = 50
    temp = np.random.uniform(1000, 2500, n)
    mass = np.random.uniform(0.5, 10, n)
    metal = np.random.uniform(-1, 1, n)
    
    # True relationship: water abundance increases with temp
    true_coef_temp = 0.001
    true_coef_mass = -0.05
    true_coef_metal = 0.2
    
    # Simulate log abundance with noise
    noise = np.random.normal(0, 0.5, n)
    log_abundance = (
        2.0 + 
        true_coef_temp * temp + 
        true_coef_mass * mass + 
        true_coef_metal * metal + 
        noise
    )
    
    # Simulate censoring: values below -4 are censored (upper limits)
    censor_threshold = -4.0
    is_censored = log_abundance < censor_threshold
    # For censored values, we observe the threshold or a value slightly below (simulating detection limit)
    observed_abundance = np.where(is_censored, censor_threshold - 0.1, log_abundance)
    
    df = pd.DataFrame({
        "equilibrium_temp": temp,
        "planet_mass": mass,
        "host_metallicity": metal,
        "water_log_abundance": observed_abundance,
        "is_censored": is_censored
    })
    
    result = run_tobit_regression(
        df,
        outcome_col="water_log_abundance",
        censor_col="is_censored",
        predictors=["equilibrium_temp", "planet_mass", "host_metallicity"]
    )
    
    assert result is not None, "Tobit regression should return a result"
    assert "coefficients" in result
    assert "log_likelihood" in result
    
    # Check that coefficients are roughly in the expected direction (signs)
    # Note: Weibull AFT coefficients might differ in magnitude from OLS/Tobit exact,
    # but signs should be consistent for this synthetic test.
    assert result["coefficients"]["equilibrium_temp"] > 0, "Temp coefficient should be positive"
    assert result["coefficients"]["planet_mass"] < 0, "Mass coefficient should be negative"
    assert result["coefficients"]["host_metallicity"] > 0, "Metallicity coefficient should be positive"

def test_tobit_regression_no_censorship():
    """Test with no censored data to ensure basic regression works."""
    np.random.seed(123)
    n = 30
    temp = np.random.uniform(1000, 2000, n)
    mass = np.random.uniform(1, 5, n)
    metal = np.random.uniform(-0.5, 0.5, n)
    log_abundance = 1.0 + 0.0005 * temp - 0.02 * mass + 0.1 * metal + np.random.normal(0, 0.2, n)
    
    df = pd.DataFrame({
        "equilibrium_temp": temp,
        "planet_mass": mass,
        "host_metallicity": metal,
        "water_log_abundance": log_abundance,
        "is_censored": False  # No censorship
    })
    
    result = run_tobit_regression(
        df,
        outcome_col="water_log_abundance",
        censor_col="is_censored",
        predictors=["equilibrium_temp", "planet_mass", "host_metallicity"]
    )
    
    assert result is not None
    assert result["log_likelihood"] < 0 # Log likelihood should be negative (log of probability < 1)
    
def test_tobit_regression_insufficient_data():
    """Test with too few data points."""
    df = pd.DataFrame({
        "equilibrium_temp": [1500.0, 1600.0],
        "planet_mass": [1.0, 2.0],
        "host_metallicity": [0.0, 0.1],
        "water_log_abundance": [2.0, 2.1],
        "is_censored": [False, False]
    })
    
    result = run_tobit_regression(
        df,
        outcome_col="water_log_abundance",
        censor_col="is_censored",
        predictors=["equilibrium_temp", "planet_mass", "host_metallicity"]
    )
    
    # Should return None or handle gracefully
    assert result is None or "coefficients" in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])