import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from data_loader import fetch_dragmesh_manifest, get_manifest_checksum, ensure_dirs, MANIFEST_PATH

class TestDragMeshFetcher:
    """Tests for the DragMesh-2 data fetcher and verification logic."""

    def test_ensure_dirs_creates_directory(self, tmp_path):
        """Test that ensure_dirs creates the required directory structure."""
        # Mock the DATA_RAW_DIR to point to a temp directory
        with patch('data_loader.DATA_RAW_DIR', tmp_path):
            ensure_dirs()
            assert tmp_path.exists()

    def test_fetch_manifest_raises_on_missing_dataset(self):
        """Test that fetch_dragmesh_manifest raises ConnectionError if dataset is missing."""
        with patch('data_loader.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Dataset not found")
            
            with pytest.raises(ConnectionError):
                fetch_dragmesh_manifest()

    def test_fetch_manifest_raises_on_empty_manifest(self):
        """Test that fetch_dragmesh_manifest raises FileNotFoundError if manifest is empty."""
        with patch('data_loader.HfApi') as MockApi:
            mock_api_instance = MagicMock()
            MockApi.return_value = mock_api_instance
            mock_api_instance.list_repo_files.return_value = ["manifest.json"]
            
            with patch('data_loader.hf_hub_download') as mock_download:
                # Create a temporary empty file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                    f.write("")
                    temp_path = f.name
                
                mock_download.return_value = temp_path
                
                try:
                    with pytest.raises(FileNotFoundError) as exc_info:
                        fetch_dragmesh_manifest()
                    assert "empty" in str(exc_info.value).lower()
                finally:
                    os.unlink(temp_path)

    def test_fetch_manifest_returns_valid_data(self):
        """Test that fetch_dragmesh_manifest returns a valid dictionary when successful."""
        mock_manifest = {"version": "2.0", "objects": 100, "source": "DragMesh-2"}
        
        with patch('data_loader.HfApi') as MockApi:
            mock_api_instance = MagicMock()
            MockApi.return_value = mock_api_instance
            mock_api_instance.list_repo_files.return_value = ["manifest.json"]
            
            with patch('data_loader.hf_hub_download') as mock_download:
                # Create a temporary file with valid JSON
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                    json.dump(mock_manifest, f)
                    temp_path = f.name
                
                mock_download.return_value = temp_path
                
                try:
                    result = fetch_dragmesh_manifest()
                    assert isinstance(result, dict)
                    assert result["version"] == "2.0"
                    assert result["source"] == "DragMesh-2"
                finally:
                    os.unlink(temp_path)

    def test_get_manifest_checksum_raises_on_missing_file(self, tmp_path):
        """Test that get_manifest_checksum raises FileNotFoundError if file is missing."""
        missing_path = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            get_manifest_checksum(missing_path)

    def test_get_manifest_checksum_returns_valid_hash(self, tmp_path):
        """Test that get_manifest_checksum returns a valid SHA256 hash."""
        test_file = tmp_path / "test.json"
        content = '{"test": "data"}'
        test_file.write_text(content)
        
        checksum = get_manifest_checksum(test_file)
        assert len(checksum) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
