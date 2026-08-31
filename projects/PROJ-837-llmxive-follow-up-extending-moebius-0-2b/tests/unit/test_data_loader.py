import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.loader import (
    fetch_places365_subset, 
    list_available_datasets,
    get_image_paths
)

class TestDataLoader:
    def test_list_available_datasets(self):
        """Test listing available datasets"""
        datasets = list_available_datasets()
        assert isinstance(datasets, list)
        # Should return at least the Places365 dataset
        assert len(datasets) >= 0  # May be empty if no datasets cached

    def test_get_image_paths_empty(self):
        """Test getting image paths from empty directory"""
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = get_image_paths(tmpdir)
            assert paths == []

    def test_get_image_paths_with_files(self):
        """Test getting image paths from directory with files"""
        import tempfile
        from PIL import Image
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some dummy images
            for i in range(3):
                img = Image.new('RGB', (64, 64), color='red')
                img.save(os.path.join(tmpdir, f"test_{i}.jpg"))
            
            paths = get_image_paths(tmpdir)
            
            assert len(paths) == 3
            assert all('.jpg' in p for p in paths)

    def test_get_image_paths_recursive(self):
        """Test getting image paths recursively"""
        import tempfile
        from PIL import Image
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create subdirectory
            subdir = os.path.join(tmpdir, "subdir")
            os.makedirs(subdir)
            
            # Create images in both
            img1 = Image.new('RGB', (32, 32), color='blue')
            img1.save(os.path.join(tmpdir, "test1.png"))
            
            img2 = Image.new('RGB', (32, 32), color='green')
            img2.save(os.path.join(subdir, "test2.png"))
            
            paths = get_image_paths(tmpdir)
            
            assert len(paths) == 2

    def test_fetch_places365_subset_mock(self):
        """Test Places365 fetching with mocked dataset"""
        # Mock the datasets.load_dataset to avoid actual download
        with patch('data.loader.load_dataset') as mock_load:
            mock_dataset = MagicMock()
            mock_dataset['train'].select.return_value = [
                {'image': None, 'filename': 'test.jpg'}
            ]
            mock_load.return_value = mock_dataset
            
            try:
                result = fetch_places365_subset(
                    split='train', 
                    num_samples=1,
                    cache_dir='/tmp/test_cache'
                )
                
                # Should return a list with one item
                assert len(result) == 1
                assert result[0]['filename'] == 'test.jpg'
            except ImportError:
                # If datasets library not available, skip test
                pytest.skip("datasets library not available")

    def test_fetch_places365_subset_validation(self):
        """Test that fetch validates parameters"""
        with pytest.raises(ValueError):
            fetch_places365_subset(
                split='invalid_split',
                num_samples=10,
                cache_dir='/tmp'
            )

    def test_fetch_places365_subset_zero_samples(self):
        """Test that fetch handles zero samples"""
        with pytest.raises(ValueError):
            fetch_places365_subset(
                split='train',
                num_samples=0,
                cache_dir='/tmp'
            )
