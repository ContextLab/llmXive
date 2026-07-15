"""
Tests for T014: Fetch Real Stimuli (Pilot)

Note: These tests verify the logic of the script. 
Since fetching real data from HuggingFace can be slow and requires network,
we mock the dataset loading and image handling for unit tests.
Integration tests (T014_integration) would run the script against real data.
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.metrics.fetch_stimuli import fetch_stimuli, ensure_directory, PILOT_DIR

class TestFetchStimuli:
    
    @patch('src.metrics.fetch_stimuli.load_dataset')
    @patch('src.metrics.fetch_stimuli.Image')
    def test_fetch_stimuli_downloads_correct_count(self, mock_pil, mock_load_dataset):
        """Test that the function attempts to download the correct number of items."""
        # Mock dataset
        mock_item = MagicMock()
        mock_item.get.return_value = MagicMock(mode='RGB', save=MagicMock())
        mock_dataset = [mock_item] * 5
        mock_load_dataset.return_value = mock_dataset

        # Mock ensure_directory to avoid actual file creation during test
        with patch('src.metrics.fetch_stimuli.ensure_directory'):
            with patch('src.metrics.fetch_stimuli.PILOT_DIR', Path(tempfile.gettempdir())):
                count = fetch_stimuli(target_count=5)
                
        assert count == 5
        mock_load_dataset.assert_called_once_with(
            'HuggingFaceM4/video-conference-backgrounds',
            split='train',
            trust_remote_code=True
        )

    @patch('src.metrics.fetch_stimuli.load_dataset')
    def test_fetch_stimuli_handles_empty_dataset(self, mock_load_dataset):
        """Test handling of an empty dataset."""
        mock_load_dataset.return_value = []
        
        with patch('src.metrics.fetch_stimuli.ensure_directory'):
            with patch('src.metrics.fetch_stimuli.PILOT_DIR', Path(tempfile.gettempdir())):
                count = fetch_stimuli(target_count=5)
                
        assert count == 0

    @patch('src.metrics.fetch_stimuli.load_dataset')
    def test_fetch_stimuli_skips_missing_image_key(self, mock_load_dataset):
        """Test that items without 'image' key are skipped."""
        mock_item_no_image = {'other_key': 'value'}
        mock_dataset = [mock_item_no_image] * 3
        mock_load_dataset.return_value = mock_dataset

        with patch('src.metrics.fetch_stimuli.ensure_directory'):
            with patch('src.metrics.fetch_stimuli.PILOT_DIR', Path(tempfile.gettempdir())):
                count = fetch_stimuli(target_count=3)
                
        assert count == 0
        
    @patch('src.metrics.fetch_stimuli.load_dataset')
    @patch('src.metrics.fetch_stimuli.Image')
    def test_fetch_stimuli_handles_rgba_conversion(self, mock_pil, mock_load_dataset):
        """Test that RGBA images are converted to RGB before saving."""
        mock_img_rgba = MagicMock()
        mock_img_rgb = MagicMock()
        mock_img_rgba.mode = 'RGBA'
        mock_img_rgba.convert.return_value = mock_img_rgb
        
        mock_item = {'image': mock_img_rgba}
        mock_dataset = [mock_item]
        mock_load_dataset.return_value = mock_dataset

        with patch('src.metrics.fetch_stimuli.ensure_directory'):
            with patch('src.metrics.fetch_stimuli.PILOT_DIR', Path(tempfile.gettempdir())):
                count = fetch_stimuli(target_count=1)
                
        assert count == 1
        mock_img_rgba.convert.assert_called_once_with('RGB')

    def test_ensure_directory_creates_path(self):
        """Test that ensure_directory creates the path if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "subdir" / "nested"
            assert not test_path.exists()
            
            ensure_directory(test_path)
            
            assert test_path.exists()
            assert test_path.is_dir()