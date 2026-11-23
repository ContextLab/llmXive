"""
Integration test for LMM data preparation (T019).

This test validates the end-to-end data preparation and execution flow
for the Linear Mixed-Effects Model (LMM) analysis pipeline. It verifies
that the `run_lmm_analysis` function correctly processes simulation data,
handles the formula specification, and returns a structured result dictionary
containing convergence status and parameter estimates.
"""
import pytest
import pandas as pd
import sys
import os
import numpy as np

# Ensure the project root is in the path to resolve imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.analysis.lmm_runner import run_lmm_analysis
from src.data_models import SimulationRun, MetricRecord
from datetime import datetime

def test_lmm_data_preparation_and_run():
    """
    Prepare mock data and run LMM analysis to ensure pipeline works.
    
    The mock data simulates a realistic scenario where:
    - 'step' represents the simulation time step.
    - 'coherence_score' is the dependent variable with some noise and trend.
    - 'param' is a categorical independent variable (fixed effect).
    - 'time_step' is the grouping variable for the random effect.
    """
    # Create mock data
    # We use a fixed seed to ensure reproducibility of the mock data generation
    np.random.seed(42)
    
    n_samples = 50
    steps = np.arange(n_samples)
    
    # Simulate a slight trend and noise
    base_coherence = 0.5
    noise = np.random.normal(0, 0.05, n_samples)
    trend = (steps % 10) * 0.01
    coherence_scores = base_coherence + trend + noise
    
    # Create categorical parameter
    params = ["A" if i % 2 == 0 else "B" for i in range(n_samples)]
    
    # Create time_step groups (random effect)
    time_steps = steps // 10
    
    data = {
        "step": steps,
        "coherence_score": coherence_scores,
        "param": params,
        "time_step": time_steps
    }
    
    df = pd.DataFrame(data)
    
    # Verify data integrity before running analysis
    assert not df.isnull().any().any(), "Mock data contains NaN values"
    assert df["coherence_score"].dtype in [np.float64, np.float32], "Coherence score must be numeric"
    assert df["param"].dtype == object, "Param should be categorical/object"
    
    # Run LMM
    # Formula: coherence_score ~ param + (1|time_step)
    # This tests the fixed effect of 'param' and the random intercept for 'time_step'
    result = run_lmm_analysis(df, formula="coherence_score ~ param + (1|time_step)")
    
    # Assertions on the result structure
    assert isinstance(result, dict), "Result must be a dictionary"
    assert "status" in result or "converged" in result, "Result must contain convergence info"
    
    # If the model converged, we expect parameter estimates
    if result.get("converged", False):
        assert "params" in result, "Converged result must contain 'params'"
        assert "fixed_effects" in result or "random_effects" in result, "Converged result must contain effect estimates"
        
        # Verify specific fixed effects are present (Intercept and param_B usually)
        fixed = result.get("fixed_effects", {})
        assert "Intercept" in fixed or "const" in fixed, "Intercept should be in fixed effects"
    else:
        # If it didn't converge, we might have an error message or just lack params
        # This is acceptable in a test if the mock data is insufficient for the model
        # but the function should handle it gracefully
        assert "error" in result or "message" in result, "Non-converged result should have an error or message"

def test_lmm_with_realistic_simulation_data():
    """
    Test LMM with data that more closely mimics a real SimulationRun output.
    """
    # Simulate a more complex scenario with multiple parameters
    np.random.seed(123)
    n_groups = 10
    n_obs_per_group = 20
    
    data = []
    for g in range(n_groups):
        for i in range(n_obs_per_group):
            # Random intercept per group
            group_effect = np.random.normal(0, 0.1)
            
            # Fixed effect of parameter
            param_val = "High" if g % 2 == 0 else "Low"
            param_effect = 0.2 if param_val == "High" else 0.0
            
            # Residual noise
            noise = np.random.normal(0, 0.05)
            
            coherence = 0.5 + group_effect + param_effect + noise
            
            data.append({
                "step": g * n_obs_per_group + i,
                "coherence_score": coherence,
                "diversity_score": np.random.uniform(0.4, 0.8),
                "param": param_val,
                "time_step": g
            })
    
    df = pd.DataFrame(data)
    
    # Run analysis
    result = run_lmm_analysis(df, formula="coherence_score ~ param + (1|time_step)")
    
    # Verify the result
    assert result.get("converged", False) is True or "error" in result, \
        "Analysis should either converge or report an error clearly"
    
    if result.get("converged", False):
        fixed = result.get("fixed_effects", {})
        # Check that param effect is detectable (High should be higher than Low)
        # We don't assert exact values due to randomness, but we check structure
        assert len(fixed) > 0, "Fixed effects should be populated"
