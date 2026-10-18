"""Unit tests for code/config.py (T001)."""
import importlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from config import Config  # noqa: E402


def test_config_importable():
    """T001 verification: code/config.py imports without errors."""
    assert Config is not None


def test_cpu_only_enforcement(monkeypatch):
    """DEVICE must default to 'cpu' unless explicitly overridden."""
    monkeypatch.delenv("DREAM_STATE_ALLOW_GPU", raising=False)
    cfg = Config()
    assert cfg.DEVICE == "cpu"


def test_memory_limit_is_6_3_gb():
    """FR-005: hard memory limit must be 6.3 GB."""
    assert Config.MAX_MEMORY_GB == pytest.approx(6.3)


def test_memory_limit_below_runner_budget():
    assert Config.MAX_MEMORY_GB < 7.0


def test_warmup_is_20_steps():
    """FR-007: warm-up must be exactly 20 wake-only steps."""
    assert Config.WARMUP_STEPS == 20


def test_wake_dream_ratio_is_4_to_1():
    """US-1: 4:1 wake-to-dream ratio."""
    assert Config.WAKE_TO_DREAM_RATIO == 4


def test_temperature_sweep_matches_spec():
    """FR-006: sweep across [0.5, 1.0, 1.5, 2.0]."""
    assert Config.TEMPERATURES == [0.5, 1.0, 1.5, 2.0]


def test_seed_reproducibility():
    """Constructing with a fixed seed must be deterministic."""
    import numpy as np

    Config(seed=123)
    a = np.random.randint(0, 1000, size=10)
    Config(seed=123)
    b = np.random.randint(0, 1000, size=10)
    assert list(a) == list(b)


def test_directories_created():
    cfg = Config()
    for d in [cfg.DATA_DIR, cfg.RAW_DATA_DIR, cfg.CHECKPOINTS_DIR,
              cfg.RESULTS_DIR, cfg.LOGS_DIR]:
        assert Path(d).exists()


def test_get_accessor():
    cfg = Config()
    assert cfg.get("significance_level", 0.05) == 0.05
    assert cfg.get("nonexistent_key", "fallback") == "fallback"


def test_to_dict_roundtrip():
    cfg = Config(seed=7)
    d = cfg.to_dict()
    assert d["max_memory_gb"] == pytest.approx(6.3)
    assert d["warmup_steps"] == 20
    cfg2 = Config.from_dict(d)
    assert cfg2.to_dict() == d