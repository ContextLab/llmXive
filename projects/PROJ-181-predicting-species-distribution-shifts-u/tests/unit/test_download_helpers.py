"""
Unit tests for helper functions in ``code/download.py``.
These tests ensure that the internal utilities behave as expected
without performing any network I/O.
"""

import datetime
from pathlib import Path

import pytest

# Import the functions directly from the module under test
from download import _year_in_range, _load_species_list

def test_year_in_range_true():
    assert _year_in_range("1995-06-12", 1990, 2000) is True

def test_year_in_range_false():
    assert _year_in_range("1985-01-01", 1990, 2000) is False

def test_year_in_range_invalid():
    # Empty or malformed dates should return False, not raise
    assert _year_in_range("", 1990, 2000) is False
    assert _year_in_range("not-a-date", 1990, 2000) is False

def test_load_species_list_from_config(tmp_path, monkeypatch):
    """
    Verify that when ``file_path`` is None the function falls back to
    ``config.SPECIES_LIST``.
    """
    # Ensure the config module is importable and contains SPECIES_LIST
    import config

    # Monkey‑patch the list to a known value
    monkeypatch.setattr(config, "SPECIES_LIST", ["Test species A", "Test species B"])
    result = _load_species_list(None)
    assert result == ["Test species A", "Test species B"]

def test_load_species_list_from_file(tmp_path):
    # Create a temporary species list file
    file_path = tmp_path / "species.txt"
    file_path.write_text("Species One\nSpecies Two\n\nSpecies Three\n")
    result = _load_species_list(file_path)
    assert result == ["Species One", "Species Two", "Species Three"]