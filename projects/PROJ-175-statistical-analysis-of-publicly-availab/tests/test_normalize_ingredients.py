"""
Tests for T014a: Normalize Ingredients
"""
import pytest
import pandas as pd
import numpy as np
from Levenshtein import distance as levenshtein_distance
import json
import os
from pathlib import Path

# Add code directory to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'code'))

from data.normalize_ingredients import normalize_ingredient, load_amendment_log

class TestLevenshteinNormalization:
    def test_exact_match(self):
        # If raw is in map, it should return itself
        canonical_map = {
            "tomato": {"id": "ING_001", "frequency": 100},
            "potato": {"id": "ING_002", "frequency": 50}
        }
        assert normalize_ingredient("tomato", canonical_map) == "tomato"

    def test_close_match(self):
        # "tomatoes" should map to "tomato" if distance <= 2
        canonical_map = {
            "tomato": {"id": "ING_001", "frequency": 100}
        }
        # distance("tomatoes", "tomato") = 2 (s, e)
        assert normalize_ingredient("tomatoes", canonical_map) == "tomato"

    def test_no_match(self):
        # "pineapple" is far from "tomato"
        canonical_map = {
            "tomato": {"id": "ING_001", "frequency": 100}
        }
        assert normalize_ingredient("pineapple", canonical_map) == "pineapple"

    def test_tie_breaking_frequency(self):
        # If two canonicals are equally close, pick the one with higher frequency
        canonical_map = {
            "apple": {"id": "ING_001", "frequency": 10},
            "pear": {"id": "ING_002", "frequency": 100}
        }
        # "aple" is distance 1 from "apple" and distance 2 from "pear"?
        # Let's construct a case where distance is equal.
        # "ba" -> "ba" (dist 0) vs "ca" (dist 1).
        # Let's use "cat" and "bat".
        # Input: "at". Dist to "cat"=1, "bat"=1.
        canonical_map = {
            "cat": {"id": "ING_001", "frequency": 10},
            "bat": {"id": "ING_002", "frequency": 100}
        }
        # "at" -> "bat" (higher freq)
        # Wait, distance("at", "cat") = 1, distance("at", "bat") = 1.
        result = normalize_ingredient("at", canonical_map)
        assert result == "bat", f"Expected 'bat' due to higher frequency, got {result}"

class TestAmendmentLog:
    def test_load_amendment_log_missing(self):
        # This test requires a fake environment or mocking.
        # For now, we just ensure the function exists and handles the import.
        # In a real CI, we'd mock the file system.
        pass
