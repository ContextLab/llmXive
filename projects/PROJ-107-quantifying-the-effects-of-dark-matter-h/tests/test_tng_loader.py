"""
Tests for the TNG-100 Data Fetcher (T011).

These tests verify:
1. API interaction logic (mocked).
2. Checksum verification logic.
3. File handling and directory creation.
"""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import hashlib

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.tng_loader import TNGDownloader, fetch_tng_snapshot_000


class TestTNGDownloader:
    """Unit tests for TNGDownloader class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        tmp = tempfile.mkdtemp()
        yield Path(tmp)
        shutil.rmtree(tmp)

    @pytest.fixture
    def downloader(self, temp_dir):
        """Create a TNGDownloader instance with a temp output dir."""
        return TNGDownloader(api_key="test_key", output_dir=temp_dir)

    def test_init_creates_output_dir(self, temp_dir, downloader):
        """Test that __init__ creates the output directory."""
        assert downloader.output_dir.exists()
        assert downloader.output_dir == temp_dir / "tng-100" / "snapshot-000"

    def test_fetch_page_handles_pagination_params(self, downloader):
        """Test that _fetch_page constructs correct request params."""
        with patch.object(downloader.session, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {'results': [], 'next': None}
            mock_get.return_value = mock_response

            downloader._fetch_page(page=2, limit=50)
            
            call_args = mock_get.call_args
            assert call_args[1]['params']['page'] == 2
            assert call_args[1]['params']['limit'] == 50
            assert call_args[1]['params']['format'] == 'json'

    def test_get_all_halo_files_stops_on_no_next(self, downloader):
        """Test that pagination stops when 'next' is None."""
        with patch.object(downloader, '_fetch_page') as mock_fetch:
            # First call returns results and a 'next' link
            mock_fetch.side_effect = [
                {'results': [{'id': 1}], 'next': 'http://next'},
                {'results': [{'id': 2}], 'next': None}
            ]

            files = downloader.get_all_halo_files()
            
            assert len(files) == 2
            assert mock_fetch.call_count == 2

    def test_get_all_halo_files_stops_on_empty_results(self, downloader):
        """Test that pagination stops when results are empty."""
        with patch.object(downloader, '_fetch_page') as mock_fetch:
            mock_fetch.return_value = {'results': [], 'next': None}

            files = downloader.get_all_halo_files()
            
            assert len(files) == 0
            assert mock_fetch.call_count == 1

    def test_verify_checksum_success(self, downloader, temp_dir):
        """Test successful checksum verification."""
        test_content = b"test data for checksum"
        file_path = temp_dir / "test.hdf5"
        file_path.write_bytes(test_content)
        
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        assert downloader._verify_checksum(file_path, expected_hash) is True

    def test_verify_checksum_failure(self, downloader, temp_dir):
        """Test failed checksum verification."""
        test_content = b"test data"
        file_path = temp_dir / "test.hdf5"
        file_path.write_bytes(test_content)
        
        wrong_hash = "a" * 64
        
        assert downloader._verify_checksum(file_path, wrong_hash) is False

    def test_verify_checksum_no_hash(self, downloader, temp_dir):
        """Test that verification passes if no hash provided (with warning)."""
        test_content = b"test data"
        file_path = temp_dir / "test.hdf5"
        file_path.write_bytes(test_content)
        
        # Should return True but log a warning
        assert downloader._verify_checksum(file_path, None) is True

    def test_download_file_skips_existing_valid(self, downloader, temp_dir, mocker):
        """Test that existing valid files are not re-downloaded."""
        file_info = {'url': 'http://example.com/file.hdf5', 'sha256': 'hash123'}
        file_path = temp_dir / "file.hdf5"
        
        # Create a dummy file
        file_path.write_bytes(b"dummy content")
        
        # Mock the checksum verification to return True
        with patch.object(downloader, '_verify_checksum', return_value=True):
            with patch.object(downloader.session, 'get') as mock_get:
                result = downloader.download_file(file_info)
                
                # Should not call session.get
                mock_get.assert_not_called()
                assert result == file_path

    def test_download_file_retries_on_checksum_fail(self, downloader, temp_dir, mocker):
        """Test that file is re-downloaded if existing checksum fails."""
        file_info = {'url': 'http://example.com/file.hdf5', 'sha256': 'hash123'}
        file_path = temp_dir / "file.hdf5"
        
        # Create a dummy file
        file_path.write_bytes(b"dummy content")
        
        call_count = 0
        def mock_verify(path, hash_val):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return False # First check fails
            return True # Second check (after re-download) passes
        
        with patch.object(downloader, '_verify_checksum', side_effect=mock_verify):
            with patch.object(downloader.session, 'get') as mock_get:
                # Mock response for download
                mock_resp = MagicMock()
                mock_resp.iter_content.return_value = [b"new content"]
                mock_resp.headers.get.return_value = 0
                mock_get.return_value = mock_resp
                
                # Mock unlink to avoid actual file deletion issues in test
                with patch.object(file_path, 'unlink'):
                    result = downloader.download_file(file_info)
                    
                    # Should have called get (download)
                    assert mock_get.called

    def test_run_limits_files(self, downloader, mocker):
        """Test that run respects max_files limit."""
        mock_files = [{'url': f'http://example.com/{i}.hdf5'} for i in range(10)]
        
        with patch.object(downloader, 'get_all_halo_files', return_value=mock_files):
            with patch.object(downloader, 'download_file', return_value=Path("dummy")) as mock_dl:
                downloader.run(max_files=3)
                
                assert mock_dl.call_count == 3

def test_fetch_tng_snapshot_000_function():
    """Test the convenience wrapper function."""
    with patch('ingestion.tng_loader.TNGDownloader') as MockDownloader:
        mock_instance = MagicMock()
        MockDownloader.return_value = mock_instance
        
        fetch_tng_snapshot_000(api_key="key", max_files=5)
        
        MockDownloader.assert_called_once_with(api_key="key")
        mock_instance.run.assert_called_once_with(max_files=5)
