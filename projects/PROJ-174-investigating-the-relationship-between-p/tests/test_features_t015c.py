"""
Tests for T015c: On-the-Fly Salience Computation.
"""
import os
import sys
import unittest
import tempfile
import shutil
import numpy as np
import pandas as pd
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.features import (
    process_target_salience_metadata,
    compute_target_salience,
    compute_gabor_salience,
    process_dataset_features
)

class TestT015cSalience(unittest.TestCase):

    def setUp(self):
        """Create temporary directories and mock data for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.stimuli_dir = os.path.join(self.temp_dir, "stimuli")
        os.makedirs(self.stimuli_dir)
        
        # Create a dummy image for testing (using numpy and saving as PNG)
        # We'll use a simple gradient image
        dummy_img = np.zeros((100, 100), dtype=np.uint8)
        dummy_img[:, :] = 128  # Gray background
        # Add a high-contrast edge
        dummy_img[:, 50:] = 255
        
        self.test_img_path = os.path.join(self.stimuli_dir, "1.png")
        cv2 = __import__('cv2')
        cv2.imwrite(self.test_img_path, dummy_img)

        self.test_img_missing = os.path.join(self.stimuli_dir, "missing.png")
        # Do not create this file

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir)

    def test_process_target_salience_metadata_marks_nan(self):
        """Test that NaN values are marked as NEEDS_COMPUTATION."""
        df = pd.DataFrame({
            'trial_id': [1, 2, 3],
            'target_salience': [0.5, np.nan, 0.8]
        })
        
        result = process_target_salience_metadata(df)
        
        self.assertEqual(result.loc[0, 'status'], 'OK')
        self.assertEqual(result.loc[1, 'status'], 'NEEDS_COMPUTATION')
        self.assertEqual(result.loc[2, 'status'], 'OK')
        self.assertTrue(np.isnan(result.loc[1, 'target_salience']))

    def test_compute_gabor_salience_returns_value(self):
        """Test that Gabor salience computation returns a float for a valid image."""
        config = {
            'wavelength': 10.0,
            'sigma': 5.0,
            'gamma': 0.5,
            'orientations': [0, 90],
            'scales': [1.0]
        }
        
        salience = compute_gabor_salience(self.test_img_path, config)
        
        self.assertIsNotNone(salience)
        self.assertIsInstance(salience, float)
        self.assertGreater(salience, 0)

    def test_compute_target_salience_handles_missing_image(self):
        """Test that missing images are marked as UNFULFILLABLE."""
        df = pd.DataFrame({
            'trial_id': [999], # No image 999.png exists
            'target_salience': [np.nan],
            'status': ['NEEDS_COMPUTATION']
        })
        
        config = {
            'wavelength': 10.0,
            'sigma': 5.0,
            'gamma': 0.5,
            'orientations': [0],
            'scales': [1.0]
        }
        
        result = compute_target_salience(df, self.stimuli_dir, config)
        
        self.assertEqual(result.loc[0, 'status'], 'UNFULFILLABLE')
        self.assertTrue(np.isnan(result.loc[0, 'target_salience']))

    def test_compute_target_salience_computes_when_found(self):
        """Test that salience is computed when image exists."""
        df = pd.DataFrame({
            'trial_id': [1], # Image 1.png exists
            'target_salience': [np.nan],
            'status': ['NEEDS_COMPUTATION']
        })
        
        config = {
            'wavelength': 10.0,
            'sigma': 5.0,
            'gamma': 0.5,
            'orientations': [0],
            'scales': [1.0]
        }
        
        result = compute_target_salience(df, self.stimuli_dir, config)
        
        self.assertEqual(result.loc[0, 'status'], 'OK')
        self.assertFalse(np.isnan(result.loc[0, 'target_salience']))

    def test_process_dataset_features_pipeline(self):
        """Test the full pipeline with mixed valid/invalid entries."""
        # Create input CSV
        input_path = os.path.join(self.temp_dir, "input.csv")
        df_input = pd.DataFrame({
            'trial_id': [1, 2, 999],
            'target_salience': [np.nan, np.nan, np.nan],
            'status': ['NEEDS_COMPUTATION', 'NEEDS_COMPUTATION', 'NEEDS_COMPUTATION']
        })
        df_input.to_csv(input_path, index=False)
        
        output_path = os.path.join(self.temp_dir, "output.csv")
        
        config = {
            'wavelength': 10.0,
            'sigma': 5.0,
            'gamma': 0.5,
            'orientations': [0],
            'scales': [1.0]
        }
        
        process_dataset_features(input_path, output_path, self.stimuli_dir, config)
        
        # Verify output
        self.assertTrue(os.path.exists(output_path))
        df_out = pd.read_csv(output_path)
        
        self.assertEqual(len(df_out), 3)
        self.assertEqual(df_out.loc[0, 'status'], 'OK') # Has image
        self.assertEqual(df_out.loc[1, 'status'], 'UNFULFILLABLE') # No image (2.png missing)
        self.assertEqual(df_out.loc[2, 'status'], 'UNFULFILLABLE') # No image (999.png missing)

if __name__ == '__main__':
    unittest.main()