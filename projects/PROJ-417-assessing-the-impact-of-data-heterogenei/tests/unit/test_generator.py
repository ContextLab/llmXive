"""
Unit tests for the simulation generator (Task T002, FR-001).

Verification criterion (tasks.md T002): the injected tau^2 matches the
empirical (method-of-moments) between-study variance of the generated
effect sizes within 0.05, using deterministic per-replicate seeding
(Constitution Principle I).

These tests are written WITHOUT pytest fixtures so they can also be
executed directly by ``code/scripts/verify_generator.py`` (which does
not require pytest to be installed), while remaining fully compatible
with ``pytest tests/unit/test_generator.py``.
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

# Deterministic pseudo base data: 20 studies, SEs in a realistic
# meta-analysis range (~0.08 - 0.18).
BASE_EFFECTS = [0.0] * 20
BASE_SES = [round(0.08 + 0.005 * i, 4) for i in range(20)]

REAL_BASE_CANDIDATES = [
    Path("data/raw/cochrane_base.csv"),
    Path("data/raw/cochrane_base_synthetic.csv"),
]


def _make_config(tau2: float, seed: int = 42, n_studies: int = 20) -> SimulationConfig:
    return SimulationConfig(
        injected_true_effect=0.5,
        injected_tau2=tau2,
        N_studies=n_studies,
        base_data_path="dummy_path",
        seed=seed,
    )


def test_load_base_data_structure():
    """Base data (effect sizes / standard errors) loads correctly from CSV."""
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

def test_load_base_data_structure_missing_file_raises():
    """A missing base data file must raise FileNotFoundError (fail loudly)."""
    try:
        load_base_data_structure("data/raw/does_not_exist_12345.csv")
    except FileNotFoundError:
        return
    raise AssertionError("Expected FileNotFoundError for missing base data file")

def test_load_base_data_structure_real_base():
    """If a real project base data file exists, it loads with valid values."""
    base = next((p for p in REAL_BASE_CANDIDATES if p.exists()), None)
    if base is None:
        # Nothing on disk yet in this environment; nothing to assert.
        return
    effects, ses = load_base_data_structure(str(base))
    assert len(effects) > 0
    assert len(effects) == len(ses)
    assert all(s > 0 for s in ses)
    assert all(math.isfinite(e) for e in effects)

def test_calculate_effect_and_variance_zero_tau2():
    """tau2 = 0 yields variance exactly base_se^2 and effect near truth."""
    rng = np.random.default_rng(42)
    true_effect = 0.5
    base_se = 0.1
    obs_effect, obs_var = calculate_effect_and_variance(
        0.0, base_se, true_effect, 0.0, rng
    )
    assert math.isclose(obs_var, base_se ** 2, rel_tol=1e-5)
    assert abs(obs_effect - true_effect) < 3 * base_se

def test_create_replicate():
    """A replicate has the correct structure and injected parameters."""
    rng = np.random.default_rng(42)
    config = _make_config(0.1, n_studies=5)
    result = create_replicate(config, BASE_EFFECTS[:5], BASE_SES[:5], rng)
    assert isinstance(result, SimulationResult)
    assert result.injected_true_effect == 0.5
    assert result.injected_tau2 == 0.1
    assert result.N_studies == 5
    assert len(result.studies) == 5
    for study in result.studies:
        assert "study_id" in study
        assert "effect_size" in study
        assert "standard_error" in study
        assert "variance" in study

def test_validate_simulation_output():
    """Generated output passes structural validation."""
    rng = np.random.default_rng(42)
    config = _make_config(0.1)
    result = create_replicate(config, BASE_EFFECTS, BASE_SES, rng)
    assert validate_simulation_output([result]) is True

def test_deterministic_seeding():
    """Same pinned seed -> bit-identical replicates (Constitution Principle I)."""
    config = _make_config(0.5, seed=42)
    rng_a = np.random.default_rng(42)
    rng_b = np.random.default_rng(42)
    res_a = create_replicate(config, BASE_EFFECTS, BASE_SES, rng_a)
    res_b = create_replicate(config, BASE_EFFECTS, BASE_SES, rng_b)
    assert res_a.mean_effect == res_b.mean_effect
    assert res_a.observed_between_study_variance == res_b.observed_between_study_variance
    assert [s["effect_size"] for s in res_a.studies] == [
        s["effect_size"] for s in res_b.studies
    ]

def test_variance_match_unit_test():
    """
    T002 verification: injected tau^2 matches the empirical variance of
    generated effect sizes within 0.05 (method-of-moments estimator,
    averaged over 500 replicates with deterministic per-replicate seeds).
    """
    tau2_target = 0.5
    n_replicates = 500
    config = _make_config(tau2_target, seed=42, n_studies=20)

    obs_tau2_values = []
    for i in range(n_replicates):
        sub_rng = np.random.default_rng(config.seed + i)
        result = create_replicate(config, BASE_EFFECTS, BASE_SES, sub_rng)
        obs_tau2_values.append(result.observed_between_study_variance)

    mean_obs_tau2 = float(np.mean(obs_tau2_values))
    assert abs(mean_obs_tau2 - tau2_target) < 0.05, (
        f"Empirical tau^2 {mean_obs_tau2:.4f} differs from target "
        f"{tau2_target} by more than 0.05"
    )

def test_homogeneity_check():
    """tau2 = 0 produces near-zero empirical between-study variance."""
    n_replicates = 100
    config = _make_config(0.0, seed=42, n_studies=20)

    obs_tau2_values = []
    for i in range(n_replicates):
        sub_rng = np.random.default_rng(config.seed + i)
        result = create_replicate(config, BASE_EFFECTS, BASE_SES, sub_rng)
        obs_tau2_values.append(result.observed_between_study_variance)

    mean_obs_tau2 = float(np.mean(obs_tau2_values))
    assert mean_obs_tau2 < 0.05, (
        f"Expected near-zero tau^2 for homogeneity, got {mean_obs_tau2:.4f}"
    )
