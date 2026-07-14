"""
Unit tests for the grain size feature extraction module.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import cv2

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data.extract_features import estimate_grain_size, extract_features_for_dataset, save_features_csv
from utils.config import set_seed

class TestGrainSizeExtraction(unittest.TestCase):

    def setUp(self):
        """Create temporary test images."""
        set_seed(42)
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.temp_dir) / "raw"
        self.processed_dir = Path(self.temp_dir) / "processed"
        self.raw_dir.mkdir(parents=True)
        
        # Create a synthetic image with known "grains" (white circles on black background)
        # Image size: 100x100
        # Pixel size: 1.0 um
        # Two circles of radius 10px (Area = pi*100, ECD = 2*10 = 20)
        self.test_image_path = self.raw_dir / "test_img.png"
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Draw two circles (grains)
        cv2.circle(img, (30, 30), 10, (255, 255, 255), -1)
        cv2.circle(img, (70, 70), 10, (255, 255, 255), -1)
        
        cv2.imwrite(str(self.test_image_path), img)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_estimate_grain_size_known_geometry(self):
        """Test extraction on a synthetic image with known grain size."""
        # Expected ECD for circle with radius 10px is 20px.
        # With pixel_size_um = 1.0, expected size is 20.0 um.
        result = estimate_grain_size(self.test_image_path, pixel_size_um=1.0)
        
        self.assertIsNotNone(result)
        # Allow some tolerance due to morphological operations and discretization
        self.assertAlmostEqual(result, 20.0, delta=2.0)

    def test_estimate_grain_size_no_grains(self):
        """Test extraction on a black image (no grains)."""
        black_img_path = self.raw_dir / "black_img.png"
        black_img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(black_img_path), black_img)
        
        result = estimate_grain_size(black_img_path, pixel_size_um=1.0)
        self.assertIsNone(result)

    def test_extract_features_for_dataset(self):
        """Test the full dataset extraction pipeline."""
        results = extract_features_for_dataset(self.raw_dir, self.processed_dir, pixel_size_um=1.0)
        
        self.assertEqual(len(results), 1)
        image_id, size = results[0]
        self.assertEqual(image_id, "test_img")
        self.assertAlmostEqual(size, 20.0, delta=2.0)

    def test_save_features_csv(self):
        """Test CSV saving functionality."""
        results = [("img1", 10.5), ("img2", 15.2)]
        output_path = self.processed_dir / "test_output.csv"
        
        save_features_csv(results, output_path)
        
        self.assertTrue(output_path.exists())
        with open(output_path, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 3) # Header + 2 rows
        self.assertIn("image_id", lines[0])
        self.assertIn("grain_size_um", lines[0])

if __name__ == "__main__":
    unittest.main()