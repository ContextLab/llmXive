"""
Unit tests for the simulation generator (Task T002, FR-001).
"""
import csv
import math
import os
import sys
import tempfile
from pathlib import Path
import numpy as np
from simulation.generator import (
    SimulationConfig,
    SimulationResult,
    load_base_data_structure,
    calculate_effect_and_variance,
    create_replicate,
    validate_simulation_output,
)

BASE_EFFECTS = [0.0] * 20
BASE_SES = [round(0.08 + 0.005 * i, 4) for i in range(20)]

def _make_config(tau2: float, seed: int = 42, n_studies: int = 20) -> SimulationConfig:
    return SimulationConfig(
        injected_true_effect=0.5,
        injected_tau2=tau2,
        N_studies=n_studies,
        base_data_path="dummy_path",
        seed=seed,
    )

def test_load_base_data_structure():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "base.csv")
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["study_id", "effect_size", "standard_error"])
            for i, (e, s) in enumerate(zip(BASE_EFFECTS, BASE_SES)):
                writer.writerow([f"s{i}", e, s])
        effects, ses = load_base_data_structure(path)
    assert len(effects) == 20
    assert len(ses) == 20
    assert all(math.isclose(a, b) for a, b in zip(ses, BASE_SES))

def test_calculate_effect_and_variance_zero_tau2():
    rng = np.random.default_rng(42)
    true_effect = 0.5
    base_se = 0.1
    obs_effect, obs_var = calculate_effect_and_variance(0.0, base_se, true_effect, 0.0, rng)
    assert math.isclose(obs_var, base_se ** 2, rel_tol=1e-5)
    assert abs(obs_effect - true_effect) < 3 * base_se

def test_create_replicate():
    rng = np.random.default_rng(42)
    config = _make_config(0.1, n_studies=5)
    result = create_replicate(config, BASE_EFFECTS[:5], BASE_SES[:5], rng)
    assert isinstance(result, SimulationResult)
    assert result.injected_tau2 == 0.1
    assert len(result.studies) == 5

def test_validate_simulation_output():
    rng = np.random.default_rng(42)
    config = _make_config(0.1)
    result = create_replicate(config, BASE_EFFECTS, BASE_SES, rng)
    assert validate_simulation_output([result]) is True

def test_deterministic_seeding():
    config = _make_config(0.5, seed=42)
    rng_a = np.random.default_rng(42)
    rng_b = np.random.default_rng(42)
    res_a = create_replicate(config, BASE_EFFECTS, BASE_SES, rng_a)
    res_b = create_replicate(config, BASE_EFFECTS, BASE_SES, rng_b)
    assert res_a.mean_effect == res_b.mean_effect
    assert [s["effect_size"] for s in res_a.studies] == [s["effect_size"] for s in res_b.studies]

def test_variance_match_unit_test():
    tau2_target = 0.5
    n_replicates = 500
    config = _make_config(tau2_target, seed=42, n_studies=20)
    obs_tau2_values = []
    for i in range(n_replicates):
        sub_rng = np.random.default_rng(config.seed + i)
        result = create_replicate(config, BASE_EFFECTS, BASE_SES, sub_rng)
        obs_tau2_values.append(result.observed_between_study_variance)
    mean_obs_tau2 = float(np.mean(obs_tau2_values))
    assert abs(mean_obs_tau2 - tau2_target) < 0.05