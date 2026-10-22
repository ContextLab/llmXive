"""
Unit tests for the project's configuration module.

These tests verify that:
1. The default random seed is set to 42.
2. ``ensure_directories`` creates only the allowed top‑level directories
   (excluding the platform‑owned ``state/`` directory).
3. ``get_config_summary`` returns a dictionary with the expected structure.
"""

import os
from pathlib import Path

from code.config import Hyperparameters, ensure_directories, get_config_summary
from llmxive_toolkit import paths

def test_hyperparameters_random_seed():
    """Hyperparameters should expose a default random seed of 42."""
    hp = Hyperparameters()
    assert hp.random_seed == 42, "Default random seed should be 42"

def test_ensure_directories_excludes_state(tmp_path, monkeypatch):
    """
    ``ensure_directories`` must not create the platform‑owned ``state/`` folder.
    The test runs in a temporary directory to avoid interfering with the real
    project layout.
    """
    # Monkey‑patch the ``paths`` helpers to point at the temporary directory.
    monkeypatch.setattr(paths, "root", Path(tmp_path))
    monkeypatch.setattr(paths, "data", lambda *parts: Path(tmp_path) / "data" / Path(*parts))
    monkeypatch.setattr(paths, "code", lambda: Path(tmp_path) / "code")
    monkeypatch.setattr(paths, "tests", lambda: Path(tmp_path) / "tests")
    monkeypatch.setattr(paths, "docs", lambda: Path(tmp_path) / "docs")
    monkeypatch.setattr(paths, "contracts", lambda: Path(tmp_path) / "contracts")
    monkeypatch.setattr(paths, "results", lambda: Path(tmp_path) / "results")
    # Note: we deliberately do NOT patch ``paths.state`` because it must not be used.

    # Run the directory‑creation helper.
    ensure_directories()

    # Expected directories (relative to the temporary root)
    expected_dirs = [
        Path("data/raw"),
        Path("data/derived"),
        Path("code"),
        Path("tests"),
        Path("docs"),
        Path("contracts"),
        Path("results"),
    ]

    for rel_dir in expected_dirs:
        assert (Path(tmp_path) / rel_dir).is_dir(), f"Directory {rel_dir} should exist"

    # The ``state`` directory must NOT be created by ``ensure_directories``.
    assert not (Path(tmp_path) / "state").exists(), "`state/` should not be created by ensure_directories"

def test_get_config_summary_structure():
    """The summary should contain hyperparameters and the allowed directory paths."""
    summary = get_config_summary()
    # Hyperparameters dict must contain the random seed.
    assert "hyperparameters" in summary
    assert summary["hyperparameters"]["random_seed"] == 42

    # Directories dict must contain exactly the allowed keys.
    expected_keys = {
        "data_raw",
        "data_derived",
        "code",
        "tests",
        "docs",
        "contracts",
        "results",
    }
    assert "directories" in summary
    assert set(summary["directories"].keys()) == expected_keys