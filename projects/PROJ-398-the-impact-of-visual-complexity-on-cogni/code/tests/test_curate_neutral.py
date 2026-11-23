"""
Tests for T032d: Curate Neutral Stimuli
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from PIL import Image

# Ensure src is in path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.experiment.curate_neutral import (
    load_metrics, 
    filter_neutral_stimuli, 
    copy_stimuli_to_neutral, 
    save_manifest, 
    main,
    OBJECT_COUNT_THRESHOLD
)
from src.config import DATA_DIR, PROJECT_ROOT


class TestCurateNeutral(unittest.TestCase):
    """Test suite for neutral stimuli curation logic."""

    def setUp(self):
        """Set up temporary directories and mock files for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.test_dir) / "stimuli" / "raw"
        self.neutral_dir = Path(self.test_dir) / "stimuli" / "neutral"
        self.processed_dir = Path(self.test_dir) / "processed"
        
        self.raw_dir.mkdir(parents=True)
        self.processed_dir.mkdir(parents=True)
        
        # Create mock images
        self.img_ids = ["img_001", "img_002", "img_003"]
        for img_id in self.img_ids:
            img_path = self.raw_dir / f"{img_id}.jpg"
            img = Image.new('RGB', (640, 640), color='red')
            img.save(img_path)

        # Create mock metrics CSV
        self.metrics_csv = self.processed_dir / "metrics.csv"
        data = {
            'image_id': self.img_ids,
            'entropy': [10.0, 20.0, 5.0],
            'color_variance': [100.0, 200.0, 50.0],
            'object_count': [0, 1, 5]  # First two are neutral (< 2), third is not
        }
        df = pd.DataFrame(data)
        df.to_csv(self.metrics_csv, index=False)

        # Patch the config paths to use our temp dir
        self.patcher_data_dir = patch('src.experiment.curate_neural.DATA_DIR', Path(self.test_dir))
        self.patcher_metrics_path = patch('src.experiment.curate_neutral.METRICS_CSV_PATH', self.metrics_csv)
        self.patcher_raw_dir = patch('src.experiment.curate_neutral.RAW_STIMULI_DIR', self.raw_dir)
        self.patcher_neutral_dir = patch('src.experiment.curate_neutral.NEUTRAL_STIMULI_DIR', self.neutral_dir)
        self.patcher_manifest_path = patch('src.experiment.curate_neutral.NEUTRAL_MANIFEST_PATH', self.processed_dir / "neutral_manifest.json")
        
        self.patcher_data_dir.start()
        self.patcher_metrics_path.start()
        self.patcher_raw_dir.start()
        self.patcher_neutral_dir.start()
        self.patcher_manifest_path.start()

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        self.patcher_data_dir.stop()
        self.patcher_metrics_path.stop()
        self.patcher_metrics_path.stop()
        self.patcher_raw_dir.stop()
        self.patcher_neutral_dir.stop()
        self.patcher_manifest_path.stop()

    def test_load_metrics_success(self):
        """Test that load_metrics correctly reads the CSV."""
        df = load_metrics()
        self.assertEqual(len(df), 3)
        self.assertIn('object_count', df.columns)

    def test_load_metrics_missing_file(self):
        """Test that load_metrics raises FileNotFoundError if CSV missing."""
        with patch('src.experiment.curate_neutral.METRICS_CSV_PATH', Path("/nonexistent.csv")):
            with self.assertRaises(FileNotFoundError):
                load_metrics()

    def test_filter_neutral_stimuli(self):
        """Test filtering logic: object_count < 2."""
        df = load_metrics()
        neutral_items = filter_neutral_stimuli(df)
        
        # Should have 2 items (0 and 1)
        self.assertEqual(len(neutral_items), 2)
        
        # Verify object counts
        counts = [item['object_count'] for item in neutral_items]
        self.assertIn(0, counts)
        self.assertIn(1, counts)
        self.assertNotIn(5, counts)

    def test_filter_neutral_stimuli_empty(self):
        """Test filtering when no items meet criteria."""
        # Create a DF where all have high object count
        bad_data = pd.DataFrame({
            'image_id': ['img_bad'],
            'object_count': [10]
        })
        with patch('src.experiment.curate_neutral.METRICS_CSV_PATH', Path("/fake.csv")):
            # We can't easily mock the file read inside filter_neutral_stimuli without more patching,
            # so we test the logic directly on a DataFrame
            # Re-using the function logic but passing a fake DF
            # Actually, filter_neutral_stimuli takes a DF, so we can just pass one.
            result = filter_neutral_stimuli(bad_data)
            self.assertEqual(len(result), 0)

    def test_copy_stimuli_to_neutral(self):
        """Test that neutral images are copied to the correct directory."""
        df = load_metrics()
        neutral_items = filter_neutral_stimuli(df)
        
        copy_stimuli_to_neutral(neutral_items)
        
        self.assertTrue(self.neutral_dir.exists())
        # Should have copied 2 images
        copied_files = list(self.neutral_dir.glob("*.jpg"))
        self.assertEqual(len(copied_files), 2)

    def test_save_manifest(self):
        """Test that manifest is saved correctly."""
        df = load_metrics()
        neutral_items = filter_neutral_stimuli(df)
        
        save_manifest(neutral_items)
        
        manifest_path = self.processed_dir / "neutral_manifest.json"
        self.assertTrue(manifest_path.exists())
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        self.assertEqual(manifest['count'], 2)
        self.assertIn('items', manifest)
        self.assertEqual(manifest['criteria'], "object_count < 2")

    def test_curate_neutral_stimuli_categorized(self):
        """
        Verification test for T032d: 
        Asserts that the neutral stimuli are correctly categorized and saved.
        """
        # Run the full curation logic
        df = load_metrics()
        neutral_items = filter_neutral_stimuli(df)
        copy_stimuli_to_neutral(neutral_items)
        save_manifest(neutral_items)

        # Assertions
        # 1. Check directory exists
        self.assertTrue(self.neutral_dir.exists(), "Neutral stimuli directory should exist")

        # 2. Check files exist
        neutral_files = list(self.neutral_dir.glob("*"))
        self.assertGreater(len(neutral_files), 0, "Neutral stimuli directory should contain files")

        # 3. Check manifest content
        manifest_path = self.processed_dir / "neutral_manifest.json"
        self.assertTrue(manifest_path.exists(), "Manifest file should exist")
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Verify that all items in manifest have object_count < 2
        for item in manifest['items']:
            self.assertLess(
                item['object_count'], 
                2, 
                f"Item {item['image_id']} should have object_count < 2"
            )

        # 4. Verify file count matches manifest count
        self.assertEqual(
            len(neutral_files), 
            manifest['count'], 
            "Number of copied files should match manifest count"
        )


if __name__ == '__main__':
    unittest.main()