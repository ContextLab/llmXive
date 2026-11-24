"""Tests for T009: environment configuration management with config.yaml overrides."""
import sys
from pathlib import Path

import pytest

CODE_DIR = Path(__file__).resolve().parents[2] / 'code'
sys.path.insert(0, str(CODE_DIR))

from config import (  # noqa: E402
    Config,
    DEFAULT_PATHS,
    DEFAULT_SEEDS,
    DEFAULT_THRESHOLDS,
    PROJECT_ROOT,
    find_config_yaml,
    get_config,
    load_yaml_overrides,
    reset_config,
)


def setup_function(_fn):
    reset_config()


def teardown_function(_fn):
    reset_config()


def test_defaults_without_yaml():
    cfg = Config(yaml_path=PROJECT_ROOT / 'nonexistent_config.yaml')
    assert cfg.seeds['training_seed'] == 42
    assert cfg.seeds['holdout_seed'] == 43
    assert cfg.thresholds['fidelity_tolerance'] == 0.90
    assert cfg.thresholds['holdout_variance_multiplier'] == 1.5
    assert cfg.paths['training_dir'] == DEFAULT_PATHS['training_dir']


def test_yaml_overrides_seeds_and_paths(tmp_path):
    yaml_file = tmp_path / 'config.yaml'
    yaml_file.write_text(
        "project:\n"
        "  seed: 99\n"
        "paths:\n"
        "  data_held_out: custom/held_out\n"
        "rule_induction:\n"
        "  fidelity_threshold: 0.95\n"
        "generation:\n"
        "  variance_multiplier: 2.0\n",
        encoding='utf-8',
    )
    cfg = Config(yaml_path=yaml_file)
    assert cfg.seeds['random_seed'] == 99
    assert cfg.paths['held_out_dir'] == PROJECT_ROOT / 'custom' / 'held_out'
    assert cfg.thresholds['fidelity_threshold'] == 0.95
    assert cfg.thresholds['holdout_variance_multiplier'] == 2.0
    # Untouched defaults remain
    assert cfg.seeds['training_seed'] == DEFAULT_SEEDS['training_seed']


def test_yaml_invalid_section_raises(tmp_path):
    yaml_file = tmp_path / 'config.yaml'
    yaml_file.write_text("paths: [1, 2, 3]\n", encoding='utf-8')
    with pytest.raises(ValueError):
        Config(yaml_path=yaml_file)


def test_env_overrides_take_precedence(monkeypatch, tmp_path):
    yaml_file = tmp_path / 'config.yaml'
    yaml_file.write_text("project:\n  seed: 7\n", encoding='utf-8')
    monkeypatch.setenv('LLMXIVE_SEEDS_TRAINING_SEED', '123')
    monkeypatch.setenv('LLMXIVE_THRESHOLDS_FIDELITY_TOLERANCE', '0.85')
    cfg = Config(yaml_path=yaml_path)
    assert cfg.seeds['training_seed'] == 123
    assert cfg.thresholds['fidelity_tolerance'] == 0.85
    # YAML still applies where env does not override
    assert cfg.seeds['random_seed'] == 7


def test_singleton_and_reset():
    cfg1 = get_config()
    cfg2 = get_config()
    assert cfg1 is cfg2
    reset_config()
    cfg3 = get_config()
    assert cfg3 is not cfg1


def test_dict_like_access():
    cfg = get_config()
    assert cfg['training_seed'] == 42
    assert 'missing_key_xyz' not in cfg
    assert cfg.get('missing_key_xyz', 'fallback') == 'fallback'
    with pytest.raises(KeyError):
        cfg['missing_key_xyz']


def test_find_config_yaml_returns_existing_or_none():
    result = find_config_yaml()
    assert result is None or result.is_file()


def test_load_yaml_overrides_empty_for_missing_file(tmp_path):
    assert load_yaml_overrides(tmp_path / 'nope.yaml') == {}
