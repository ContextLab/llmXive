"""
Unit tests for ``code.utils.config``.
"""

import os
import json
import subprocess
from pathlib import Path

import pytest
import numpy as np

# Import the module under test
from code.utils import config

def test_load_city_list_success(tmp_path, monkeypatch):
    """
    Verify that ``load_city_list`` correctly reads a temporary city list file.
    """
    # Create a temporary city list file
    test_file = tmp_path / "city_list.txt"
    test_file.write_text("Alpha\nBeta\nGamma\n", encoding="utf-8")

    # Monkey‑patch the default path to point to our temporary file
    monkeypatch.setattr(
        config.paths, "data", lambda *parts: tmp_path / Path(*parts)
    )

    cities = config.load_city_list()
    assert cities == ["Alpha", "Beta", "Gamma"]

def test_load_city_list_missing():
    """
    Ensure a missing file raises ``FileNotFoundError``.
    """
    with pytest.raises(FileNotFoundError):
        config.load_city_list(Path("non_existent_file.txt"))

def test_set_random_seeds_reproducibility():
    """
    After setting the seed, NumPy random numbers should be reproducible.
    """
    seed = 12345
    config.set_random_seeds(seed)

    first = np.random.rand(5)
    # Reset the seed and generate again
    config.set_random_seeds(seed)
    second = np.random.rand(5)

    np.testing.assert_array_equal(first, second)

def test_get_config_returns_expected_structure(monkeypatch):
    """
    ``get_config`` should return a dict with ``city_list`` and ``seed`` keys.
    """
    # Prepare a temporary city list file
    tmp_dir = Path(os.getenv("TMPDIR", "/tmp"))
    city_file = tmp_dir / "city_list.txt"
    city_file.write_text("Delta\nEpsilon\n", encoding="utf-8")

    # Monkey‑patch the default data path to our temporary file
    monkeypatch.setattr(
        config.paths, "data", lambda *parts: tmp_dir / Path(*parts)
    )

    cfg = config.get_config(seed=999)
    assert isinstance(cfg, dict)
    assert cfg["seed"] == 999
    assert cfg["city_list"] == ["Delta", "Epsilon"]