"""Reproducibility tests for code/utils/seed.py."""

import random
import sys
from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from utils.seed import set_seed  # noqa: E402


def _draw():
    py_vals = [random.random() for _ in range(5)]
    np_vals = np.random.rand(5).tolist()
    return py_vals, np_vals


def test_set_seed_is_reproducible():
    set_seed(42)
    first = _draw()
    set_seed(42)
    second = _draw()
    assert first == second


def test_set_seed_changes_state():
    set_seed(42)
    a = _draw()
    b = _draw()
    assert a != b


def test_different_seeds_differ():
    set_seed(42)
    a = _draw()
    set_seed(7)
    b = _draw()
    assert a != b


def test_set_seed_sets_pythonhashseed(monkeypatch):
    monkeypatch.delenv("PYTHONHASHSEED", raising=False)
    set_seed(123)
    import os

    assert os.environ["PYTHONHASHSEED"] == "123"
