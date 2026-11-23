"""
Unit tests for the batched salience generation module.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path if running standalone, but in project context:
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion.salience_batcher import (
    load_image_paths_from_metadata,
    process_single_image_batch,
    run_batched_salience_generation,
    DEFAULT_BATCH_SIZE
)
from ingestion.salience_gen import SalienceResult


class TestSalienceBatcher(unittest.TestCase):

    def setUp(self):
        """Set up temporary directories and mock data."""
        self.temp_dir = tempfile.mkdtemp()
        self.metadata_path = Path(self.temp_dir) / "metadata.json"
        self.output_dir = Path(self.temp_dir) / "output"
        self.output_dir.mkdir()

        # Create mock metadata
        self.mock_data = [
            {
                "image_id": "img_001",
                "image_path": str(Path(self.temp_dir) / "img_001.jpg"),
                "map_path": None  # Needs processing
            },
            {
                "image_id": "img_002",
                "image_path": str(Path(self.temp_dir) / "img_002.jpg"),
                "map_path": str(Path(self.temp_dir) / "existing_map.npy")  # Already exists
            }
        ]

        with open(self.metadata_path, 'w') as f:
            json.dump(self.mock_data, f)

        # Create dummy image files (empty) to avoid file not found errors
        Path(self.temp_dir, "img_001.jpg").touch()
        Path(self.temp_dir, "existing_map.npy").touch()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('ingestion.salience_batcher.get_paths')
    def test_load_image_paths_from_metadata(self, mock_get_paths):
        """Test loading pending images from metadata."""
        # Test with valid metadata
        pending = load_image_paths_from_metadata(self.metadata_path)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]['image_id'], 'img_001')

        # Test with non-existent file
        pending_empty = load_image_paths_from_metadata(Path("/nonexistent.json"))
        self.assertEqual(len(pending_empty), 0)

    @patch('ingestion.salience_batcher.load_deepgaze_model')
    @patch('ingestion.salience_batcher.process_image_with_monitoring')
    def test_process_single_image_batch_success(self, mock_process, mock_load_model):
        """Test successful processing of a single image."""
        # Mock model
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model

        # Mock successful result
        mock_result = SalienceResult(
            success=True,
            map_path="/fake/path.npy",
            method="DeepGaze",
            image_path="/fake/image.jpg"
        )
        mock_process.return_value = mock_result

        item = {
            "image_id": "test_img",
            "image_path": "/fake/image.jpg"
        }

        image_id, result, error = process_single_image_batch(item, mock_model)

        self.assertEqual(image_id, "test_img")
        self.assertTrue(result.success)
        self.assertIsNone(error)

    @patch('ingestion.salience_batcher.load_deepgaze_model')
    @patch('ingestion.salience_batcher.process_image_with_monitoring')
    @patch('ingestion.salience_batcher.run_gvs')
    def test_process_single_image_batch_fallback(self, mock_gvs, mock_process, mock_load_model):
        """Test fallback to GBVS when DeepGaze fails."""
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model

        # DeepGaze fails
        mock_process.return_value = SalienceResult(
            success=False,
            map_path=None,
            method="DeepGaze",
            image_path="/fake/image.jpg"
        )

        # GBVS succeeds (returning a path string as per implementation assumption)
        mock_gvs.return_value = "/fake/gvs_map.npy"

        item = {
            "image_id": "test_img",
            "image_path": "/fake/image.jpg"
        }

        image_id, result, error = process_single_image_batch(item, mock_model)

        self.assertEqual(image_id, "test_img")
        self.assertIsNotNone(result)
        self.assertTrue(result.get('success') if isinstance(result, dict) else result.success)
        self.assertIsNone(error)

    @patch('ingestion.salience_batcher.get_paths')
    @patch('ingestion.salience_batcher.load_image_paths_from_metadata')
    @patch('ingestion.salience_batcher.process_single_image_batch')
    def test_run_batched_salience_generation(self, mock_process, mock_load_meta, mock_get_paths):
        """Test the main batched generation loop."""
        # Mock paths
        mock_paths = MagicMock()
        mock_paths.processed = Path(self.temp_dir)
        mock_paths.interim = Path(self.temp_dir)
        mock_get_paths.return_value = mock_paths

        # Mock metadata loading
        mock_load_meta.return_value = [
            {"image_id": "img_1", "image_path": "fake1.jpg"},
            {"image_id": "img_2", "image_path": "fake2.jpg"}
        ]

        # Mock processing results
        mock_result = {
            "success": True,
            "map_path": "fake_map.npy",
            "method": "DeepGaze"
        }
        mock_process.return_value = ("img_1", mock_result, None)

        # Run the function
        report = run_batched_salience_generation(
            metadata_path=self.metadata_path,
            batch_size=2,
            use_multiprocessing=False
        )

        self.assertEqual(report['status'], 'completed')
        self.assertEqual(report['processed'], 2)
        self.assertEqual(report['failed'], 0)
        self.assertIn('duration_seconds', report)


if __name__ == '__main__':
    unittest.main()
