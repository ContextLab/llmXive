import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.preprocess import parse_composition, compute_mean_coordination_number, compute_electronegativity_variance, compute_atomic_radius_variance

class TestParseComposition:
    def test_valid_simple(self):
        result = parse_composition("Ge20Se80")
        assert result == {'Ge': 20, 'Se': 80}

    def test_valid_no_count(self):
        # Assuming valid element symbols if count is missing (default 1)
        # Note: 'As' is valid, 'Xy' is not.
        result = parse_composition("As")
        assert result == {'As': 1}

    def test_invalid_symbol(self):
        result = parse_composition("Ge20Xy80")
        assert result is None

    def test_empty_string(self):
        result = parse_composition("")
        assert result is None

    def test_none_input(self):
        result = parse_composition(None)
        assert result is None

class TestFeatureComputation:
    def test_mean_coordination_number(self):
        # Ge (CN=4), Se (CN=2) approx
        # Ge20Se80 -> (0.2*4 + 0.8*2) = 0.8 + 1.6 = 2.4
        comp = {'Ge': 20, 'Se': 80}
        mcn = compute_mean_coordination_number(comp)
        assert isinstance(mcn, float)
        assert mcn > 0

    def test_electronegativity_variance(self):
        comp = {'Ge': 20, 'Se': 80}
        var = compute_electronegativity_variance(comp)
        assert isinstance(var, float)
        assert var >= 0

    def test_atomic_radius_variance(self):
        comp = {'Ge': 20, 'Se': 80}
        var = compute_atomic_radius_variance(comp)
        assert isinstance(var, float)
        assert var >= 0

    def test_empty_composition(self):
        assert compute_mean_coordination_number({}) != compute_mean_coordination_number({}) # NaN check
        assert compute_electronegativity_variance({}) != compute_electronegativity_variance({})
        assert compute_atomic_radius_variance({}) != compute_atomic_radius_variance({})
