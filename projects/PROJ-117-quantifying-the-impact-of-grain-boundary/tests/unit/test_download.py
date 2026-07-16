"""
Unit tests for download modules (T034).

Verifies that:
1. Download scripts log the raw record count.
2. Download scripts do NOT halt on data insufficiency (delegating to T011).
3. No synthetic fallbacks are used when data is missing or API fails.
"""
import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO

import pytest

# Ensure the code directory is in the path for imports
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from download import fetch_materials_project_data, fetch_openkim_data, save_raw_data, main
from error_handling import DataInsufficiencyError
from utils import setup_logging, compute_sha256


class TestDownloadLoggingAndBehavior:
    """Tests for T034: Logging raw counts, no halting, no synthetic fallback."""

    @pytest.fixture
    def mock_api_response(self):
        """Mock a valid API response with grain boundary data."""
        return {
            "data": [
                {
                    "task_id": "mp-123",
                    "structure": {"lattice": [[1,0,0],[0,1,0],[0,0,1]], "sites": []},
                    "properties": {"diffusivity": 1e-10},
                    "keywords": ["grain boundary", "bicrystal"]
                },
                {
                    "task_id": "mp-456",
                    "structure": {"lattice": [[1,0,0],[0,1,0],[0,0,1]], "sites": []},
                    "properties": {"diffusivity": 2e-10},
                    "keywords": ["grain boundary"]
                }
            ],
            "meta": {"total_count": 2}
        }

    @pytest.fixture
    def mock_empty_response(self):
        """Mock an empty API response."""
        return {"data": [], "meta": {"total_count": 0}}

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_fetch_mp_logs_raw_count(self, mock_api_response, temp_dir, caplog):
        """Verify that fetch_materials_project_data logs the raw record count."""
        caplog.set_level(logging.INFO)
        
        with patch("download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_api_response
            mock_get.return_value = mock_response
            
            with patch("download.os.environ", {"MATERIALS_PROJECT_API_KEY": "test_key"}):
                with patch("download.Path") as mock_path:
                    mock_path.return_value = Path(temp_dir)
                    # Mock the save function to avoid actual file writing
                    with patch("download.save_raw_data") as mock_save:
                        fetch_materials_project_data(Path(temp_dir))
        
        # Check that logging occurred
        assert any("raw record count" in msg.lower() for msg in caplog.messages)
        assert any("2" in msg for msg in caplog.messages)

    def test_fetch_mp_no_halt_on_empty(self, mock_empty_response, temp_dir, caplog):
        """Verify that fetch_materials_project_data does NOT halt on empty data."""
        caplog.set_level(logging.INFO)
        
        with patch("download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_empty_response
            mock_get.return_value = mock_response
            
            with patch("download.os.environ", {"MATERIALS_PROJECT_API_KEY": "test_key"}):
                with patch("download.Path") as mock_path:
                    mock_path.return_value = Path(temp_dir)
                    with patch("download.save_raw_data") as mock_save:
                        # Should NOT raise DataInsufficiencyError here
                        fetch_materials_project_data(Path(temp_dir))
        
        # Verify no exception was raised
        # If it raised, the test would fail before reaching this line
        assert True

    def test_fetch_mp_no_synthetic_fallback(self, mock_empty_response, temp_dir):
        """Verify that fetch_materials_project_data does NOT generate synthetic data."""
        with patch("download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_empty_response
            mock_get.return_value = mock_response
            
            with patch("download.os.environ", {"MATERIALS_PROJECT_API_KEY": "test_key"}):
                with patch("download.Path") as mock_path:
                    mock_path.return_value = Path(temp_dir)
                    with patch("download.save_raw_data") as mock_save:
                        fetch_materials_project_data(Path(temp_dir))
        
        # Verify save_raw_data was called with the empty data, not synthetic
        # If synthetic data was generated, save_raw_data would be called with non-empty data
        # We check that the data passed to save_raw_data matches what we got from the API
        assert mock_save.called
        call_args = mock_save.call_args
        data_saved = call_args[0][0]  # First positional argument
        
        # The data should be empty, not synthetic
        assert len(data_saved) == 0

    def test_fetch_kim_logs_raw_count(self, mock_api_response, temp_dir, caplog):
        """Verify that fetch_openkim_data logs the raw record count."""
        caplog.set_level(logging.INFO)
        
        with patch("download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_api_response
            mock_get.return_value = mock_response
            
            with patch("download.os.environ", {"OPENKIM_API_KEY": "test_key"}):
                with patch("download.Path") as mock_path:
                    mock_path.return_value = Path(temp_dir)
                    with patch("download.save_raw_data") as mock_save:
                        fetch_openkim_data(Path(temp_dir))
        
        assert any("raw record count" in msg.lower() for msg in caplog.messages)
        assert any("2" in msg for msg in caplog.messages)

    def test_fetch_kim_no_halt_on_empty(self, mock_empty_response, temp_dir, caplog):
        """Verify that fetch_openkim_data does NOT halt on empty data."""
        caplog.set_level(logging.INFO)
        
        with patch("download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_empty_response
            mock_get.return_value = mock_response
            
            with patch("download.os.environ", {"OPENKIM_API_KEY": "test_key"}):
                with patch("download.Path") as mock_path:
                    mock_path.return_value = Path(temp_dir)
                    with patch("download.save_raw_data") as mock_save:
                        fetch_openkim_data(Path(temp_dir))
        
        assert True

    def test_fetch_kim_no_synthetic_fallback(self, mock_empty_response, temp_dir):
        """Verify that fetch_openkim_data does NOT generate synthetic data."""
        with patch("download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_empty_response
            mock_get.return_value = mock_response
            
            with patch("download.os.environ", {"OPENKIM_API_KEY": "test_key"}):
                with patch("download.Path") as mock_path:
                    mock_path.return_value = Path(temp_dir)
                    with patch("download.save_raw_data") as mock_save:
                        fetch_openkim_data(Path(temp_dir))
        
        assert mock_save.called
        call_args = mock_save.call_args
        data_saved = call_args[0][0]
        assert len(data_saved) == 0

    def test_save_raw_data_creates_checksums(self, temp_dir):
        """Verify that save_raw_data creates files with checksums."""
        test_data = [{"id": "test", "value": 123}]
        
        save_raw_data(test_data, Path(temp_dir), "test_source")
        
        # Check that files were created
        output_dir = Path(temp_dir) / "test_source"
        assert output_dir.exists()
        
        # Check for metadata file with checksum
        metadata_file = output_dir / "metadata.json"
        assert metadata_file.exists()
        
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
        
        assert "checksums" in metadata
        assert "retrieval_date" in metadata
        assert "source" in metadata

    def test_main_delegates_to_fetch_functions(self, temp_dir, caplog):
        """Verify that main() delegates to fetch functions and logs counts."""
        caplog.set_level(logging.INFO)
        
        with patch("download.fetch_materials_project_data") as mock_mp:
            with patch("download.fetch_openkim_data") as mock_kim:
                with patch("download.os.environ", {
                    "MATERIALS_PROJECT_API_KEY": "test",
                    "OPENKIM_API_KEY": "test"
                }):
                    main(Path(temp_dir))
        
        assert mock_mp.called
        assert mock_kim.called

    def test_download_does_not_validate_minimum_count(self, mock_empty_response, temp_dir):
        """Verify that download scripts do NOT enforce n >= 500 (T011 responsibility)."""
        with patch("download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_empty_response
            mock_get.return_value = mock_response
            
            with patch("download.os.environ", {"MATERIALS_PROJECT_API_KEY": "test_key"}):
                with patch("download.Path") as mock_path:
                    mock_path.return_value = Path(temp_dir)
                    with patch("download.save_raw_data") as mock_save:
                        # Should NOT raise DataInsufficiencyError
                        # T011 is responsible for this check
                        result = fetch_materials_project_data(Path(temp_dir))
                        
                        # If we get here without exception, the test passes
                        assert result is None

    def test_download_logs_but_does_not_exit_on_insufficiency(self, mock_empty_response, temp_dir, caplog):
        """Verify that download scripts log insufficiency but do not exit (T011 responsibility)."""
        caplog.set_level(logging.INFO)
        
        with patch("download.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_empty_response
            mock_get.return_value = mock_response
            
            with patch("download.os.environ", {"MATERIALS_PROJECT_API_KEY": "test_key"}):
                with patch("download.Path") as mock_path:
                    mock_path.return_value = Path(temp_dir)
                    with patch("download.save_raw_data") as mock_save:
                        fetch_materials_project_data(Path(temp_dir))
        
        # Should log the count
        assert any("raw record count" in msg.lower() for msg in caplog.messages)
        # Should NOT have logged "Data Insufficiency" or "exiting" (that's T011)
        assert not any("data insufficiency" in msg.lower() and "exiting" in msg.lower() 
                     for msg in caplog.messages)