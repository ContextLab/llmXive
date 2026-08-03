"""
Integration test for full generation and split workflow (T010).

This test mocks the HuggingFace download to avoid network dependencies,
then runs the real preprocessing, splitting, and validation logic to ensure
the pipeline produces the expected directory structure and manifest files.
"""
import os
import sys
import unittest
import tempfile
import shutil
import json
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import cv2

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data import preprocess
from data import split
from data import validate
from utils.config import get_project_root, get_data_dir, get_processed_dir, get_raw_dir, get_results_dir, set_seed


class TestDataPipeline(unittest.TestCase):
    """Integration test for the full data pipeline workflow."""

    def setUp(self):
        """Set up a temporary directory structure for the test."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Create a fake project root structure in the temp directory
        self.mock_root = Path(self.test_dir) / "mock_project"
        self.mock_root.mkdir(parents=True)
        
        # Create required directories
        (self.mock_root / "code").mkdir()
        (self.mock_root / "data").mkdir()
        (self.mock_root / "data" / "raw").mkdir()
        (self.mock_root / "data" / "processed").mkdir()
        (self.mock_root / "results").mkdir()
        
        # Change to the mock project root
        os.chdir(self.mock_root)
        
        # Patch the project root detection
        self.root_patcher = patch('utils.config._find_project_root', return_value=self.mock_root)
        self.root_patcher.start()
        
        # Initialize seed
        set_seed(42)

    def tearDown(self):
        """Clean up temporary files and restore state."""
        os.chdir(self.original_cwd)
        self.root_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_mock_image(self, path: Path, shape=(224, 224, 3)):
        """Create a dummy image file for testing."""
        path.parent.mkdir(parents=True, exist_ok=True)
        # Create a random image
        img = np.random.randint(0, 255, shape, dtype=np.uint8)
        cv2.imwrite(str(path), img)

    def _create_mock_raw_data(self, count=10):
        """Create mock raw data images and a manifest."""
        raw_dir = get_raw_dir()
        manifest_path = raw_dir / "manifest.csv"
        
        with open(manifest_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'image_path', 'yield_strength'])
            
            for i in range(count):
                img_name = f"sample_{i:04d}.png"
                img_path = raw_dir / img_name
                self._create_mock_image(img_path)
                # Assign a deterministic yield strength based on index
                yield_strength = 200.0 + (i * 10.0)
                writer.writerow([f"specimen_{i:04d}", img_name, yield_strength])

    @patch('datasets.load_dataset')
    def test_full_pipeline(self, mock_load_dataset):
        """
        Test the full generation and split workflow.
        
        This test:
        1. Mocks the HuggingFace download (T040 step).
        2. Runs the real preprocess.py (T041).
        3. Runs the real split.py (T013).
        4. Runs the real validate.py (T042).
        5. Asserts that data/processed/train, val, test directories exist with >0 files.
        6. Asserts that manifest.csv contains valid mappings.
        """
        
        # 1. Mock the download step (simulating T040)
        # We create the raw data manually instead of actually downloading
        self._create_mock_raw_data(count=10)
        
        # 2. Run Preprocessing (T041)
        # Simulate the command: python code/data/preprocess.py
        try:
            preprocess.main()
        except SystemExit as e:
            if e.code != 0:
                self.fail(f"Preprocessing failed with exit code {e.code}")
        
        # Verify preprocess output
        processed_dir = get_processed_dir()
        self.assertTrue(processed_dir.exists(), "Processed directory should exist")
        
        # Check if manifest exists
        processed_manifest = processed_dir / "manifest.csv"
        self.assertTrue(processed_manifest.exists(), "Processed manifest should exist")
        
        with open(processed_manifest, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertGreater(len(rows), 0, "Processed manifest should have rows")
            # Verify schema
            self.assertIn('image_id', rows[0])
            self.assertIn('image_path', rows[0])
            self.assertIn('yield_strength', rows[0])

        # 3. Run Splitting (T013)
        try:
            split.main()
        except SystemExit as e:
            if e.code != 0:
                self.fail(f"Splitting failed with exit code {e.code}")
        
        # Verify split output
        train_dir = processed_dir / "train"
        val_dir = processed_dir / "val"
        test_dir = processed_dir / "test"
        
        self.assertTrue(train_dir.exists(), "Train directory should exist")
        self.assertTrue(val_dir.exists(), "Validation directory should exist")
        self.assertTrue(test_dir.exists(), "Test directory should exist")
        
        # Assert >0 files in each directory
        train_files = list(train_dir.glob("*.png"))
        val_files = list(val_dir.glob("*.png"))
        test_files = list(test_dir.glob("*.png"))
        
        self.assertGreater(len(train_files), 0, "Train directory should have >0 files")
        self.assertGreater(len(val_files), 0, "Validation directory should have >0 files")
        self.assertGreater(len(test_files), 0, "Test directory should have >0 files")
        
        # 4. Run Validation (T042)
        try:
            validate.main()
        except SystemExit as e:
            # Validation might exit 1 if invalid ratio > 1%, but with mock data it should be 0
            # We expect 0 for valid mock data
            if e.code != 0:
                # If it failed, check the report to see why
                report_path = get_results_dir() / "validation_report.json"
                if report_path.exists():
                    with open(report_path, 'r') as f:
                        report = json.load(f)
                    self.fail(f"Validation failed: {report}")
                else:
                    self.fail("Validation failed but no report generated")

        # 5. Assert manifest.csv contains valid mappings
        # The split should have generated a new manifest or updated the existing one
        # We check the processed manifest again to ensure it reflects the splits
        # Or check if split generated specific split manifests
        
        # Check the main processed manifest still has valid data
        with open(processed_manifest, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Verify that image paths point to existing files in the split directories
            valid_mappings = 0
            for row in rows:
                img_id = row['image_id']
                img_path_str = row['image_path']
                yield_str = row['yield_strength']
                
                # Check if yield strength is a valid number
                try:
                    float(yield_str)
                except ValueError:
                    self.fail(f"Invalid yield strength in manifest: {yield_str}")
                
                # Check if the image path is relative and corresponds to a file
                # The split process might have moved files, so we check the split dirs
                found_in_split = False
                for split_name, split_dir in [("train", train_dir), ("val", val_dir), ("test", test_dir)]:
                    potential_path = split_dir / img_path_str
                    if potential_path.exists():
                        found_in_split = True
                        break
                
                if found_in_split:
                    valid_mappings += 1
        
        self.assertGreater(valid_mappings, 0, "Manifest should contain valid mappings to existing files")

        # 6. Additional check: Verify split consistency
        # Total files in splits should match total files in processed manifest (minus any invalids)
        total_split_files = len(train_files) + len(val_files) + len(test_files)
        # Note: Some files might be excluded if validation failed, but with mock data all should pass
        self.assertGreater(total_split_files, 0, "Total split files should be > 0")


if __name__ == '__main__':
    unittest.main()