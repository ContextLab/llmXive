"""
Unit tests for Millennium-II data fetcher (T029).
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

# Import the module under test
# Note: We mock the actual network calls and file system writes
from ingestion.millennium_loader import (
    attempt_fetch_millennium_url,
    log_gap_to_metadata,
    fetch_millennium_data,
    log_gap_to_metadata
)
from utils.config import get_project_root


class TestMillenniumLoader:
    
    def test_attempt_fetch_millennium_url_success(self):
        """Test successful fetch simulation."""
        with patch('ingestion.millennium_loader.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [b"fake data"]
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            with tempfile.TemporaryDirectory() as tmpdir:
                save_path = Path(tmpdir) / "test_file.tar.gz"
                result = attempt_fetch_millennium_url("http://fake.url/file.tar.gz", save_path)
                
                assert result is True
                assert save_path.exists()
                assert save_path.stat().st_size > 0

    def test_attempt_fetch_millennium_url_failure(self):
        """Test failed fetch simulation (timeout/error)."""
        with patch('ingestion.millennium_loader.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection timeout")

            with tempfile.TemporaryDirectory() as tmpdir:
                save_path = Path(tmpdir) / "test_file.tar.gz"
                result = attempt_fetch_millennium_url("http://fake.url/file.tar.gz", save_path)
                
                assert result is False
                assert not save_path.exists()

    def test_log_gap_to_metadata(self):
        """Test that gap logging updates metadata correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_dir = root / "data"
            data_dir.mkdir()
            metadata_path = data_dir / "metadata.yaml"

            # Create initial metadata
            initial_data = {
                "project": {"name": "Test", "version": "1.0"},
                "success_criteria": {
                    "SC-004": "Pending"
                }
            }
            with open(metadata_path, 'w') as f:
                yaml.dump(initial_data, f)

            # Mock get_project_root to return our temp dir
            with patch('ingestion.millennium_loader.get_project_root', return_value=root):
                log_gap_to_metadata("Test gap message", "test_gap_id")

            # Verify updates
            with open(metadata_path, 'r') as f:
                updated_data = yaml.safe_load(f)

            assert updated_data["success_criteria"]["SC-004"]["status"] == "Not Measurable"
            assert "Test gap message" in updated_data["success_criteria"]["SC-004"]["details"]
            assert "test_gap_id" in updated_data["sources"]
            assert updated_data["sources"]["test_gap_id"]["status"] == "failed"

    @patch('ingestion.millennium_loader.get_project_root')
    @patch('ingestion.millennium_loader.get_data_raw_path')
    def test_fetch_millennium_data_all_fail(self, mock_raw_path, mock_root):
        """Test scenario where all Millennium fetch attempts fail."""
        mock_root.return_value = Path("/fake/root")
        mock_raw_path.return_value = Path("/fake/root/data/raw")
        
        with patch('ingestion.millennium_loader.attempt_fetch_millennium_url', return_value=False):
            with patch('ingestion.millennium_loader.log_gap_to_metadata') as mock_log:
                result = fetch_millennium_data()
                
                assert result["status"] == "failed"
                assert result["success_count"] == 0
                assert len(result["failed_urls"]) > 0
                mock_log.assert_called_once()
    
    @patch('ingestion.millennium_loader.get_project_root')
    @patch('ingestion.millennium_loader.get_data_raw_path')
    def test_fetch_millennium_data_partial_success(self, mock_raw_path, mock_root):
        """Test scenario where some fetches succeed."""
        mock_root.return_value = Path("/fake/root")
        mock_raw_path.return_value = Path("/fake/root/data/raw")
        
        call_count = 0
        def mock_fetch_side_effect(*args):
            nonlocal call_count
            call_count += 1
            return call_count == 1 # First one succeeds

        with patch('ingestion.millennium_loader.attempt_fetch_millennium_url', side_effect=mock_fetch_side_effect):
            with patch('ingestion.millennium_loader.log_gap_to_metadata') as mock_log:
                result = fetch_millennium_data()
                
                # Should not log gap if at least one succeeded
                assert result["status"] == "success"
                assert result["success_count"] > 0
                mock_log.assert_not_called()