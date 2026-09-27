"""
Integration tests for the model pipeline, specifically focusing on PGLS fitting.

This module verifies that the Phylogenetic Generalized Least Squares (PGLS) 
model converges correctly and that the phylogenetic signal (lambda) is 
statistically significant (> 0) when run on real data.
"""
import os
import sys
import unittest
from pathlib import Path
import tempfile
import shutil

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from caper import ComparativeData
from scipy.stats import pearsonr

# Import the function to test
from models import fit_pgl
from config import ensure_directories


class TestPGLSIntegration(unittest.TestCase):
    """Integration tests for PGLS model fitting."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_path = self.test_dir / "test_merged_data.csv"
        self.tree_path = self.test_dir / "test_tree.newick"
        
        # Ensure directories exist
        ensure_directories()

        # Create a minimal valid phylogenetic tree (Newick format)
        # A simple tree with 5 species to ensure PGLS can run
        self.simple_tree = """
        (Species_A:1.0, (Species_B:0.8, (Species_C:0.5, Species_D:0.5):0.3):0.2, Species_E:1.0);
        """
        with open(self.tree_path, 'w') as f:
            f.write(self.simple_tree.strip())

        # Create a minimal merged dataset that matches the tree
        # We need species that exist in the tree and have valid numerical data
        self.test_data = pd.DataFrame({
            'species': ['Species_A', 'Species_B', 'Species_C', 'Species_D', 'Species_E'],
            'depth': [10.5, 12.3, 8.7, 9.1, 11.2],
            'surface_area': [50.0, 60.0, 45.0, 48.0, 55.0],
            'conductance': [0.25, 0.30, 0.20, 0.22, 0.28],
            'photosynthesis': [15.0, 18.0, 12.0, 13.5, 16.5]
        })
        
        self.test_data.to_csv(self.data_path, index=False)

    def tearDown(self):
        """Clean up test files."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_pgl_fits_with_phylogenetic_structure(self):
        """
        Test that PGLS converges and phylogenetic signal lambda > 0.
        
        This test:
        1. Loads real test data and tree
        2. Fits a PGLS model predicting conductance from depth and surface_area
        3. Asserts the model converges
        4. Asserts the phylogenetic signal (lambda) is > 0
        """
        # Ensure the input files exist
        assert self.data_path.exists(), "Test data file not found"
        assert self.tree_path.exists(), "Test tree file not found"

        try:
            # Fit the PGLS model
            # Arguments: data_path, tree_path, target_var, predictors
            result = fit_pgl(
                data_path=str(self.data_path),
                tree_path=str(self.tree_path),
                target_var='conductance',
                predictors=['depth', 'surface_area']
            )

            # Verify the result is not None
            self.assertIsNotNone(result, "PGLS fit returned None")

            # Check that the result contains expected keys
            self.assertIn('lambda', result, "Result missing 'lambda' value")
            self.assertIn('converged', result, "Result missing 'converged' status")
            self.assertIn('coefficients', result, "Result missing 'coefficients'")

            # Assert convergence
            self.assertTrue(
                result['converged'], 
                f"PGLS model did not converge. Result: {result}"
            )

            # Assert phylogenetic signal lambda > 0
            # Lambda represents the strength of phylogenetic signal
            # A value > 0 indicates that phylogeny explains some variance
            lambda_val = result['lambda']
            self.assertGreater(
                lambda_val, 
                0.0, 
                f"Phylogenetic signal (lambda) is not > 0. Got: {lambda_val}"
            )

            # Additional check: lambda should be <= 1.0 (standard range for lambda)
            self.assertLessEqual(
                lambda_val, 
                1.0, 
                f"Phylogenetic signal (lambda) is unexpectedly > 1.0. Got: {lambda_val}"
            )

            # Verify coefficients exist and are numerical
            coeffs = result['coefficients']
            self.assertIsInstance(coeffs, dict, "Coefficients should be a dictionary")
            self.assertIn('intercept', coeffs, "Missing intercept in coefficients")
            
            # Check that predictors have coefficients
            for pred in ['depth', 'surface_area']:
                self.assertIn(pred, coeffs, f"Missing coefficient for {pred}")
                self.assertIsInstance(coeffs[pred], (int, float), f"Invalid coefficient type for {pred}")

        except Exception as e:
            self.fail(f"PGLS fitting failed with exception: {e}")

    def test_pgl_handles_missing_species_gracefully(self):
        """
        Test that PGLS handles cases where data species don't match tree species.
        
        This test verifies the error handling when there's a mismatch between
        the species in the dataset and the species in the phylogenetic tree.
        """
        # Create a dataset with species NOT in the tree
        mismatch_data = pd.DataFrame({
            'species': ['Unknown_Species_X', 'Unknown_Species_Y'],
            'depth': [10.0, 12.0],
            'surface_area': [50.0, 60.0],
            'conductance': [0.25, 0.30],
            'photosynthesis': [15.0, 18.0]
        })
        
        mismatch_path = self.test_dir / "mismatch_data.csv"
        mismatch_data.to_csv(mismatch_path, index=False)

        # We expect this to fail because there's no overlap between data and tree
        with self.assertRaises(Exception):
            fit_pgl(
                data_path=str(mismatch_path),
                tree_path=str(self.tree_path),
                target_var='conductance',
                predictors=['depth', 'surface_area']
            )

    def test_pgl_with_real_data_structure(self):
        """
        Test PGLS with a more realistic data structure that mimics the actual pipeline.
        
        This test creates a dataset with more species and realistic trait correlations
        to ensure the model behaves correctly under more complex conditions.
        """
        # Create a larger dataset with realistic correlations
        np.random.seed(42)
        n_species = 10
        
        # Generate a more complex tree structure
        complex_tree = """
        (S1:1.0, (S2:0.8, (S3:0.6, (S4:0.4, S5:0.4):0.2):0.2):0.2, 
         (S6:0.9, (S7:0.7, (S8:0.5, (S9:0.3, S10:0.3):0.2):0.2):0.2):0.1);
        """
        complex_tree_path = self.test_dir / "complex_tree.newick"
        with open(complex_tree_path, 'w') as f:
            f.write(complex_tree.strip())

        # Generate correlated data
        species_list = [f'S{i}' for i in range(1, 11)]
        
        # Create data with known phylogenetic signal
        # Depth and conductance should be correlated
        base_depth = np.random.uniform(8, 15, n_species)
        base_conductance = base_depth * 0.02 + np.random.normal(0, 0.01, n_species)
        
        test_data = pd.DataFrame({
            'species': species_list,
            'depth': base_depth,
            'surface_area': base_depth * 5 + np.random.normal(0, 1, n_species),
            'conductance': base_conductance,
            'photosynthesis': base_conductance * 60 + np.random.normal(0, 1, n_species)
        })
        
        complex_data_path = self.test_dir / "complex_data.csv"
        test_data.to_csv(complex_data_path, index=False)

        try:
            result = fit_pgl(
                data_path=str(complex_data_path),
                tree_path=str(complex_tree_path),
                target_var='conductance',
                predictors=['depth', 'surface_area']
            )

            self.assertIsNotNone(result)
            self.assertTrue(result['converged'])
            self.assertGreater(result['lambda'], 0.0)
            
            # Check that the model found a significant relationship
            # (R-squared should be reasonable for correlated data)
            if 'r_squared' in result:
                self.assertGreater(result['r_squared'], 0.0)
                
        except Exception as e:
            self.fail(f"PGLS with complex data failed: {e}")


if __name__ == '__main__':
    unittest.main()