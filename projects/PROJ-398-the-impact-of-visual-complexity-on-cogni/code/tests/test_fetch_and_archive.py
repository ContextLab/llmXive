"""
Tests for fetch_and_archive.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(project_root))

from src.metrics.fetch_and_archive import (
    compute_sha256, 
    ensure_output_directory,
    fetch_and_archive_stimuli
)

class TestFetchAndArchive:
    """Test suite for the fetch and archive functionality."""
    
    def test_compute_sha256(self):
        """Test SHA-256 checksum computation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = Path(tmp.name)
        
        try:
            checksum = compute_sha256(tmp_path)
            assert len(checksum) == 64  # SHA-256 hex length
            assert all(c in '0123456789abcdef' for c in checksum)
        finally:
            os.unlink(tmp_path)
    
    def test_ensure_output_directory(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_path = Path(tmp_dir) / "subdir" / "nested"
            assert not test_path.exists()
            
            ensure_output_directory(test_path)
            assert test_path.exists()
            assert test_path.is_dir()
    
    @patch('src.metrics.fetch_and_archive.load_dataset')
    @patch('src.metrics.fetch_and_archive.PIL.Image.open')
    def test_fetch_and_archive_success(self, mock_pil_open, mock_load_dataset):
        """Test successful fetching and archiving of stimuli."""
        # Mock dataset iterator
        mock_item = {
            'id': 'test_001',
            'image': MagicMock()
        }
        mock_dataset_iter = iter([mock_item])
        mock_load_dataset.return_value.__iter__ = lambda self: mock_dataset_iter
        
        # Mock PIL Image
        mock_img = MagicMock()
        mock_pil_open.return_value = mock_img
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            result = fetch_and_archive_stimuli(
                dataset_name="test_dataset",
                split="train",
                max_items=1,
                output_dir=output_dir
            )
            
            assert result["status"] == "success"
            assert result["count"] == 1
            assert (output_dir / "manifest.json").exists()
            
            # Verify manifest content
            with open(output_dir / "manifest.json", 'r') as f:
                manifest = json.load(f)
                assert manifest["dataset_name"] == "test_dataset"
                assert len(manifest["items"]) == 1
    
    def test_skip_if_archive_exists(self):
        """Test that download is skipped if archive already exists."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            manifest_path = output_dir / "manifest.json"
            
            # Create a dummy manifest
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(manifest_path, 'w') as f:
                json.dump({"status": "dummy"}, f)
            
            result = fetch_and_archive_stimuli(
                dataset_name="test",
                split="train",
                max_items=10,
                output_dir=output_dir
            )
            
            assert result["status"] == "skipped"
            assert result["reason"] == "archive_exists"