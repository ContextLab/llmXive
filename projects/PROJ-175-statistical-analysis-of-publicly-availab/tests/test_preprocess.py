import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.preprocess import levenshtein_distance, normalize_ingredient_name, build_canonical_map

def test_levenshtein_distance():
    """Test the Levenshtein distance function."""
    assert levenshtein_distance("cat", "cat") == 0
    assert levenshtein_distance("cat", "bat") == 1
    assert levenshtein_distance("cat", "car") == 1
    assert levenshtein_distance("cat", "cart") == 1
    assert levenshtein_distance("cat", "dog") == 3
    assert levenshtein_distance("ingredient", "ingredent") == 1

def test_normalize_ingredient_name_exact_match():
    """Test normalization with exact match."""
    canonical_map = {"salt": "Salt", "sugar": "Sugar"}
    result, excluded = normalize_ingredient_name("Salt", canonical_map)
    assert result == "Salt"
    assert not excluded

def test_normalize_ingredient_name_close_match():
    """Test normalization with close match (Levenshtein <= 2)."""
    canonical_map = {"salt": "Salt"}
    result, excluded = normalize_ingredient_name("solt", canonical_map)
    assert result == "Salt"
    assert not excluded

def test_normalize_ingredient_name_excluded():
    """Test normalization with no close match."""
    canonical_map = {"salt": "Salt"}
    result, excluded = normalize_ingredient_name("xyz", canonical_map)
    assert excluded
    assert result == "xyz"  # Returns cleaned version

def test_normalize_ingredient_name_case_insensitive():
    """Test case insensitivity."""
    canonical_map = {"salt": "Salt"}
    result, excluded = normalize_ingredient_name("SALT", canonical_map)
    assert result == "Salt"
    assert not excluded

def test_normalize_ingredient_name_special_chars():
    """Test handling of special characters."""
    canonical_map = {"salt": "Salt"}
    result, excluded = normalize_ingredient_name("salt!", canonical_map)
    assert result == "Salt"
    assert not excluded

def test_build_canonical_map_empty():
    """Test canonical map building with no data."""
    # This test assumes no input file exists in a clean environment
    # We can't easily test the file reading part without mocking
    # So we just test that it returns a dict
    canonical_map = build_canonical_map()
    assert isinstance(canonical_map, dict)

def test_normalize_ingredient_name_non_string():
    """Test handling of non-string input."""
    canonical_map = {"salt": "Salt"}
    result, excluded = normalize_ingredient_name(123, canonical_map)
    assert excluded
    assert result == "123"
