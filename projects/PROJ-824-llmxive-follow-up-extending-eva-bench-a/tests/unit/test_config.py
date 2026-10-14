"""Unit tests for code/config.py (task T002)."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import config  # noqa: E402


def test_delay_values():
    assert config.DELAY_VALUES == [
        200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000
    ]


def test_path_constants():
    assert config.DATA_RAW == config.PROJECT_ROOT / "data" / "raw"
    assert config.DATA_PROCESSED == config.PROJECT_ROOT / "data" / "processed"
    assert config.RESULTS_DIR == config.PROJECT_ROOT / "data" / "results"


def test_seed_handling():
    assert config.SEED == config.RANDOM_SEED == 42
    config.set_global_seed(123)
    assert config.SEED == 123
    config.set_global_seed(42)
    assert config.SEED == 42


def test_ensure_directories(tmp_path, monkeypatch):
    # ensure_directories should not raise and should be idempotent
    config.ensure_directories()
    config.ensure_directories()
    assert config.DATA_RAW.exists()
    assert config.DATA_PROCESSED.exists()
    assert config.RESULTS_DIR.exists()