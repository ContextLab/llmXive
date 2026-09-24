"""
Unit tests for descriptor computation (T007).
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import unittest

import pandas as pd
import numpy as np

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from descriptors import compute_descriptors, load_raw_data, save_descriptors

class TestMagpieL2Normalization(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data = pd.DataFrame({
            'formula': ['H2O', 'NaCl', 'SiO2', 'Fe2O3'],
            'property_a': [1.0, 2.0, 3.0, 4.0]
        })
        
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Override paths for testing
        self.original_processed_dir = None
        
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_compute_descriptors_creates_columns(self):
        """Test that compute_descriptors creates descriptor columns."""
        # Create a minimal mock Magpie
        # Since we can't guarantee Magpie is installed in test env, we mock the compute result
        import unittest.mock as mock
        
        mock_descriptors = pd.DataFrame({
            'mean_atomic_number': [1.0, 11.0, 14.0, 26.0],
            'mean_atomic_mass': [1.0, 23.0, 28.0, 56.0],
            'mean_electronegativity': [2.1, 0.9, 1.8, 1.8],
            'mean_melting_point': [100.0, 800.0, 1600.0, 1500.0],
            'mean_molar_volume': [18.0, 27.0, 22.0, 7.0],
            'mean_valence_electrons': [1.0, 1.0, 4.0, 2.0],
            'mean_atomic_radius': [1.0, 1.9, 1.1, 1.2],
            'mean_first_ionization': [13.6, 5.1, 8.1, 7.9],
            'mean_electron_affinity': [0.0, 3.6, 1.4, 1.5],
            'mean_dipole_polarizability': [0.7, 1.0, 0.5, 0.2],
            'mean_specific_heat': [0.0, 0.8, 0.7, 0.4],
            'mean_thermal_conductivity': [0.6, 0.0, 1.4, 80.0],
            'mean_vickers_hardness': [0.0, 0.0, 9.0, 10.0],
            'mean_bulk_modulus': [0.0, 25.0, 35.0, 170.0]
        })
        
        with mock.patch('descriptors.Magpie') as MockMagpie:
            mock_instance = MockMagpie.return_value
            mock_instance.compute.return_value = mock_descriptors
            
            result = compute_descriptors(self.test_data)
            
            # Check that descriptor columns exist
            expected_desc_cols = list(mock_descriptors.columns)
            for col in expected_desc_cols:
                self.assertIn(col, result.columns)
            
            # Check that original columns are preserved
            self.assertIn('formula', result.columns)
            self.assertIn('property_a', result.columns)
    
    def test_l2_normalization_applied(self):
        """Test that L2-normalization is correctly applied to descriptors."""
        import unittest.mock as mock
        
        # Create mock descriptors with known values
        mock_descriptors = pd.DataFrame({
            'feat_a': [3.0, 0.0, 0.0],
            'feat_b': [4.0, 0.0, 0.0],
            'feat_c': [0.0, 3.0, 4.0]
        })
        
        with mock.patch('descriptors.Magpie') as MockMagpie:
            mock_instance = MockMagpie.return_value
            mock_instance.compute.return_value = mock_descriptors
            
            # Use only first 3 rows
            test_data = self.test_data.iloc[:3].reset_index(drop=True)
            result = compute_descriptors(test_data)
            
            # Check L2 norm of first row (should be 1.0)
            row0_norm = np.sqrt(result['feat_a'].iloc[0]**2 + result['feat_b'].iloc[0]**2)
            self.assertAlmostEqual(row0_norm, 1.0, places=5)
            
            # Check L2 norm of third row (should be 1.0)
            row2_norm = np.sqrt(result['feat_c'].iloc[2]**2 + result['feat_c'].iloc[2]**2) # Wait, feat_c is [0, 3, 4]
            # Actually row 2 is [0, 0, 4] for feat_c? No, feat_c is [0, 3, 4]
            # Let's recheck: row 2 has feat_c = 4.0, feat_a = 0.0, feat_b = 0.0
            row2_norm = np.sqrt(result['feat_a'].iloc[2]**2 + result['feat_b'].iloc[2]**2 + result['feat_c'].iloc[2]**2)
            self.assertAlmostEqual(row2_norm, 1.0, places=5)
    
    def test_save_descriptors_creates_file(self):
        """Test that save_descriptors creates the output file."""
        import unittest.mock as mock
        
        mock_descriptors = pd.DataFrame({
            'feat_a': [1.0, 2.0],
            'feat_b': [3.0, 4.0]
        })
        
        with mock.patch('descriptors.Magpie') as MockMagpie:
            mock_instance = MockMagpie.return_value
            mock_instance.compute.return_value = mock_descriptors
            
            result = compute_descriptors(self.test_data.iloc[:2].reset_index(drop=True))
            
            # Temporarily override OUTPUT_FILE
            import descriptors as desc_module
            original_output = desc_module.OUTPUT_FILE
            desc_module.OUTPUT_FILE = Path(self.processed_dir) / "test_descriptors.parquet"
            
            try:
                save_descriptors(result)
                self.assertTrue((Path(self.processed_dir) / "test_descriptors.parquet").exists())
            finally:
                desc_module.OUTPUT_FILE = original_output

if __name__ == '__main__':
    unittest.main()