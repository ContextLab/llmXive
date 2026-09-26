import pytest
import os
import json
import math
import numpy as np
from pathlib import Path

# Import from project modules
from simulation.generator import (
    SimulationConfig, 
    StudyResult, 
    SimulationResult, 
    load_base_data_structure, 
    calculate_effect_and_variance, 
    create_replicate, 
    validate_simulation_output,
    generate_synthetic_meta_analysis
)
from config_loader import get_base_data_path, get_replicate_count, get_tau2_levels, get_random_seed

@pytest.fixture
def mock_base_data():
    """Create a mock base data structure for testing."""
    return {
        'effect_sizes': [0.5, 0.6, 0.4, 0.7, 0.55],
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
    
    data = load_base_data_structure()
    assert 'effect_sizes' in data
    assert 'ses' in data
    assert 'N_studies' in data
    assert len(data['effect_sizes']) == data['N_studies']
    assert len(data['ses']) == data['N_studies']

def test_calculate_effect_and_variance_zero_tau2(rng):
    """Test effect calculation when tau2 is 0 (homogeneity)."""
    true_effect = 0.5
    tau2 = 0.0
    base_se = 0.1
    
    obs_effect, obs_se = calculate_effect_and_variance(true_effect, tau2, base_se, rng)
    
    # When tau2=0, between-study variance is 0, so total_var = base_se^2
    expected_se = math.sqrt(base_se**2 + tau2)
    assert math.isclose(obs_se, expected_se, rel_tol=1e-5)
    
    # The effect should be close to true_effect + noise
    # We can't assert exact value due to randomness, but we can check it's in a reasonable range
    assert abs(obs_effect - true_effect) < 3 * expected_se, "Observed effect is too far from true effect"

def test_calculate_effect_and_variance_positive_tau2(rng):
    """Test effect calculation when tau2 > 0."""
    true_effect = 0.5
    tau2 = 0.25
    base_se = 0.1
    
    obs_effect, obs_se = calculate_effect_and_variance(true_effect, tau2, base_se, rng)
    
    expected_se = math.sqrt(base_se**2 + tau2)
    assert math.isclose(obs_se, expected_se, rel_tol=1e-5)

def test_create_replicate(mock_base_data, rng):
    """Test that a replicate is created with the correct structure."""
    config = SimulationConfig(
        true_effect=0.5,
        tau2=0.1,
        replicate_id=0,
        n_studies=5
    )
    
    result = create_replicate(config, mock_base_data, rng)
    
    assert result.injected_true_effect == 0.5
    assert result.injected_tau2 == 0.1
    assert result.N_studies == 5
    assert len(result.studies) == 5
    assert result.replicate_id == 0
    
    # Check study structure
    for study in result.studies:
        assert 'effect' in study
        assert 'se' in study
        assert 'study_id' in study
        assert study['study_id'] < 5

def test_validate_simulation_output(mock_base_data, rng):
    """Test that validation passes for valid results."""
    config = SimulationConfig(
        true_effect=0.5,
        tau2=0.1,
        replicate_id=0,
        n_studies=5
    )
    
    result = create_replicate(config, mock_base_data, rng)
    results = [result]
    
    assert validate_simulation_output(results) is True

def test_validate_simulation_output_invalid_structure():
    """Test that validation fails for invalid results."""
    invalid_result = SimulationResult(
        injected_true_effect=0.5,
        injected_tau2=0.1,
        N_studies=5,
        studies=[],  # Empty studies list
        replicate_id=0
    )
    
    assert validate_simulation_output([invalid_result]) is False

def test_variance_match_unit_test(mock_base_data, rng):
    """
    Unit test to verify that generated variance matches injected tau2 within Monte Carlo error.
    This test uses a small number of replicates for speed.
    """
    n_replicates = 100
    tau2_target = 0.5
    true_effect = 0.5
    n_studies = 20
    
    # Generate multiple replicates
    results = []
    for i in range(n_replicates):
        config = SimulationConfig(
            true_effect=true_effect,
            tau2=tau2_target,
            replicate_id=i,
            n_studies=n_studies
        )
        result = create_replicate(config, mock_base_data, rng)
        results.append(result)
    
    # Extract all effects and compute empirical variance
    all_effects = []
    for res in results:
        for study in res.studies:
            all_effects.append(study['effect'])
    
    # The variance of effects should be approximately tau2 + mean(se^2)
    # But for simplicity, we check that the between-study variance is close to tau2
    # We'll compute the variance of the means of each replicate
    replicate_means = [np.mean([s['effect'] for s in res.studies]) for res in results]
    empirical_var_between = np.var(replicate_means, ddof=1)
    
    # The expected variance of the mean is (tau2 + avg_se^2 / n_studies)
    # This is a rough check; in practice, we'd need a more sophisticated test
    # For now, we just ensure it's in the right ballpark
    avg_se_sq = np.mean([s['se']**2 for res in results for s in res.studies])
    expected_var_mean = tau2_target + avg_se_sq / n_studies
    
    # Allow for Monte Carlo error (10% tolerance)
    tolerance = 0.1 * expected_var_mean
    assert abs(empirical_var_between - expected_var_mean) < tolerance, \
        f"Empirical variance {empirical_var_between} differs too much from expected {expected_var_mean}"

def test_homogeneity_check(mock_base_data, rng):
    """
    Unit test to verify that tau2=0 produces zero between-study variance (homogeneity).
    """
    n_replicates = 50
    tau2_target = 0.0
    true_effect = 0.5
    n_studies = 20
    
    replicate_means = []
    for i in range(n_replicates):
        config = SimulationConfig(
            true_effect=true_effect,
            tau2=tau2_target,
            replicate_id=i,
            n_studies=n_studies
        )
        result = create_replicate(config, mock_base_data, rng)
        replicate_means.append(np.mean([s['effect'] for s in result.studies]))
    
    # When tau2=0, the between-study variance should be very small (only due to sampling error)
    empirical_var_between = np.var(replicate_means, ddof=1)
    
    # The expected variance of the mean is avg_se^2 / n_studies
    # We'll compute a rough bound
    all_ses = [s['se'] for res in [create_replicate(SimulationConfig(true_effect, tau2_target, i, n_studies), mock_base_data, rng) for i in range(n_replicates)] for s in res.studies]
    avg_se_sq = np.mean([se**2 for se in all_ses])
    expected_var_mean = avg_se_sq / n_studies
    
    # Allow for some Monte Carlo error
    assert empirical_var_between < 2 * expected_var_mean, \
        f"Empirical variance {empirical_var_between} is too large for tau2=0 (expected < {2 * expected_var_mean})"
