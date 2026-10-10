import pytest
import os
import math
import numpy as np
from pathlib import Path
from typing import List

# Import from project modules
from simulation.generator import (
    SimulationConfig, 
    SimulationResult, 
    load_base_data_structure, 
    calculate_effect_and_variance, 
    create_replicate, 
    validate_simulation_output,
    generate_synthetic_meta_analysis
)
from config_loader import get_base_data_path

@pytest.fixture
def mock_base_data():
    """Create mock base data lists for testing."""
    return {
        'effects': [0.5, 0.6, 0.4, 0.7, 0.55],
        'ses': [0.1, 0.12, 0.11, 0.09, 0.1],
        'N_studies': 5
    }

@pytest.fixture
def rng():
    """Create a deterministic RNG for testing."""
    return np.random.default_rng(42)

def test_load_base_data_structure():
    """Test that base data is loaded correctly from the configured path."""
    base_path = get_base_data_path()
    assert os.path.exists(base_path), f"Base data file not found at {base_path}"
    
    effects, ses = load_base_data_structure(str(base_path))
    assert len(effects) > 0
    assert len(effects) == len(ses)

def test_calculate_effect_and_variance_zero_tau2(rng):
    """Test effect calculation when tau2 is 0 (homogeneity)."""
    true_effect = 0.5
    tau2 = 0.0
    base_se = 0.1
    
    obs_effect, obs_var = calculate_effect_and_variance(0.0, base_se, true_effect, tau2, rng)
    
    # Variance should be exactly base_se^2
    assert math.isclose(obs_var, base_se**2, rel_tol=1e-5)
    # Effect should be within a reasonable range (3 sigma)
    assert abs(obs_effect - true_effect) < 3 * base_se

def test_create_replicate(mock_base_data, rng):
    """Test that a replicate is created with the correct structure."""
    config = SimulationConfig(
        injected_true_effect=0.5,
        injected_tau2=0.1,
        N_studies=5,
        base_data_path="dummy_path",
        seed=42
    )
    
    result = create_replicate(config, mock_base_data['effects'], mock_base_data['ses'], rng)
    
    assert isinstance(result, SimulationResult)
    assert result.injected_true_effect == 0.5
    assert result.injected_tau2 == 0.1
    assert result.N_studies == 5
    assert len(result.studies) == 5
    
    for study in result.studies:
        assert 'effect_size' in study
        assert 'standard_error' in study
        assert 'variance' in study

def test_validate_simulation_output(mock_base_data, rng):
    """Test that validation passes for valid results."""
    config = SimulationConfig(
        injected_true_effect=0.5,
        injected_tau2=0.1,
        N_studies=5,
        base_data_path="dummy_path",
        seed=42
    )
    
    result = create_replicate(config, mock_base_data['effects'], mock_base_data['ses'], rng)
    assert validate_simulation_output([result]) is True

def test_variance_match_unit_test(mock_base_data, rng):
    """
    Verify that the injected tau^2 matches the empirical variance 
    of generated effect sizes within 0.05.
    """
    tau2_target = 0.5
    true_effect = 0.5
    n_studies = 20
    n_replicates = 500
    
    config = SimulationConfig(
        injected_true_effect=true_effect,
        injected_tau2=tau2_target,
        N_studies=n_studies,
        base_data_path="dummy_path",
        seed=42
    )
    
    obs_tau2_values = []
    for i in range(n_replicates):
        sub_rng = np.random.default_rng(config.seed + i)
        result = create_replicate(config, mock_base_data['effects'], mock_base_data['ses'], sub_rng)
        obs_tau2_values.append(result.observed_between_study_variance)
    
    mean_obs_tau2 = np.mean(obs_tau2_values)
    
    # Verification: injected tau^2 matches empirical variance within 0.05
    assert abs(mean_obs_tau2 - tau2_target) < 0.05, \
        f"Empirical tau^2 {mean_obs_tau2:.4f} differs from target {tau2_target} by more than 0.05"

def test_homogeneity_check(mock_base_data, rng):
    """
    Verify that tau2=0 produces near-zero between-study variance.
    """
    tau2_target = 0.0
    n_studies = 20
    n_replicates = 100
    
    config = SimulationConfig(
        injected_true_effect=0.5,
        injected_tau2=tau2_target,
        N_studies=n_studies,
        base_data_path="dummy_path",
        seed=42
    )
    
    obs_tau2_values = []
    for i in range(n_replicates):
        sub_rng = np.random.default_rng(config.seed + i)
        result = create_replicate(config, mock_base_data['effects'], mock_base_data['ses'], sub_rng)
        obs_tau2_values.append(result.observed_between_study_variance)
    
    mean_obs_tau2 = np.mean(obs_tau2_values)
    # For tau2=0, the MoM estimator should be very close to 0
    assert mean_obs_tau2 < 0.05, f"Expected near-zero tau^2 for homogeneity, got {mean_obs_tau2:.4f}"