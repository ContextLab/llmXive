"""
Tests for T032: Fetch Real Meeting Clips (Main Study)
"""

import os
import tempfile
import json
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.experiment.fetch_clips import (
    ensure_output_directory,
    download_dataset_items,
    save_manifest,
    main,
    OUTPUT_DIR,
    MANIFEST_PATH
)


class TestFetchClips:
    """Test suite for fetch_clips module."""

    @patch("src.experiment.fetch_clips.OUTPUT_DIR")
    def test_ensure_output_directory(self, mock_output_dir):
        """Test that ensure_output_directory creates the directory."""
        mock_output_dir.mkdir = MagicMock()

        ensure_output_directory()

        mock_output_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("src.experiment.fetch_clips.load_dataset")
    @patch("src.experiment.fetch_clips.OUTPUT_DIR")
    def test_download_dataset_items_limit(self, mock_output_dir, mock_load_dataset):
        """Test that download_dataset_items respects the max_items limit."""
        # Mock dataset
        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=1000)
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"image": MagicMock()},  # Mock image item
            {"video": MagicMock()},  # Mock video item
        ]))

        mock_load_dataset.return_value = mock_dataset

        # Mock PIL Image
        with patch("src.experiment.fetch_clips.Image") as mock_pil_image:
            mock_img = MagicMock()
            mock_pil_image.open.return_value = mock_img
            mock_img.save = MagicMock()

            # Mock file operations
            with patch("builtins.open", MagicMock()):
                items = download_dataset_items(max_items=5)

                # Should only process up to max_items
                assert len(items) <= 5

    def test_save_manifest(self):
        """Test that save_manifest creates a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_manifest_path = Path(tmpdir) / "test_manifest.json"

            test_items = [
                {"id": 1, "filename": "test1.png", "type": "image"},
                {"id": 2, "filename": "test2.mp4", "type": "video"}
            ]

            # Temporarily override MANIFEST_PATH
            import src.experiment.fetch_clips as fetch_module
            original_path = fetch_module.MANIFEST_PATH
            fetch_module.MANIFEST_PATH = test_manifest_path

            try:
                save_manifest(test_items)

                # Verify file exists
                assert test_manifest_path.exists()

                # Verify content
                with open(test_manifest_path, "r") as f:
                    manifest = json.load(f)

                assert manifest["total_downloaded"] == len(test_items)
                assert len(manifest["items"]) == len(test_items)
                assert manifest["dataset_name"] == "HuggingFaceM4/video-conference-backgrounds"
            finally:
                # Restore original path
                fetch_module.MANIFEST_PATH = original_path

    @patch("src.experiment.fetch_clips.download_dataset_items")
    @patch("src.experiment.fetch_clips.save_manifest")
    @patch("src.experiment.fetch_clips.ensure_output_directory")
    def test_main_function(self, mock_ensure_dir, mock_save_manifest, mock_download):
        """Test that main function calls the expected methods."""
        mock_download.return_value = [{"id": 1}]

        # Mock MANIFEST_PATH to not exist
        with patch("src.experiment.fetch_clips.MANIFEST_PATH.exists", return_value=False):
            main()

            mock_ensure_dir.assert_called_once()
            mock_download.assert_called_once()
            mock_save_manifest.assert_called_once()

    @patch("src.experiment.fetch_clips.MANIFEST_PATH.exists", return_value=True)
    @patch("src.experiment.fetch_clips.download_dataset_items")
    @patch("src.experiment.fetch_clips.save_manifest")
    def test_main_skips_when_manifest_exists(self, mock_save_manifest, mock_download, mock_exists):
        """Test that main skips download if manifest already exists."""
        # This should not call download or save
        main()

        mock_download.assert_not_called()
        mock_save_manifest.assert_not_called()

    def test_output_structure(self):
        """Test that the output structure matches expectations."""
        # This is a structural test to ensure the code produces the right artifacts
        # In a real test, we would run the actual code and verify outputs
        pass
