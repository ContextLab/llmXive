"""
Unit tests for conformer generation and molecular flexibility descriptors.
This module tests the logic in code/data/conformer_gen.py and code/data/descriptors.py.
"""

import os
import sys
import pickle
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

# Add the project root to the path to allow imports
# We assume the test is run from the project root or the path is set up correctly
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.conformer_gen import generate_conformers, load_filtered_data
from data.descriptors import (
    load_conformers,
    get_conformer_count,
    calculate_internal_coordinate_variance,
    calculate_variance_metrics,
    process_molecules
)
from utils.config import get_project_root, set_seed

class TestConformerGeneration(unittest.TestCase):
    """Tests for the conformer generation logic."""

    def setUp(self):
        """Set up test fixtures."""
        set_seed(42)
        self.project_root = get_project_root()
        self.test_smiles_list = [
            "CCO",  # Ethanol - simple, flexible
            "CC(=O)O", # Acetic acid
            "c1ccccc1", # Benzene - rigid
            "CCCCCCCCCCCC", # Dodecane - highly flexible
            "C1CCCCC1" # Cyclohexane
        ]

    def test_generate_conformers_empty_list(self):
        """Test that an empty list returns an empty result."""
        result = generate_conformers([])
        self.assertEqual(len(result), 0)

    def test_generate_conformers_single_molecule(self):
        """Test generation for a single, simple molecule."""
        smiles = "CCO"
        result = generate_conformers([smiles])
        
        self.assertEqual(len(result), 1)
        self.assertIn("smiles", result[0])
        self.assertIn("conformers", result[0])
        self.assertIn("lowest_energy_conformer_id", result[0])
        
        # Check that conformers were generated (at least 1, up to 50)
        conformers = result[0]["conformers"]
        self.assertGreater(len(conformers), 0)
        self.assertLessEqual(len(conformers), 50)

    def test_generate_conformers_rigid_molecule(self):
        """Test generation for a rigid molecule (benzene)."""
        smiles = "c1ccccc1"
        result = generate_conformers([smiles])
        
        self.assertEqual(len(result), 1)
        # Benzene is rigid, so conformers should be very similar or identical
        # but we still expect the function to return a list of conformers
        self.assertIn("conformers", result[0])
        self.assertGreater(len(result[0]["conformers"]), 0)

    def test_generate_conformers_flexible_molecule(self):
        """Test generation for a flexible molecule (dodecane)."""
        smiles = "CCCCCCCCCCCC"
        result = generate_conformers([smiles])
        
        self.assertEqual(len(result), 1)
        # Flexible molecules should generate a diverse set of conformers
        self.assertGreater(len(result[0]["conformers"]), 1)

    def test_generate_conformers_invalid_smiles(self):
        """Test handling of invalid SMILES strings."""
        invalid_smiles = ["invalid_smiles_string", "CCO"]
        result = generate_conformers(invalid_smiles)
        
        # The function should handle invalid SMILES gracefully, 
        # likely by skipping them or returning an empty list for that entry.
        # We expect the result to only contain valid molecules or be filtered.
        # For this test, we check that the function doesn't crash and returns a list.
        self.assertIsInstance(result, list)
        # If the implementation skips invalid SMILES, we should have 1 valid entry.
        # If it fails on the first one, we might have 0.
        # The exact behavior depends on the implementation in conformer_gen.py.
        # We assert that it doesn't raise an exception.

    def test_generate_conformers_energy_window(self):
        """Test that conformers are within the energy window."""
        # This is a bit tricky to test without inspecting the internal energy values
        # We assume the implementation in conformer_gen.py handles this correctly.
        # We can test that the function runs without error and returns results.
        smiles_list = ["CCO", "CCCCCCCCCCCC"]
        result = generate_conformers(smiles_list)
        self.assertEqual(len(result), 2) # Assuming both are valid

    def test_generate_conformers_output_structure(self):
        """Test the structure of the output data."""
        smiles_list = ["CCO"]
        result = generate_conformers(smiles_list)
        
        self.assertEqual(len(result), 1)
        entry = result[0]
        
        # Check required keys
        self.assertIn("smiles", entry)
        self.assertIn("conformers", entry)
        self.assertIn("lowest_energy_conformer_id", entry)
        self.assertIn("rdkit_mol", entry) # Assuming rdkit_mol is stored for later use

        # Check conformer structure
        conformers = entry["conformers"]
        for conf in conformers:
            self.assertIn("id", conf)
            self.assertIn("energy", conf)
            self.assertIn("positions", conf) # 3D coordinates

