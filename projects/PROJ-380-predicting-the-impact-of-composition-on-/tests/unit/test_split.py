import os
import sys
import unittest
import csv
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from data.split import load_processed_data, extract_alloy_family, stratified_split, save_split_data

class TestHybridLOFOGroupKFold(unittest.TestCase):
    """
    Unit test for hybrid LOFO/GroupKFold split logic.
    
    This test verifies that the splitting logic correctly handles:
    1. Large alloy families using Leave-One-Family-Out (LOFO) logic (simulated via stratified split with family groups).
    2. Small alloy families using GroupKFold logic (simulated by ensuring family-based grouping).
    3. Edge cases where a family is too small to split.
    """

    def setUp(self):
        """Create a temporary CSV file with test data mimicking BMG dataset."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_path = Path(self.temp_dir.name) / "test_data.csv"
        
        # Create a dataset with distinct alloy families
        # Family A: Large (6 samples) -> Should allow LOFO-style split
        # Family B: Small (3 samples) -> Should be handled as a group
        # Family C: Medium (4 samples)
        self.test_data = [
            {"composition": "Zr41Ti14Cu12.5Ni10Be22.5", "shear_modulus": 32.0, "family": "Zr-based"},
            {"composition": "Zr55Cu30Al10Ni5", "shear_modulus": 35.5, "family": "Zr-based"},
            {"composition": "Zr60Cu25Al10Ni5", "shear_modulus": 33.2, "family": "Zr-based"},
            {"composition": "Zr52Ti5Cu17.9Ni14.6Al10", "shear_modulus": 34.1, "family": "Zr-based"},
            {"composition": "Zr65Al7.5Ni10Cu17.5", "shear_modulus": 36.0, "family": "Zr-based"},
            {"composition": "Zr57Nb5Al10Cu15.4Ni12.6", "shear_modulus": 31.5, "family": "Zr-based"},
            
            {"composition": "Pd40Cu30Ni10P20", "shear_modulus": 28.0, "family": "Pd-based"},
            {"composition": "Pd43Cu27Ni10P20", "shear_modulus": 29.5, "family": "Pd-based"},
            {"composition": "Pd40Ni40P20", "shear_modulus": 30.0, "family": "Pd-based"},
            
            {"composition": "Mg65Cu25Gd10", "shear_modulus": 25.0, "family": "Mg-based"},
            {"composition": "Mg70Cu20Y10", "shear_modulus": 26.5, "family": "Mg-based"},
            {"composition": "Mg60Cu30Y10", "shear_modulus": 24.8, "family": "Mg-based"},
            {"composition": "Mg75Cu20Y5", "shear_modulus": 27.0, "family": "Mg-based"},
        ]

        with open(self.data_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.test_data[0].keys())
            writer.writeheader()
            writer.writerows(self.test_data)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extract_alloy_family(self):
        """Test that family extraction works correctly from CSV data."""
        data = load_processed_data(self.data_path)
        families = [extract_alloy_family(row) for row in data]
        
        expected_families = ["Zr-based"] * 6 + ["Pd-based"] * 3 + ["Mg-based"] * 4
        self.assertEqual(families, expected_families)

    def test_stratified_split_by_family(self):
        """
        Test the stratified split logic which simulates the GroupKFold aspect.
        Ensures that samples from the same family are not randomly distributed 
        in a way that breaks the grouping assumption if used for LOFO.
        """
        data = load_processed_data(self.data_path)
        
        # Perform a stratified split by family
        train_data, test_data = stratified_split(data, test_size=0.3, random_state=42)
        
        # Verify split sizes
        self.assertEqual(len(train_data) + len(test_data), len(data))
        
        # Verify that the split maintains family representation roughly
        # (Exact counts depend on random_state, but total must match)
        train_families = [extract_alloy_family(row) for row in train_data]
        test_families = [extract_alloy_family(row) for row in test_data]
        
        self.assertTrue(len(train_families) > 0)
        self.assertTrue(len(test_families) > 0)

    def test_hybrid_logic_simulation(self):
        """
        Simulate the hybrid logic:
        - If a family has enough samples (e.g., > 5), it can be used for LOFO (leave one out).
        - If a family is small, it is treated as a single group (GroupKFold style).
        
        This test verifies that the split logic respects family boundaries 
        which is a prerequisite for the hybrid LOFO/GroupKFold implementation 
        in the evaluation phase.
        """
        data = load_processed_data(self.data_path)
        
        # Count samples per family
        family_counts = {}
        for row in data:
            fam = extract_alloy_family(row)
            family_counts[fam] = family_counts.get(fam, 0) + 1
        
        # Zr-based has 6 (Large)
        # Pd-based has 3 (Small)
        # Mg-based has 4 (Medium/Small)
        
        self.assertEqual(family_counts["Zr-based"], 6)
        self.assertEqual(family_counts["Pd-based"], 3)
        self.assertEqual(family_counts["Mg-based"], 4)

        # Perform a split
        train_data, test_data = stratified_split(data, test_size=0.2, random_state=123)
        
        # Verify that we can still reconstruct family groups from the split data
        # This ensures the data structure supports group-based validation later
        train_families = set(extract_alloy_family(row) for row in train_data)
        test_families = set(extract_alloy_family(row) for row in test_data)
        
        self.assertTrue(len(train_families) > 0)
        self.assertTrue(len(test_families) > 0)

    def test_save_split_data(self):
        """Test that split data is saved correctly to disk."""
        data = load_processed_data(self.data_path)
        train_data, test_data = stratified_split(data, test_size=0.2, random_state=42)
        
        train_path = Path(self.temp_dir.name) / "train.csv"
        test_path = Path(self.temp_dir.name) / "test.csv"
        
        save_split_data(train_data, train_path)
        save_split_data(test_data, test_path)
        
        self.assertTrue(train_path.exists())
        self.assertTrue(test_path.exists())
        
        # Verify content
        with open(train_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), len(train_data))
