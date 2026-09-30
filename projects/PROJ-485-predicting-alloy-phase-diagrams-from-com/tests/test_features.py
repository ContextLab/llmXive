"""
Tests for feature generation and validation.
T011: Independent test for US-1 verifying descriptor deviation <= 1% from elemental properties.
"""
import os
import sys
import csv
import json
import tempfile
import shutil
import pandas as pd
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from features.generate_descriptors import (
    load_elemental_properties,
    calculate_mean_atomic_radius,
    calculate_electronegativity_variance,
    calculate_valence_electron_count,
    calculate_hume_rothery_concentration,
    generate_descriptors,
    validate_descriptors,
    process_alloy_dataset
)
from utils.error_codes import ErrorCode

class TestDescriptorValidation:
    """Tests for descriptor validation logic (T018)."""

    def test_validate_descriptors_success(self):
        """Test that valid descriptors pass validation."""
        # Setup props
        props = {
            'Cu': {'atomic_radius': 1.28, 'electronegativity': 1.90, 'valence_electrons': 1},
            'Zn': {'atomic_radius': 1.34, 'electronegativity': 1.65, 'valence_electrons': 2}
        }
        
        # Generate a valid descriptor
        row = {'system_id': 'Cu-Zn-01', 'element_a': 'Cu', 'element_b': 'Zn', 'composition': 0.5, 'temperature': 1000}
        desc = generate_descriptors(row, props)
        
        # Validate
        assert validate_descriptors([desc], props) is True

    def test_validate_descriptors_missing_element(self):
        """Test that descriptors with missing elements fail validation."""
        props = {
            'Cu': {'atomic_radius': 1.28, 'electronegativity': 1.90, 'valence_electrons': 1}
        }
        
        row = {'system_id': 'Cu-X-01', 'element_a': 'Cu', 'element_b': 'Unknown', 'composition': 0.5, 'temperature': 1000}
        desc = generate_descriptors(row, props)
        
        assert validate_descriptors([desc], props) is False

    def test_validate_descriptors_calculation_error(self):
        """Test that descriptors with incorrect calculations fail validation."""
        props = {
            'Cu': {'atomic_radius': 1.28, 'electronegativity': 1.90, 'valence_electrons': 1},
            'Zn': {'atomic_radius': 1.34, 'electronegativity': 1.65, 'valence_electrons': 2}
        }
        
        # Generate valid descriptor then corrupt it
        row = {'system_id': 'Cu-Zn-01', 'element_a': 'Cu', 'element_b': 'Zn', 'composition': 0.5, 'temperature': 1000}
        desc = generate_descriptors(row, props)
        
        # Corrupt mean_atomic_radius
        desc['mean_atomic_radius'] = 999.0
        
        assert validate_descriptors([desc], props) is False

class TestDescriptorGeneration:
    """Tests for descriptor calculation logic."""

    def test_mean_atomic_radius_calculation(self):
        """Test mean atomic radius calculation."""
        props = {
            'A': {'atomic_radius': 1.0, 'electronegativity': 1.0, 'valence_electrons': 1},
            'B': {'atomic_radius': 2.0, 'electronegativity': 1.0, 'valence_electrons': 1}
        }
        
        # 50-50 mix
        result = calculate_mean_atomic_radius(0.5, 'A', 'B', props)
        assert abs(result - 1.5) < 1e-6

    def test_electronegativity_variance_calculation(self):
        """Test electronegativity variance calculation."""
        props = {
            'A': {'atomic_radius': 1.0, 'electronegativity': 1.0, 'valence_electrons': 1},
            'B': {'atomic_radius': 2.0, 'electronegativity': 3.0, 'valence_electrons': 1}
        }
        
        # 50-50 mix: mean = 2.0
        # Var = (1-2)^2 * 0.5 + (3-2)^2 * 0.5 = 1 * 0.5 + 1 * 0.5 = 1.0
        result = calculate_electronegativity_variance(0.5, 'A', 'B', props)
        assert abs(result - 1.0) < 1e-6

    def test_valence_electron_count_calculation(self):
        """Test valence electron count calculation."""
        props = {
            'A': {'atomic_radius': 1.0, 'electronegativity': 1.0, 'valence_electrons': 1},
            'B': {'atomic_radius': 2.0, 'electronegativity': 1.0, 'valence_electrons': 3}
        }
        
        # 50-50 mix: (1*0.5) + (3*0.5) = 2.0
        result = calculate_valence_electron_count(0.5, 'A', 'B', props)
        assert abs(result - 2.0) < 1e-6

    def test_hume_rothery_concentration_calculation(self):
        """Test Hume-Rothery concentration calculation."""
        props = {
            'A': {'atomic_radius': 1.0, 'electronegativity': 1.0, 'valence_electrons': 1},
            'B': {'atomic_radius': 2.0, 'electronegativity': 1.0, 'valence_electrons': 1}
        }
        
        # diff = |1 - 2| / ((1 + 2) / 2) = 1 / 1.5 = 0.666...
        result = calculate_hume_rothery_concentration(0.5, 'A', 'B', props)
        assert abs(result - (1.0 / 1.5)) < 1e-6

