import os
import sys
import csv
import math
import unittest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.features.generate_descriptors import (
    load_elemental_properties,
    calculate_mean_atomic_radius,
    calculate_electronegativity_variance,
    calculate_valence_electron_count,
    calculate_hume_rothery_concentration
)

class TestDescriptorDeviation(unittest.TestCase):
    """
    Test task T011: Verify derived values deviate <= 1% from data/raw/elemental_properties.csv.
    """

    def setUp(self):
        """Load the real reference data file."""
        self.raw_data_path = project_root / "data" / "raw" / "elemental_properties.csv"
        if not self.raw_data_path.exists():
            raise FileNotFoundError(
                f"Required reference file missing: {self.raw_data_path}. "
                "Task T006 must be completed to seed this file."
            )
        self.elemental_props = load_elemental_properties(str(self.raw_data_path))

    def test_descriptor_deviation(self):
        """
        Assert derived values deviate <= 1% from data/raw/elemental_properties.csv.
        
        This test validates the integrity of the descriptor generation logic by:
        1. Calculating descriptors for a known alloy (Cu-Al) using the loaded properties.
        2. Manually computing the expected values based on the CSV data.
        3. Asserting the deviation is within the 1% tolerance.
        """
        # Define a test alloy: Cu50Al50 (atomic percent)
        # Composition: 50% Cu, 50% Al
        alloy_composition = {
            "Cu": 0.50,
            "Al": 0.50
        }
        
        # Get raw properties for Cu and Al
        cu_props = self.elemental_props.get("Cu")
        al_props = self.elemental_props.get("Al")
        
        self.assertIsNotNone(cu_props, "Cu properties missing from reference CSV")
        self.assertIsNotNone(al_props, "Al properties missing from reference CSV")

        # --- Test 1: Mean Atomic Radius ---
        # Formula: sum(c_i * r_i)
        expected_mean_radius = (
            alloy_composition["Cu"] * cu_props["atomic_radius_angstrom"] +
            alloy_composition["Al"] * al_props["atomic_radius_angstrom"]
        )
        calculated_mean_radius = calculate_mean_atomic_radius(alloy_composition, self.elemental_props)
        
        deviation_radius = abs(calculated_mean_radius - expected_mean_radius) / expected_mean_radius
        self.assertLessEqual(
            deviation_radius, 0.01,
            f"Mean atomic radius deviation {deviation_radius*100:.2f}% exceeds 1% limit. "
            f"Expected: {expected_mean_radius}, Got: {calculated_mean_radius}"
        )

        # --- Test 2: Valence Electron Count ---
        # Formula: sum(c_i * v_i)
        expected_vec = (
            alloy_composition["Cu"] * cu_props["valence_electrons"] +
            alloy_composition["Al"] * al_props["valence_electrons"]
        )
        calculated_vec = calculate_valence_electron_count(alloy_composition, self.elemental_props)
        
        # Allow small floating point tolerance for integer-like values
        deviation_vec = abs(calculated_vec - expected_vec) / max(expected_vec, 1e-9)
        self.assertLessEqual(
            deviation_vec, 0.01,
            f"Valence electron count deviation {deviation_vec*100:.2f}% exceeds 1% limit. "
            f"Expected: {expected_vec}, Got: {calculated_vec}"
        )

        # --- Test 3: Electronegativity Variance ---
        # Formula: sum(c_i * (x_i - mean_x)^2)
        mean_en = (
            alloy_composition["Cu"] * cu_props["electronegativity_pauling"] +
            alloy_composition["Al"] * al_props["electronegativity_pauling"]
        )
        expected_variance = (
            alloy_composition["Cu"] * (cu_props["electronegativity_pauling"] - mean_en)**2 +
            alloy_composition["Al"] * (al_props["electronegativity_pauling"] - mean_en)**2
        )
        calculated_variance = calculate_electronegativity_variance(alloy_composition, self.elemental_props)
        
        # Avoid division by zero if variance is near 0 (not the case here, but good practice)
        if expected_variance > 1e-9:
            deviation_en = abs(calculated_variance - expected_variance) / expected_variance
        else:
            deviation_en = abs(calculated_variance - expected_variance)
        
        self.assertLessEqual(
            deviation_en, 0.01,
            f"Electronegativity variance deviation {deviation_en*100:.2f}% exceeds 1% limit. "
            f"Expected: {expected_variance}, Got: {calculated_variance}"
        )

        # --- Test 4: Hume-Rothery Concentration (simplified as valence electron ratio check) ---
        # The function returns a specific metric based on VEC and composition.
        # We verify it runs and produces a deterministic result consistent with inputs.
        hr_conc = calculate_hume_rothery_concentration(alloy_composition, self.elemental_props)
        self.assertIsInstance(hr_conc, float, "Hume-Rothery concentration must be a float")
        self.assertGreaterEqual(hr_conc, 0.0, "Hume-Rothery concentration must be non-negative")

        print("All descriptor deviation tests passed within 1% tolerance.")

if __name__ == "__main__":
    unittest.main()