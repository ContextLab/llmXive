"""
Tests for the dMRI download functionality.

These tests verify that the download module correctly handles:
- URL construction for different subjects
- File existence after download (mocked)
- Error handling for missing files
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.download import (
    get_subject_url,
    download_file,
    process_subject,
    SUBJECTS,
    FILE_TYPES,
    OPENNEURO_DATASET
)

class TestURLConstruction:
    """Test URL construction for different subjects and file types."""
    
    def test_url_construction_dwi(self):
        """Test URL construction for dwi.nii.gz file."""
        url = get_subject_url("sub-001", "dwi.nii.gz")
        assert url is not None
        assert "ds003813" in url
        assert "sub-001" in url
        assert "dwi.nii.gz" in url
    
    def test_url_construction_bvec(self):
        """Test URL construction for bvec file."""
        url = get_subject_url("sub-002", "bvec")
        assert url is not None
        assert "ds003813" in url
        assert "sub-002" in url
        assert "dwi.bvec" in url
    
    def test_url_construction_bval(self):
        """Test URL construction for bval file."""
        url = get_subject_url("sub-010", "bval")
        assert url is not None
        assert "ds003813" in url
        assert "sub-010" in url
        assert "dwi.bval" in url

class TestDownloadFile:
    """Test file download functionality."""
    
    @patch('code.data.download.urlretrieve')
    @patch('code.data.download.Path.exists', return_value=True)
    @patch('code.data.download.Path.stat')
    def test_download_success(self, mock_stat, mock_exists, mock_urlretrieve, tmp_path):
        """Test successful file download."""
        # Setup mocks
        mock_stat.return_value.st_size = 1024
        mock_urlretrieve.return_value = None
        
        target = tmp_path / "test_file.nii.gz"
        success = download_file("http://example.com/test.nii.gz", target)
        
        assert success is True
        mock_urlretrieve.assert_called_once()
    
    @patch('code.data.download.urlretrieve')
    def test_download_http_error_404(self, mock_urlretrieve, tmp_path):
        """Test handling of 404 error."""
        from urllib.error import HTTPError
        
        mock_urlretrieve.side_effect = HTTPError(
            url="http://example.com/test.nii.gz",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None
        )
        
        target = tmp_path / "test_file.nii.gz"
        success = download_file("http://example.com/test.nii.gz", target)
        
        assert success is False
    
    @patch('code.data.download.urlretrieve')
    def test_download_empty_file(self, mock_urlretrieve, tmp_path):
        """Test handling of empty file download."""
        from unittest.mock import MagicMock
        
        mock_stat = MagicMock()
        mock_stat.st_size = 0
        
        with patch('code.data.download.Path.stat', return_value=mock_stat):
            with patch('code.data.download.Path.exists', return_value=True):
                mock_urlretrieve.return_value = None
                
                target = tmp_path / "test_file.nii.gz"
                success = download_file("http://example.com/test.nii.gz", target)
                
                assert success is False

class TestSubjectProcessing:
    """Test subject-level processing."""
    
    def test_subject_list(self):
        """Test that correct subjects are defined."""
        assert len(SUBJECTS) == 10
        assert "sub-001" in SUBJECTS
        assert "sub-010" in SUBJECTS
        assert "sub-011" not in SUBJECTS
    
    def test_file_types(self):
        """Test that all required file types are defined."""
        assert "dwi.nii.gz" in FILE_TYPES
        assert "bvec" in FILE_TYPES
        assert "bval" in FILE_TYPES

class TestIntegration:
    """Integration tests for the download module."""
    
    @patch('code.data.download.get_data_root')
    @patch('code.data.download.ensure_data_directories')
    @patch('code.data.download.ensure_directories')
    def test_main_function_structure(self, mock_ensure_dirs, mock_ensure_data, mock_get_root, tmp_path):
        """Test that main function executes without crashing (mocked)."""
        from code.data.download import main
        
        # Mock the data root
        mock_get_root.return_value = tmp_path
        
        # Run main (should not raise exceptions)
        # Note: This will likely return False since we're not actually downloading
        result = main()
        
        # We expect False since we're not actually downloading real files
        # The important thing is that the function structure is correct
        assert isinstance(result, bool)