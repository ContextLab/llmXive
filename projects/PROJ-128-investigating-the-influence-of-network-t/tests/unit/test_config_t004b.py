"""Unit tests for T004b hyperparameter definitions in code/config.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

import config


def test_window_lengths_and_step():
    assert config.WINDOW_LENGTH_BASELINE == 30
    assert config.WINDOW_LENGTH_VALIDATION == [20]
    assert isinstance(config.WINDOW_LENGTH_VALIDATION, list)
    assert config.WINDOW_STEP == 1


def test_k_means_k():
    assert config.K_MEANS_K == 5


def test_baseline_density_defined():
    assert hasattr(config, "BASELINE_DENSITY")
    assert isinstance(config.BASELINE_DENSITY, float)
    assert 0.0 < config.BASELINE_DENSITY < 1.0


def test_density_variations_are_explicit_relative_perturbation():
    b = config.BASELINE_DENSITY
    expected = [
        round(b * 0.95, 6),
        b,
        round(b * 1.05, 6),
    ]
    assert config.DENSITY_THRESHOLD_VARIATIONS == expected
    assert len(config.DENSITY_THRESHOLD_VARIATIONS) == 3


def test_backward_compatible_alias():
    assert config.DENSITY_THRESHOLD_BASELINE == config.BASELINE_DENSITY


def test_get_config_dict_consistency():
    cfg = config.get_config_dict()
    assert cfg["window_length_baseline"] == 30
    assert cfg["window_length_validation"] == [20]
    assert cfg["k_means_k"] == 5
    assert cfg["baseline_density"] == config.BASELINE_DENSITY
    assert cfg["density_threshold_variations"] == config.DENSITY_THRESHOLD_VARIATIONS