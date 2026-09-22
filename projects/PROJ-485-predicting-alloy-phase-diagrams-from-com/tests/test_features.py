"""
Test suite for feature generation functions in code/features/generate_descriptors.py.
Specifically tests the deviation of derived values against the source elemental properties.
"""
import os
import sys
import unittest
import csv
import math
from pathlib import Path

# Add the project root to the path to allow imports from code/
# Assuming tests are at tests/test_features.py and code is at code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from features.generate_descriptors import (
    load_elemental_properties,
    calculate_mean_atomic_radius,
    calculate_electronegativity_variance,
    calculate_valence_electron_count,
    calculate_hume_rothery_concentration
)
from utils.error_codes import ErrorCode

# Constants for test tolerance
DEVIATION_THRESHOLD = 0.01  # 1%

class TestDescriptorDeviation(unittest.TestCase):
    """
    Test that derived values deviate <= 1% from data/raw/elemental_properties.csv.
    """

    @classmethod
    def setUpClass(cls):
        """Load the elemental properties once for all tests."""
        cls.properties_path = project_root / "data" / "raw" / "elemental_properties.csv"
        if not cls.properties_path.exists():
            raise FileNotFoundError(
                f"Required data file not found: {cls.properties_path}. "
                "Ensure T006 has been completed to seed elemental_properties.csv."
            )
        cls.elemental_props = load_elemental_properties(str(cls.properties_path))

    def test_load_elemental_properties_valid(self):
        """Verify that the properties are loaded correctly as a dictionary."""
        self.assertIsInstance(self.elemental_props, dict)
        self.assertGreater(len(self.elemental_props), 0, "Elemental properties file is empty.")
        
        # Check expected keys for a known element (e.g., Cu from T006)
        if "Cu" in self.elemental_props:
            self.assertIn("atomic_radius_angstrom", self.elemental_props["Cu"])
            self.assertIn("electronegativity_pauling", self.elemental_props["Cu"])
            self.assertIn("valence_electrons", self.elemental_props["Cu"])

    def test_descriptor_deviation_mean_atomic_radius(self):
        """
        Test that calculate_mean_atomic_radius returns values within 1% of the source data.
        For a single element alloy, the mean should be exactly the element's radius.
        """
        # Test with a single element (Cu) - effectively a pure metal case for the mean
        # In a real alloy, this would be a weighted mean, but for 100% Cu, it's just Cu's radius.
        composition = {"Cu": 1.0}
        expected_radius = self.elemental_props["Cu"]["atomic_radius_angstrom"]
        calculated_radius = calculate_mean_atomic_radius(composition, self.elemental_props)

        deviation = abs(calculated_radius - expected_radius) / expected_radius
        self.assertLessEqual(
            deviation,
            DEVIATION_THRESHOLD,
            f"Mean atomic radius deviation {deviation:.4f} exceeds 1% threshold."
        )

    def test_descriptor_deviation_electronegativity_variance(self):
        """
        Test that calculate_electronegativity_variance is consistent with source data.
        For a single element, variance should be 0.
        """
        composition = {"Al": 1.0}
        # For a single element, variance is 0
        calculated_variance = calculate_electronegativity_variance(composition, self.elemental_props)
        
        self.assertAlmostEqual(
            calculated_variance,
            0.0,
            places=6,
            msg="Variance for a single element should be 0."
        )

        # Test with a binary alloy (Cu-Zn) to ensure calculation logic holds
        # Mean EN = (EN_Cu * 0.5) + (EN_Zn * 0.5)
        # Var = 0.5 * (EN_Cu - Mean)^2 + 0.5 * (EN_Zn - Mean)^2
        composition_binary = {"Cu": 0.5, "Zn": 0.5}
        calculated_variance_binary = calculate_electronegativity_variance(composition_binary, self.elemental_props)
        
        # We expect a positive variance here, just verifying it calculates without error
        # and uses the loaded properties correctly.
        self.assertGreater(calculated_variance_binary, 0, "Binary alloy variance should be > 0.")

    def test_descriptor_deviation_valence_electron_count(self):
        """
        Test that calculate_valence_electron_count matches source data within tolerance.
        """
        composition = {"Fe": 1.0}
        expected_valence = self.elemental_props["Fe"]["valence_electrons"]
        calculated_valence = calculate_valence_electron_count(composition, self.elemental_props)

        # Valence electrons are usually integers, but let's check relative difference
        if expected_valence != 0:
            deviation = abs(calculated_valence - expected_valence) / expected_valence
            self.assertLessEqual(
                deviation,
                DEVIATION_THRESHOLD,
                f"Valence electron count deviation {deviation:.4f} exceeds 1% threshold."
            )
        else:
            self.assertEqual(calculated_valence, 0, "Valence count should be 0 if expected is 0.")

    def test_descriptor_deviation_hume_rothery_concentration(self):
        """
        Test that calculate_hume_rothery_concentration uses correct source values.
        This function typically checks if concentration is within specific ranges (e.g., 14-15 for FCC).
        We verify the calculation uses the loaded valence electrons correctly.
        """
        # Cu-Zn (Brass) is a classic Hume-Rothery system.
        # e/a ratio = sum(x_i * v_i)
        composition = {"Cu": 0.6, "Zn": 0.4}
        
        # Calculate expected manually to verify
        v_Cu = self.elemental_props["Cu"]["valence_electrons"]
        v_Zn = self.elemental_props["Zn"]["valence_electrons"]
        expected_e_a = (0.6 * v_Cu) + (0.4 * v_Zn)
        
        calculated_e_a = calculate_hume_rothery_concentration(composition, self.elemental_props)
        
        deviation = abs(calculated_e_a - expected_e_a) / expected_e_a
        self.assertLessEqual(
            deviation,
            DEVIATION_THRESHOLD,
            f"Hume-Rothery concentration (e/a) deviation {deviation:.4f} exceeds 1% threshold."
        )

    def test_missing_element_raises_error(self):
        """
        Test that the functions handle missing elements in the composition 
        by raising an appropriate error or handling it gracefully (depending on implementation).
        Given the requirement to fail loudly on missing data, we expect an exception.
        """
        composition = {"FakeElement": 1.0}
        
        # We expect KeyError or ValueError from load_elemental_properties or the calculation functions
        # if the element is not in the loaded CSV.
        with self.assertRaises((KeyError, ValueError)):
            calculate_mean_atomic_radius(composition, self.elemental_props)

if __name__ == "__main__":
    unittest.main()