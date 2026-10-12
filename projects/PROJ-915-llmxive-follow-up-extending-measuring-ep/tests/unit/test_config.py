"""Unit tests for code/config.py (T004)."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import config  # noqa: E402


def test_seed_constant():
    assert config.SEED == 42


def test_max_runtime_hours():
    assert config.MAX_RUNTIME_HOURS == 6


def test_data_root():
    assert config.DATA_ROOT == Path("../data")


def test_results_root():
    assert config.RESULTS_ROOT == Path("../data/results")


def test_get_config_includes_constants():
    cfg = config.get_config()
    assert cfg["SEED"] == 42
    assert cfg["MAX_RUNTIME_HOURS"] == 6
    assert cfg["DATA_ROOT"] == "../data"
    assert cfg["RESULTS_ROOT"] == "../data/results"