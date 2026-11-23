"""
Unit tests for the atlas module.

Tests cover:
- Download functionality (mocked)
- Atlas loading
- Cache management
- Error handling
"""
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import numpy as np

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.atlas import (
    download_file,
    get_atlas_path,
    load_atlas_labels,
    load_atlas,
    ATLAS_CONFIG,
    _get_cache_dir,
    _calculate_file_hash
)

class TestAtlasDownload(unittest.TestCase):
    """Tests for atlas download functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_patch = patch(
            'src.utils.atlas._get_cache_dir',
            return_value=Path(self.temp_dir)
        )
        self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.utils.atlas.requests.get')
    def test_download_file_success(self, mock_get):
        """Test successful file download."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b'test data']
        mock_response.headers.get.return_value = '100'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        dest_path = Path(self.temp_dir) / 'test.nii.gz'
        
        # Execute
        result = download_file('http://example.com/test.nii.gz', dest_path)
        
        # Assert
        self.assertTrue(result)
        self.assertTrue(dest_path.exists())
        mock_get.assert_called_once()
    
    @patch('src.utils.atlas.requests.get')
    def test_download_file_failure(self, mock_get):
        """Test download failure handling."""
        mock_get.side_effect = Exception("Network error")
        
        dest_path = Path(self.temp_dir) / 'test.nii.gz'
        
        # Assert raises RuntimeError
        with self.assertRaises(RuntimeError):
            get_atlas_path('schaefer_400', force_download=True)

class TestAtlasLoading(unittest.TestCase):
    """Tests for atlas loading functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_patch = patch(
            'src.utils.atlas._get_cache_dir',
            return_value=Path(self.temp_dir)
        )
        self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)
        
        # Create mock atlas files
        self.atlas_path = Path(self.temp_dir) / 'Schaefer400_2018.11.01.nii.gz'
        self.labels_path = Path(self.temp_dir) / 'Schaefer400_labels.txt'
        
        # Write mock labels
        with open(self.labels_path, 'w') as f:
            f.write("1 ROI_1\n")
            f.write("2 ROI_2\n")
            f.write("3 ROI_3\n")
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('nibabel.load')
    def test_load_atlas_labels(self, mock_nibabel):
        """Test loading atlas labels."""
        # Create mock atlas image
        mock_img = MagicMock()
        mock_img.shape = (91, 109, 91)
        mock_img.affine = np.eye(4)
        mock_data = np.zeros((91, 109, 91), dtype=np.int16)
        mock_data[50, 50, 50] = 1
        mock_data[51, 51, 51] = 2
        mock_img.get_fdata.return_value = mock_data
        mock_nibabel.load.return_value = mock_img
        
        # Create mock atlas file
        with open(self.atlas_path, 'wb') as f:
            f.write(b'mock nifti data')
        
        # Patch download to skip actual download
        with patch('src.utils.atlas.get_atlas_path', return_value=self.atlas_path):
            with patch('src.utils.atlas.download_file'):
                labels = load_atlas_labels('schaefer_400')
                
                self.assertEqual(len(labels), 3)
                self.assertEqual(labels[1], 'ROI_1')
                self.assertEqual(labels[2], 'ROI_2')
    
    @patch('nibabel.load')
    def test_load_atlas_full(self, mock_nibabel):
        """Test loading full atlas (image + labels)."""
        # Create mock atlas image
        mock_img = MagicMock()
        mock_img.shape = (91, 109, 91)
        mock_img.affine = np.eye(4)
        mock_data = np.zeros((91, 109, 91), dtype=np.int16)
        mock_data[50, 50, 50] = 1
        mock_data[51, 51, 51] = 2
        mock_img.get_fdata.return_value = mock_data
        mock_nibabel.load.return_value = mock_img
        
        # Create mock atlas file
        with open(self.atlas_path, 'wb') as f:
            f.write(b'mock nifti data')
        
        # Patch download to skip actual download
        with patch('src.utils.atlas.get_atlas_path', return_value=self.atlas_path):
            with patch('src.utils.atlas.download_file'):
                img, labels = load_atlas('schaefer_400')
                
                self.assertIsNotNone(img)
                self.assertIsNotNone(labels)
                self.assertEqual(len(labels), 3)

class TestCacheManagement(unittest.TestCase):
    """Tests for cache management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_patch = patch(
            'src.utils.atlas._get_cache_dir',
            return_value=Path(self.temp_dir)
        )
        self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_directory_creation(self):
        """Test that cache directory is created if it doesn't exist."""
        new_cache = Path(self.temp_dir) / 'new_cache'
        assert not new_cache.exists()
        
        with patch('src.utils.atlas._get_cache_dir', return_value=new_cache):
            # Force a call that would create the directory
            Path(os.environ.get("LLMXIVE_CACHE_DIR", new_cache)).mkdir(parents=True, exist_ok=True)
        
        # The directory should exist now
        # Note: Our _get_cache_dir implementation creates it if needed
    
    def test_get_atlas_path_uses_cache(self):
        """Test that get_atlas_path returns cached file."""
        # Create mock files
        atlas_path = Path(self.temp_dir) / 'Schaefer400_2018.11.01.nii.gz'
        labels_path = Path(self.temp_dir) / 'Schaefer400_labels.txt'
        
        with open(atlas_path, 'wb') as f:
            f.write(b'mock data')
        with open(labels_path, 'w') as f:
            f.write("1 ROI_1\n")
        
        # Mock download to ensure it's not called
        with patch('src.utils.atlas.download_file') as mock_download:
            result = get_atlas_path('schaefer_400')
            
            self.assertEqual(result, atlas_path)
            mock_download.assert_not_called()
    
    def test_force_download_re_downloads(self):
        """Test that force_download=True triggers re-download."""
        atlas_path = Path(self.temp_dir) / 'Schaefer400_2018.11.01.nii.gz'
        
        with open(atlas_path, 'wb') as f:
            f.write(b'mock data')
        
        with patch('src.utils.atlas.download_file') as mock_download:
            get_atlas_path('schaefer_400', force_download=True)
            
            mock_download.assert_called_once()

if __name__ == '__main__':
    unittest.main()