"""Unit tests for code/config.py (Task T008)."""
import os
import sys

# Make the code/ package importable when pytest runs from the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import config
from config import (
    MAX_PARAM_INCREASE_RATIO,
    Hyperparameters,
    SafetyConstraints,
    PathConfig,
    Config,
    get_config,
    set_config,
    get_learning_rate,
    get_batch_size,
    get_seed,
    get_ram_limit,
    get_trajectory_path,
    get_max_param_increase_percent,
    get_bootstrap_resamples,
    set_seed,
    ensure_directories,
    _clamp_param_ratio,
    _parse_research_md_for_param_limit,
)


def test_module_level_cap():
    """FR-003: the module-level cap must never exceed 0.30."""
    assert MAX_PARAM_INCREASE_RATIO <= 0.30


def test_hyperparameters_defaults():
    """FR-004: lr = 5e-5, batch size = 4, seed defined."""
    hp = Hyperparameters()
    assert hp.lr == 5e-5
    assert hp.batch_size == 4
    assert isinstance(hp.seed, int)
    assert hp.epochs == 1


def test_accessors():
    assert get_learning_rate() == 5e-5
    assert get_batch_size() == 4
    assert isinstance(get_seed(), int)
    assert get_ram_limit() <= 7.0
    assert get_trajectory_path().endswith("trajectory.json")
    assert get_bootstrap_resamples() > 0


def test_research_md_ratio_is_clamped():
    """Any ratio read from research.md must be <= 0.30 (FR-003)."""
    ratio = get_max_param_increase_percent()
    if ratio is not None:
        assert ratio <= 0.30


def test_clamp_logic():
    assert _clamp_param_ratio(0.50) == 0.30
    assert _clamp_param_ratio(0.25) == 0.25
    assert _clamp_param_ratio(None) is None
    assert _clamp_param_ratio(0.30) == 0.30


def test_parse_research_md():
    """research.md defines 0.30; parsing must return it (or None), never > 0.30."""
    cfg = get_config()
    value = _parse_research_md_for_param_limit(cfg.paths.research_md)
    if value is not None:
        assert value <= 0.30


def test_set_and_get_config_roundtrip():
    cfg = Config(
        Hyperparameters(lr=1e-4, batch_size=8, seed=7),
        SafetyConstraints(max_param_increase_ratio=0.10),
        PathConfig("."),
    )
    previous = get_config()
    try:
        set_config(cfg)
        assert get_config() is cfg
        assert get_learning_rate() == 1e-4
        assert get_batch_size() == 8
        assert get_seed() == 7
        assert get_max_param_increase_percent() == 0.10
    finally:
        set_config(previous)


def test_ensure_directories_and_seed():
    ensure_directories()
    cfg = get_config()
    for d in [cfg.paths.data_raw, cfg.paths.data_processed, cfg.paths.results, cfg.paths.state]:
        assert os.path.isdir(d)
    set_seed(get_seed())