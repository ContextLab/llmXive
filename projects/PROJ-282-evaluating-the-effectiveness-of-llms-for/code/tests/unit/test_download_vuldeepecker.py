import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add code to path
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data.download_vuldeepecker import (
    compute_sha256,
    download_file,
    extract_zip,
    download_vuldeepecker_python,
    main
)

class TestVulDeePeckerDownload:
    """Tests for VulDeePecker Python dataset download functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_compute_sha256(self, temp_dir):
        """Test SHA256 computation on a known file."""
        test_file = temp_dir / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = compute_sha256(test_file)
        # Known SHA256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected

    @patch('src.data.download_vuldeepecker.requests.get')
    def test_download_file_success(self, mock_get, temp_dir):
        """Test successful file download."""
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"test data"]
        mock_response.headers = {'content-length': '9'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        dest = temp_dir / "downloaded.txt"
        download_file("http://example.com/file", dest)

        assert dest.exists()
        assert dest.read_bytes() == b"test data"
        mock_get.assert_called_once()

    @patch('src.data.download_vuldeepecker.requests.get')
    def test_download_file_failure(self, mock_get, temp_dir):
        """Test download failure raises error."""
        mock_get.side_effect = Exception("Network error")

        dest = temp_dir / "downloaded.txt"
        with pytest.raises(RuntimeError, match="Data fetch failed"):
            download_file("http://example.com/file", dest)

    def test_extract_zip(self, temp_dir):
        """Test zip extraction."""
        import zipfile
        zip_path = temp_dir / "test.zip"
        
        # Create a test zip
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("subdir/file2.txt", "content2")
        
        extract_dir = temp_dir / "extracted"
        extracted = extract_zip(zip_path, extract_dir)
        
        assert len(extracted) == 2
        assert (extract_dir / "file1.txt").exists()
        assert (extract_dir / "subdir" / "file2.txt").exists()

    @patch('src.data.download_vuldeepecker.download_file')
    @patch('src.data.download_vuldeepecker.extract_zip')
    def test_download_vuldeepecker_python_success(self, mock_extract, mock_download, temp_dir):
        """Test full download and extraction flow."""
        # Mock download
        mock_download.return_value = None
        
        # Mock extracted files
        mock_files = [
            temp_dir / "vuldeepecker_python" / "data.csv",
            temp_dir / "vuldeepecker_python" / "code.py"
        ]
        # Create dummy files for the test
        mock_files[0].parent.mkdir(parents=True, exist_ok=True)
        mock_files[0].touch()
        mock_files[1].parent.mkdir(parents=True, exist_ok=True)
        mock_files[1].touch()
        
        mock_extract.return_value = mock_files

        result = download_vuldeepecker_python(temp_dir)

        assert result["status"] == "success"
        assert len(result["files"]) == 2
        assert "data.csv" in result["files"][0] or "code.py" in result["files"][0]
        assert "checksums" in result
        assert len(result["checksums"]) == 2

    def test_main_execution(self, temp_dir, caplog):
        """Test main function execution."""
        # Mock get_project_root to return temp_dir
        with patch('src.data.download_vuldeepecker.get_project_root', return_value=temp_dir):
            # We need to ensure the raw directory exists
            (temp_dir / "data" / "raw").mkdir(parents=True, exist_ok=True)
            
            # Mock the download to avoid network call
            with patch('src.data.download_vuldeepecker.download_vuldeepecker_python') as mock_dl:
                mock_dl.return_value = {
                    "status": "success",
                    "files": ["test.csv"],
                    "checksums": {"test.csv": "abc123"}
                }
                
                # Create the dummy file
                (temp_dir / "data" / "raw" / "vuldeepecker_python").mkdir(parents=True, exist_ok=True)
                (temp_dir / "data" / "raw" / "vuldeepecker_python" / "test.csv").touch()
                
                exit_code = main()
                
                assert exit_code == 0
                assert (temp_dir / "data" / "raw" / "vuldeepecker_python_download_log.json").exists()