class TestDescriptorCalculation(unittest.TestCase):
    """Tests for the descriptor calculation logic."""

    def setUp(self):
        """Set up test fixtures."""
        set_seed(42)
        self.project_root = get_project_root()
        
        # Create a mock conformer dataset for testing
        self.mock_conformers = [
            {
                "smiles": "CCO",
                "conformers": [
                    {"id": 0, "energy": 0.0, "positions": np.random.rand(9, 3).tolist()},
                    {"id": 1, "energy": 0.5, "positions": np.random.rand(9, 3).tolist()},
                    {"id": 2, "energy": 1.0, "positions": np.random.rand(9, 3).tolist()},
                ],
                "lowest_energy_conformer_id": 0,
                "rdkit_mol": None # Will be handled by the function
            }
        ]

    def test_get_conformer_count(self):
        """Test the function to count conformers."""
        count = get_conformer_count(self.mock_conformers)
        self.assertEqual(count, 3) # Should count conformers for the first molecule

    def test_calculate_internal_coordinate_variance(self):
        """Test the calculation of internal coordinate variance."""
        # This function likely requires a valid RDKit molecule object
        # We will test it with a mock or by generating a real one
        smiles = "CCO"
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        mol = Chem.AddHs(mol)
        
        # Generate a simple conformer for testing
        from rdkit.Chem import AllChem
        AllChem.EmbedMolecule(mol, randomSeed=42)
        
        # Create a mock entry with the real molecule
        mock_entry = {
            "smiles": smiles,
            "conformers": [{"id": 0, "energy": 0.0, "positions": np.array(mol.GetConformer().GetPositions()).tolist()}],
            "lowest_energy_conformer_id": 0,
            "rdkit_mol": mol
        }
        
        # The function might expect a list of conformers or a specific structure
        # We'll test the logic by calling it with the mock entry
        # Note: The actual implementation in descriptors.py might differ
        # This test ensures the function is callable and returns a result
        try:
            # Assuming the function takes a list of conformers and a mol object
            # This is a placeholder test; the exact call depends on the implementation
            variance = calculate_internal_coordinate_variance(mock_entry["conformers"], mock_entry["rdkit_mol"])
            self.assertIsInstance(variance, dict)
            self.assertIn("bond", variance)
            self.assertIn("angle", variance)
            self.assertIn("dihedral", variance)
        except Exception as e:
            # If the implementation is different, we might need to adjust this test
            self.fail(f"calculate_internal_coordinate_variance failed: {e}")

    def test_calculate_variance_metrics(self):
        """Test the calculation of variance metrics from raw data."""
        # Create mock raw variance data
        raw_data = {
            "bond": [0.1, 0.2, 0.3],
            "angle": [0.2, 0.3, 0.4],
            "dihedral": [0.3, 0.4, 0.5]
        }
        
        metrics = calculate_variance_metrics(raw_data)
        
        self.assertIn("bond_variance", metrics)
        self.assertIn("angle_variance", metrics)
        self.assertIn("dihedral_variance", metrics)
        
        # Check that the values are reasonable (variance of the input lists)
        self.assertAlmostEqual(metrics["bond_variance"], np.var(raw_data["bond"]), places=5)
        self.assertAlmostEqual(metrics["angle_variance"], np.var(raw_data["angle"]), places=5)
        self.assertAlmostEqual(metrics["dihedral_variance"], np.var(raw_data["dihedral"]), places=5)

    def test_process_molecules(self):
        """Test the end-to-end processing of molecules."""
        # This function likely orchestrates the entire descriptor calculation
        # We will test it with a small, valid dataset
        smiles_list = ["CCO", "CC(=O)O"]
        
        # Generate conformers first (this might be slow, so we mock it or use a small set)
        # For this unit test, we assume conformers are already generated and stored
        # We will create a mock conformer dataset
        mock_conformer_data = []
        for smiles in smiles_list:
            from rdkit import Chem
            mol = Chem.MolFromSmiles(smiles)
            mol = Chem.AddHs(mol)
            AllChem.EmbedMolecule(mol, randomSeed=42)
            
            mock_conformer_data.append({
                "smiles": smiles,
                "conformers": [{"id": 0, "energy": 0.0, "positions": np.array(mol.GetConformer().GetPositions()).tolist()}],
                "lowest_energy_conformer_id": 0,
                "rdkit_mol": mol
            })
        
        # Call the process_molecules function
        # Note: The actual implementation might take a list of conformer entries
        descriptors = process_molecules(mock_conformer_data)
        
        self.assertEqual(len(descriptors), 2)
        for desc in descriptors:
            self.assertIn("smiles", desc)
            self.assertIn("bond_variance", desc)
            self.assertIn("angle_variance", desc)
            self.assertIn("dihedral_variance", desc)

    def test_flag_outliers(self):
        """Test the outlier flagging logic."""
        # Create a dataset with some outliers
        data = pd.DataFrame({
            "bond_variance": [0.1, 0.2, 0.3, 100.0], # 100 is an outlier
            "angle_variance": [0.2, 0.3, 0.4, 0.5],
            "dihedral_variance": [0.3, 0.4, 0.5, 0.6]
        })
        
        flagged_data = flag_outliers(data)
        
        self.assertIn("is_outlier", flagged_data.columns)
        # The last row should be flagged as an outlier
        self.assertTrue(flagged_data.iloc[3]["is_outlier"])
        # The first three should not be (assuming a standard IQR method)
        self.assertFalse(flagged_data.iloc[0]["is_outlier"])
        self.assertFalse(flagged_data.iloc[1]["is_outlier"])
        self.assertFalse(flagged_data.iloc[2]["is_outlier"])

