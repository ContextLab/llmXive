"""
Unit tests for the synthetic microstructure generator (T005).
"""
import os
import json
import unittest
import numpy as np
from PIL import Image
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.data.synthetic_gen import main, calculate_physics_informed_k_ic

class TestSyntheticGen(unittest.TestCase):
    
    def setUp(self):
        """Ensure the generator runs and produces expected outputs."""
        # Run the generator
        self.exit_code = main()
        self.assertEqual(self.exit_code, 0, "Generator failed to run successfully")
        
        self.output_dir = Path("data/raw")
        self.metadata_file = self.output_dir / "synthetic_metadata.json"
    
    def test_image_count(self):
        """Verify that >= 2000 images were generated."""
        png_files = list(self.output_dir.glob("synthetic_microstructure_*.png"))
        self.assertGreaterEqual(len(png_files), 2000, 
                                f"Expected >= 2000 images, found {len(png_files)}")
    
    def test_metadata_exists(self):
        """Verify metadata JSON file exists and is valid."""
        self.assertTrue(self.metadata_file.exists(), "Metadata file not found")
        
        with open(self.metadata_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn("records", data)
        self.assertGreaterEqual(len(data["records"]), 2000)
    
    def test_metadata_schema(self):
        """Verify metadata records contain required fields."""
        with open(self.metadata_file, 'r') as f:
            data = json.load(f)
        
        required_fields = ["id", "filename", "alloy_family", "k_ic_mpa_sqrtm", "microstructure_params"]
        
        for record in data["records"][:10]: # Check first 10
            for field in required_fields:
                self.assertIn(field, record, f"Missing field '{field}' in record")
            
            # Check nested fields
            params = record["microstructure_params"]
            self.assertIn("resolution_um", params)
            self.assertIn("preparation_protocol", params)
            self.assertIn("num_grains", params)
    
    def test_image_validity(self):
        """Verify generated images are valid grayscale PNGs of correct size."""
        sample_file = self.output_dir / "synthetic_microstructure_0000.png"
        self.assertTrue(sample_file.exists())
        
        img = Image.open(sample_file)
        self.assertEqual(img.mode, "L", "Image should be grayscale")
        self.assertEqual(img.size, (128, 128), "Image size should be 128x128")
    
    def test_k_ic_physics(self):
        """Verify K_IC values are within physical bounds for alloy families."""
        with open(self.metadata_file, 'r') as f:
            data = json.load(f)
        
        for record in data["records"]:
            alloy = record["alloy_family"]
            k_ic = record["k_ic_mpa_sqrtm"]
            
            if alloy == "Al":
                self.assertGreaterEqual(k_ic, 20.0)
                self.assertLessEqual(k_ic, 40.0)
            elif alloy == "Steel":
                self.assertGreaterEqual(k_ic, 50.0)
                self.assertLessEqual(k_ic, 150.0)
            elif alloy == "Ti":
                self.assertGreaterEqual(k_ic, 50.0)
                self.assertLessEqual(k_ic, 120.0)
    
    def tearDown(self):
        """Cleanup generated files to keep test environment clean."""
        # Optional: Remove generated files if strict isolation is needed
        # For this test, we assume the generator is idempotent and files are expected
        pass

if __name__ == "__main__":
    unittest.main()