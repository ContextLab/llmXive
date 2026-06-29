"""Unit tests for ``code/data/split_dataset.py``."""

from __future__ import annotations

import os
import pathlib

import pytest

# Import the module under test
from data.split_dataset import (
    DEFAULT_TRAIN_SPLIT,
    DEFAULT_TEST_SPLIT,
    TRAIN_SPLIT,
    TEST_SPLIT,
    get_split_proportions,
    document_split_proportions,
)

def test_default_proportions():
    """Verify that the defaults sum to 1 and match the documented values."""
    assert DEFAULT_TRAIN_SPLIT + DEFAULT_TEST_SPLIT == pytest.approx(1.0)
    assert DEFAULT_TRAIN_SPLIT == pytest.approx(0.70)
    assert DEFAULT_TEST_SPLIT == pytest.approx(0.30)

def test_env_override(monkeypatch):
    """Environment variables should override the defaults."""
    monkeypatch.setenv("TRAIN_SPLIT", "0.80")
    monkeypatch.setenv("TEST_SPLIT", "0.20")
    # Re‑import the module to pick up the new env vars
    import importlib

    import data.split_dataset as sd

    importlib.reload(sd)

    assert sd.TRAIN_SPLIT == pytest.approx(0.80)
    assert sd.TEST_SPLIT == pytest.approx(0.20)
    assert sd.TRAIN_SPLIT + sd.TEST_SPLIT == pytest.approx(1.0)

def test_documentation_file(tmp_path: pathlib.Path, monkeypatch):
    """The documentation function should create a markdown file with the correct content."""
    out_file = tmp_path / "my_split.md"
    # Ensure env vars are at defaults for deterministic content
    monkeypatch.delenv("TRAIN_SPLIT", raising=False)
    monkeypatch.delenv("TEST_SPLIT", raising=False)

    # Re‑import to reset constants
    import importlib

    import data.split_dataset as sd

    importlib.reload(sd)

    sd.document_split_proportions(output_path=out_file)

    assert out_file.is_file()
    text = out_file.read_text(encoding="utf-8")
    assert "Training set" in text and "Testing set" in text
    assert "70%" in text and "30%" in text