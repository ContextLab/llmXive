"""Unit tests for T001: seed initialization and reproducibility."""
import random
import sys
from pathlib import Path

import numpy as np
import pytest

CODE_DIR = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(CODE_DIR))

import seed_init  # noqa: E402


def test_seed_constants():
    assert seed_init.RANDOM_SEED == 42


def test_main_writes_log_and_succeeds(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = seed_init.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "Pipeline completed successfully" in out
    # The log must be written inside the project tree (llmxive_toolkit
    # resolves the project root), not the tmp cwd.
    from llmxive_toolkit import paths

    log_file = paths.path("logs", "seed_initialization.log")
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "random.seed(42) set: True" in content
    assert "np.random.seed(42) set: True" in content
    assert "seeds_verified: True" in content


def test_seeds_are_deterministic():
    random.seed(42)
    np.random.seed(42)
    assert abs(random.random() - 0.6394267984578837) < 1e-12
    assert abs(float(np.random.random()) - 0.3745401188473625) < 1e-12