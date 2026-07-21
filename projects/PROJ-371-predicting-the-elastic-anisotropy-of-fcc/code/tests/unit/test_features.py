"""
Unit tests for feature engineering module.
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

from src.data.features import get_element_properties, compute_compositional_features, _get_valence_electrons
from src.utils.logging import setup_logger

logger = setup_logger("test_features")

class TestGetElementProperties:
    def test_valid_element(self):
        props = get_element_properties("Fe")
        assert "radius" in props
        assert "electronegativity" in props
        assert "valence_electrons" in props
        assert props["radius"] > 0
        assert props["electronegativity"] > 0
        assert props["valence_electrons"] > 0

    def test_invalid_element(self):
        with pytest.raises(ValueError):
            get_element_properties("XyZ")

    def test_case_insensitivity(self):
        props_lower = get_element_properties("fe")
        props_upper = get_element_properties("FE")
        assert props_lower["radius"] == props_upper["radius"]

class TestComputeCompositionalFeatures:
    def test_simple_binary_alloy(self):
        data = {
            "composition": [["Fe", "Ni"]],
            "atomic_fractions": [[0.5, 0.5]]
        }
        df = pd.DataFrame(data)
        features = compute_compositional_features(df)
        
        assert "radius_variance" in features.columns
        assert "electronegativity_std" in features.columns
        assert "vec" in features.columns
        assert len(features) == 1
        
        # Check that variance is non-negative
        assert features["radius_variance"].iloc[0] >= 0
        assert features["electronegativity_std"].iloc[0] >= 0

    def test_empty_input(self):
        data = {
            "composition": [],
            "atomic_fractions": []
        }
        df = pd.DataFrame(data)
        features = compute_compositional_features(df)
        
        assert len(features) == 0
        assert "radius_variance" in features.columns

    def test_mismatched_lengths(self, caplog):
        data = {
            "composition": [["Fe", "Ni"]],
            "atomic_fractions": [[0.5]]
        }
        df = pd.DataFrame(data)
        features = compute_compositional_features(df)
        
        assert len(features) == 0  # Should be skipped

    def test_invalid_element_in_list(self, caplog):
        data = {
            "composition": [["Fe", "XyZ"]],
            "atomic_fractions": [[0.5, 0.5]]
        }
        df = pd.DataFrame(data)
        features = compute_compositional_features(df)
        
        # Should process with just Fe
        assert len(features) == 1
        assert "radius_variance" in features.columns

    def test_zero_fractions(self):
        data = {
            "composition": [["Fe", "Ni"]],
            "atomic_fractions": [[0.0, 0.0]]
        }
        df = pd.DataFrame(data)
        features = compute_compositional_features(df)
        
        assert len(features) == 0  # Skipped due to zero total

class TestValenceElectrons:
    def test_transition_metals(self):
        # Fe (group 8) -> 8
        assert _get_valence_electrons("Fe") == 8
        # Ni (group 10) -> 10
        assert _get_valence_electrons("Ni") == 10
        # Cu (group 11) -> 11
        assert _get_valence_electrons("Cu") == 11
        # Zn (group 12) -> 2
        assert _get_valence_electrons("Zn") == 2

    def test_main_group(self):
        # Al (group 13) -> 3
        assert _get_valence_electrons("Al") == 3
        # Si (group 14) -> 4
        assert _get_valence_electrons("Si") == 4
        # Na (group 1) -> 1
        assert _get_valence_electrons("Na") == 1

class TestFeaturesIntegration:
    def test_full_pipeline(self):
        # Create a realistic input
        data = {
            "id": ["test-1"],
            "composition": [["Fe", "Ni", "Cr"]],
            "atomic_fractions": [[0.33, 0.33, 0.34]],
            "C11": [200],
            "C12": [100],
            "C44": [80]
        }
        df = pd.DataFrame(data)
        features = compute_compositional_features(df)
        
        assert len(features) == 1
        assert features["radius_variance"].iloc[0] > 0
        assert features["electronegativity_std"].iloc[0] > 0
        assert features["vec"].iloc[0] > 0