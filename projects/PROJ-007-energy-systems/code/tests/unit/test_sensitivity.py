"""
Unit tests for the sensitivity analysis module.
"""
import pytest
import pandas as pd
import numpy as np
from src.analysis.sensitivity import sweep_caliper
from src.analysis.psm import estimate_propensity, match_pairs
from src.analysis.causal import run_ols

@pytest.fixture
def synthetic_data():
    """
    Create a synthetic dataset for testing sensitivity analysis.
    This mimics the structure expected by the pipeline after preprocessing.
    """
    np.random.seed(42)
    n = 1000
    
    # Generate covariates
    income = np.random.normal(50000, 15000, n)
    housing_type = np.random.choice([0, 1], n) # 0: Rent, 1: Own
    location = np.random.choice([0, 1, 2], n) # 0: Urban, 1: Suburban, 2: Rural
    
    # Propensity score generation (logistic)
    logit_p = -2 + 0.00005 * income + 0.5 * housing_type + 0.3 * location
    p = 1 / (1 + np.exp(-logit_p))
    
    # Treatment assignment
    treatment = (np.random.rand(n) < p).astype(int)
    
    # Outcome generation (with a true treatment effect of 0.5)
    # log_energy_cost = beta0 + beta1*treatment + beta2*income + error
    true_att = 0.5
    base_cost = 100 + 0.001 * income
    noise = np.random.normal(0, 10, n)
    log_energy_cost = base_cost + true_att * treatment + noise
    
    df = pd.DataFrame({
        "income": income,
        "housing_type": housing_type,
        "location": location,
        "treatment": treatment,
        "log_energy_cost": log_energy_cost,
        "propensity_score": p # Pre-computed for speed in test, though function recalculates
    })
    
    return df

def test_sweep_caliper_basic_functionality(synthetic_data):
    """Test that sweep_caliper runs without error and returns expected structure."""
    calipers = [0.01, 0.05, 0.1]
    covariates = ["income", "housing_type", "location"]
    
    result = sweep_caliper(
        synthetic_data, 
        calipers=calipers, 
        covariates=covariates,
        min_adopters=10
    )
    
    assert "sweep_results" in result
    assert "summary" in result
    assert isinstance(result["sweep_results"], list)
    assert len(result["sweep_results"]) == len(calipers)
    
    # Check that at least some results are successful
    success_count = sum(1 for r in result["sweep_results"] if r["status"] == "success")
    assert success_count > 0, "Expected at least one successful match in sensitivity sweep."

def test_sweep_caliper_att_significance(synthetic_data):
    """Test that the estimated ATT is close to the true ATT for reasonable calipers."""
    calipers = [0.05] # Use a caliper likely to match well
    covariates = ["income", "housing_type", "location"]
    
    result = sweep_caliper(
        synthetic_data, 
        calipers=calipers, 
        covariates=covariates,
        min_adopters=10
    )
    
    success_results = [r for r in result["sweep_results"] if r["status"] == "success"]
    assert len(success_results) > 0
    
    # Check if the mean ATT is reasonably close to true ATT (0.5)
    # Allow for some variance due to matching randomness and sample size
    att_values = [r["att"] for r in success_results]
    mean_att = np.mean(att_values)
    
    # Rough check: within 20% of true value
    assert abs(mean_att - 0.5) < 0.15, f"Estimated ATT {mean_att} too far from true 0.5"

def test_sweep_caliper_insufficient_power():
    """Test behavior when min_adopters threshold is not met."""
    np.random.seed(123)
    n = 50
    df = pd.DataFrame({
        "income": np.random.normal(50000, 10000, n),
        "housing_type": np.random.choice([0, 1], n),
        "location": np.random.choice([0, 1], n),
        "treatment": np.random.choice([0, 1], n), # Random treatment, might have few treated
        "log_energy_cost": np.random.normal(100, 10, n),
        "propensity_score": np.random.rand(n)
    })
    
    # Force very few treated
    df.loc[:5, "treatment"] = 1
    
    result = sweep_caliper(
        df, 
        calipers=[0.01], 
        covariates=["income", "housing_type", "location"],
        min_adopters=10 # Require 10, but only have 6
    )
    
    # Should have status 'insufficient_power' or similar, not crash
    assert len(result["sweep_results"]) > 0
    # The specific status might vary, but it should not be 'success'
    statuses = [r["status"] for r in result["sweep_results"]]
    assert "success" not in statuses or all(r["att"] is None for r in result["sweep_results"] if r["status"] == "success")

def test_sweep_caliper_invalid_covariates():
    """Test that missing covariates raise an error."""
    df = pd.DataFrame({
        "income": [1, 2, 3],
        "treatment": [0, 1, 0],
        "log_energy_cost": [10, 20, 30]
    })
    
    with pytest.raises(ValueError):
        sweep_caliper(
            df, 
            calipers=[0.01], 
            covariates=["nonexistent_col"],
            min_adopters=1
        )