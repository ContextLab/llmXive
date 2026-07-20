"""Unit tests for tensor validation logic in code/ingest/filter.py.

This module verifies the 6-component elastic tensor requirement (Constitution
Principle VI) and 2D material filtering logic.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Add the project root to the path to allow imports of sibling modules
# when running tests from the project root.
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.ingest.filter import is_valid_6_component_tensor, is_2d_material


class Test6ComponentTensorValidation:
    """Tests for is_valid_6_component_tensor function."""

    def test_valid_6_component_tensor(self):
        """Verify that a valid 6-component tensor passes validation."""
        valid = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        assert is_valid_6_component_tensor(valid) is True

    def test_invalid_length_tensor(self):
        """Verify that a tensor with incorrect length fails validation."""
        # Too short
        invalid_len_short = np.array([1.0, 2.0, 3.0])
        assert is_valid_6_component_tensor(invalid_len_short) is False

        # Too long
        invalid_len_long = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
        assert is_valid_6_component_tensor(invalid_len_long) is False

    def test_tensor_with_nan_values(self):
        """Verify that a tensor containing NaN values fails validation."""
        invalid_nan = np.array([1.0, np.nan, 3.0, 4.0, 5.0, 6.0])
        assert is_valid_6_component_tensor(invalid_nan) is False

    def test_tensor_with_inf_values(self):
        """Verify that a tensor containing Inf values fails validation."""
        invalid_inf = np.array([1.0, 2.0, 3.0, 4.0, 5.0, np.inf])
        assert is_valid_6_component_tensor(invalid_inf) is False

    def test_tensor_with_negative_inf_values(self):
        """Verify that a tensor containing -Inf values fails validation."""
        invalid_neg_inf = np.array([1.0, 2.0, 3.0, 4.0, 5.0, -np.inf])
        assert is_valid_6_component_tensor(invalid_neg_inf) is False

    def test_integer_array_input(self):
        """Verify that integer arrays are handled correctly."""
        valid_int = np.array([1, 2, 3, 4, 5, 6], dtype=int)
        assert is_valid_6_component_tensor(valid_int) is True

    def test_empty_array(self):
        """Verify that an empty array fails validation."""
        empty = np.array([])
        assert is_valid_6_component_tensor(empty) is False

    def test_single_element_array(self):
        """Verify that a single-element array fails validation."""
        single = np.array([1.0])
        assert is_valid_6_component_tensor(single) is False


class Test2DMaterialFilter:
    """Tests for is_2d_material function."""

    def test_valid_2d_material_with_vacuum(self):
        """Verify that a material with significant vacuum thickness is identified as 2D."""
        # Simulated data: has_vacuum=True, vacuum_thickness=15.0 Angstroms
        material_data = {
            "has_vacuum": True,
            "vacuum_thickness": 15.0,
            "formula": "MoS2"
        }
        assert is_2d_material(material_data) is True

    def test_insufficient_vacuum_thickness(self):
        """Verify that a material with insufficient vacuum is NOT identified as 2D."""
        # Threshold is typically 10 Angstroms
        material_data = {
            "has_vacuum": True,
            "vacuum_thickness": 5.0,
            "formula": "MoS2"
        }
        assert is_2d_material(material_data) is False

    def test_no_vacuum_flag(self):
        """Verify that a material without the vacuum flag is NOT identified as 2D."""
        material_data = {
            "has_vacuum": False,
            "vacuum_thickness": 0.0,
            "formula": "Si"
        }
        assert is_2d_material(material_data) is False

    def test_missing_vacuum_thickness_key(self):
        """Verify that missing vacuum_thickness key returns False."""
        material_data = {
            "has_vacuum": True,
            "formula": "MoS2"
        }
        assert is_2d_material(material_data) is False

    def test_missing_has_vacuum_key(self):
        """Verify that missing has_vacuum key returns False."""
        material_data = {
            "vacuum_thickness": 15.0,
            "formula": "MoS2"
        }
        assert is_2d_material(material_data) is False

    def test_exact_threshold_boundary(self):
        """Verify behavior exactly at the threshold (10.0 Angstroms)."""
        # Assuming the threshold check is >= 10.0
        material_data = {
            "has_vacuum": True,
            "vacuum_thickness": 10.0,
            "formula": "MoS2"
        }
        assert is_2d_material(material_data) is True

    def test_just_below_threshold(self):
        """Verify behavior just below the threshold (9.99 Angstroms)."""
        material_data = {
            "has_vacuum": True,
            "vacuum_thickness": 9.99,
            "formula": "MoS2"
        }
        assert is_2d_material(material_data) is False