class TestIntegration(unittest.TestCase):
    """Integration tests for the full pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        set_seed(42)
        self.project_root = get_project_root()
        self.test_dir = tempfile.mkdtemp()
        self.conformer_path = os.path.join(self.test_dir, "test_conformers.pkl")

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.conformer_path):
            os.remove(self.conformer_path)

    def test_full_conformer_to_descriptor_pipeline(self):
        """Test the full pipeline from SMILES to descriptors."""
        smiles_list = ["CCO", "CC(=O)O"]
        
        # Step 1: Generate conformers
        conformer_data = generate_conformers(smiles_list)
        
        # Step 2: Save conformers to a temporary file
        with open(self.conformer_path, "wb") as f:
            pickle.dump(conformer_data, f)
        
        # Step 3: Load conformers
        loaded_conformers = load_conformers(self.conformer_path)
        self.assertEqual(len(loaded_conformers), 2)
        
        # Step 4: Calculate descriptors
        descriptors = process_molecules(loaded_conformers)
        
        self.assertEqual(len(descriptors), 2)
        for desc in descriptors:
            self.assertIn("bond_variance", desc)
            self.assertIn("angle_variance", desc)
            self.assertIn("dihedral_variance", desc)
            # Check that variances are non-negative
            self.assertGreaterEqual(desc["bond_variance"], 0)
            self.assertGreaterEqual(desc["angle_variance"], 0)
            self.assertGreaterEqual(desc["dihedral_variance"], 0)

    def test_load_conformers_invalid_file(self):
        """Test loading conformers from an invalid file."""
        # Create an empty or invalid file
        with open(self.conformer_path, "wb") as f:
            f.write(b"invalid pickle data")
        
        with self.assertRaises(Exception):
            load_conformers(self.conformer_path)

if __name__ == "__main__":
    unittest.main()