class TestDescriptorDeviation:
    """
    T011: Independent test for US-1.
    Asserts derived values deviate <= 1% from data/raw/elemental_properties.csv.
    """

    def test_descriptor_deviation(self):
        """
        Assert derived values deviate <= 1% from data/raw/elemental_properties.csv.
        This test loads the real elemental properties file, generates descriptors
        for known compositions, and verifies the calculated descriptors match
        the expected values derived from the source properties within 1% tolerance.
        """
        # Path to the real data file (T007)
        props_path = os.path.join(project_root, 'data', 'raw', 'elemental_properties.csv')
        
        if not os.path.exists(props_path):
            pytest.fail(f"Real data file not found: {props_path}. T007 must be completed.")

        # Load real properties
        props = load_elemental_properties(props_path)
        
        # Verify we have the expected elements
        required_elements = ['Cu', 'Al', 'Zn', 'Fe', 'C']
        for elem in required_elements:
            if elem not in props:
                pytest.fail(f"Required element {elem} missing from {props_path}")

        # Test Case 1: Cu-Zn Binary (50-50)
        # Expected Mean Radius = (r_Cu + r_Zn) / 2
        # Expected EN Variance = ((EN_Cu - mean_EN)^2 + (EN_Zn - mean_EN)^2) / 2
        # Expected VEC = (v_Cu + v_Zn) / 2
        
        cu_props = props['Cu']
        zn_props = props['Zn']
        
        expected_mean_radius = (cu_props['atomic_radius_angstrom'] + zn_props['atomic_radius_angstrom']) / 2.0
        expected_en_mean = (cu_props['electronegativity_pauling'] + zn_props['electronegativity_pauling']) / 2.0
        expected_en_var = (
            ((cu_props['electronegativity_pauling'] - expected_en_mean) ** 2) +
            ((zn_props['electronegativity_pauling'] - expected_en_mean) ** 2)
        ) / 2.0
        expected_vec = (cu_props['valence_electrons'] + zn_props['valence_electrons']) / 2.0

        # Generate descriptor for 50-50 Cu-Zn
        row = {
            'system_id': 'Cu-Zn-Test',
            'element_a': 'Cu',
            'element_b': 'Zn',
            'composition': 0.5,
            'temperature': 1000.0
        }
        desc = generate_descriptors(row, props)

        # Assertions with 1% tolerance
        tolerance = 0.01 # 1%

        # Check Mean Atomic Radius
        actual_radius = desc['mean_atomic_radius']
        assert abs(actual_radius - expected_mean_radius) <= expected_mean_radius * tolerance, \
            f"Mean atomic radius deviation > 1%: expected {expected_mean_radius}, got {actual_radius}"

        # Check Electronegativity Variance
        actual_en_var = desc['electronegativity_variance']
        assert abs(actual_en_var - expected_en_var) <= expected_en_var * tolerance, \
            f"Electronegativity variance deviation > 1%: expected {expected_en_var}, got {actual_en_var}"

        # Check Valence Electron Count
        actual_vec = desc['valence_electron_count']
        assert abs(actual_vec - expected_vec) <= expected_vec * tolerance, \
            f"Valence electron count deviation > 1%: expected {expected_vec}, got {actual_vec}"

        # Test Case 2: Al-Cu Binary (30-70)
        al_props = props['Al']
        cu_props = props['Cu']
        comp_a = 0.3 # Al
        comp_b = 0.7 # Cu

        expected_mean_radius_2 = (al_props['atomic_radius_angstrom'] * comp_a) + (cu_props['atomic_radius_angstrom'] * comp_b)
        expected_en_mean_2 = (al_props['electronegativity_pauling'] * comp_a) + (cu_props['electronegativity_pauling'] * comp_b)
        expected_en_var_2 = (
            ((al_props['electronegativity_pauling'] - expected_en_mean_2) ** 2) * comp_a +
            ((cu_props['electronegativity_pauling'] - expected_en_mean_2) ** 2) * comp_b
        )
        expected_vec_2 = (al_props['valence_electrons'] * comp_a) + (cu_props['valence_electrons'] * comp_b)

        row_2 = {
            'system_id': 'Al-Cu-Test',
            'element_a': 'Al',
            'element_b': 'Cu',
            'composition': comp_a, # Composition of element_a
            'temperature': 900.0
        }
        desc_2 = generate_descriptors(row_2, props)

        # Assertions with 1% tolerance
        actual_radius_2 = desc_2['mean_atomic_radius']
        assert abs(actual_radius_2 - expected_mean_radius_2) <= expected_mean_radius_2 * tolerance, \
            f"Al-Cu Mean atomic radius deviation > 1%: expected {expected_mean_radius_2}, got {actual_radius_2}"

        actual_en_var_2 = desc_2['electronegativity_variance']
        # Handle case where variance might be very small (close to 0)
        if expected_en_var_2 > 1e-6:
            assert abs(actual_en_var_2 - expected_en_var_2) <= expected_en_var_2 * tolerance, \
                f"Al-Cu Electronegativity variance deviation > 1%: expected {expected_en_var_2}, got {actual_en_var_2}"
        else:
            assert abs(actual_en_var_2 - expected_en_var_2) < 1e-6, \
                f"Al-Cu Electronegativity variance deviation too large: expected {expected_en_var_2}, got {actual_en_var_2}"

        actual_vec_2 = desc_2['valence_electron_count']
        assert abs(actual_vec_2 - expected_vec_2) <= expected_vec_2 * tolerance, \
            f"Al-Cu Valence electron count deviation > 1%: expected {expected_vec_2}, got {actual_vec_2}"