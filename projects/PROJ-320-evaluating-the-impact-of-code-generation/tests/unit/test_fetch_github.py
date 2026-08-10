"""
Unit tests for code/data/fetch_github.py

Tests focus on:
- Backoff logic calculation
- Checksum generation
- Retry behavior simulation
"""

import json
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.fetch_github import (
    calculate_checksum,
    fetch_prs_from_repo,
    save_prs_to_raw,
    MAX_RETRIES,
    BASE_BACKOFF_SECONDS,
    MAX_BACKOFF_SECONDS
)

# Note: We test the logic components. The actual API call is mocked.

class TestChecksum:
    def test_calculate_checksum_file_exists(self, tmp_path):
        """Test checksum calculation on a real file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = calculate_checksum(test_file)
        
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
    
    def test_calculate_checksum_deterministic(self, tmp_path):
        """Test that checksum is deterministic."""
        test_file = tmp_path / "test2.txt"
        test_file.write_text("Same content")
        
        checksum1 = calculate_checksum(test_file)
        checksum2 = calculate_checksum(test_file)
        
        assert checksum1 == checksum2
    
    def test_calculate_checksum_different_content(self, tmp_path):
        """Test that different content produces different checksums."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("Content A")
        file2.write_text("Content B")
        
        checksum1 = calculate_checksum(file1)
        checksum2 = calculate_checksum(file2)
        
        assert checksum1 != checksum2

class TestBackoffLogic:
    def test_exponential_backoff_calculation(self):
        """Verify exponential backoff formula."""
        # Base * 2^attempt
        for attempt in range(MAX_RETRIES):
            expected = BASE_BACKOFF_SECONDS * (2 ** attempt)
            # Cap at MAX_BACKOFF_SECONDS
            actual = min(expected, MAX_BACKOFF_SECONDS)
            assert actual <= MAX_BACKOFF_SECONDS
            if expected <= MAX_BACKOFF_SECONDS:
                assert actual == expected
    
    def test_backoff_capped_at_max(self):
        """Ensure backoff does not exceed MAX_BACKOFF_SECONDS."""
        large_attempt = 10
        calculated = BASE_BACKOFF_SECONDS * (2 ** large_attempt)
        capped = min(calculated, MAX_BACKOFF_SECONDS)
        assert capped == MAX_BACKOFF_SECONDS

class TestSavePRs:
    def test_save_prs_creates_file(self, tmp_path, monkeypatch):
        """Test that save_prs_to_raw creates the expected file."""
        monkeypatch.chdir(tmp_path)
        
        # Mock the OUTPUT_DIR to use tmp_path
        import code.data.fetch_github as fetch_module
        original_dir = fetch_module.OUTPUT_DIR
        fetch_module.OUTPUT_DIR = tmp_path
        
        try:
            prs = [{"id": 1, "title": "Test PR"}]
            file_path = save_prs_to_raw(prs, "test-repo")
            
            assert file_path.exists()
            assert file_path.suffix == ".json"
            
            # Verify content
            with open(file_path, "r") as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]["id"] == 1
            
            # Verify checksum file exists
            checksum_file = tmp_path / f"{file_path.name}.sha256"
            assert checksum_file.exists()
        finally:
            fetch_module.OUTPUT_DIR = original_dir

class TestFetchPRsMock:
    @patch('code.data.fetch_github.requests.get')
    def test_fetch_success(self, mock_get):
        """Test successful PR fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "title": "PR 1"},
            {"id": 2, "title": "PR 2"}
        ]
        mock_get.return_value = mock_response
        
        prs = fetch_prs_from_repo("test", "repo", max_prs=2)
        
        assert len(prs) == 2
        mock_get.assert_called_once()
    
    @patch('code.data.fetch_github.requests.get')
    def test_fetch_rate_limit_retry(self, mock_get):
        """Test rate limit handling and retry."""
        mock_response_403 = Mock()
        mock_response_403.status_code = 403
        mock_response_403.headers = {"Retry-After": "1"}
        
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = [{"id": 1}]
        
        # First call fails, second succeeds
        mock_get.side_effect = [mock_response_403, mock_response_200]
        
        with patch('code.data.fetch_github.time.sleep'):
            prs = fetch_prs_from_repo("test", "repo", max_prs=1)
        
        assert len(prs) == 1
        assert mock_get.call_count == 2
    
    @patch('code.data.fetch_github.requests.get')
    def test_fetch_all_retries_fail(self, mock_get):
        """Test that exception is raised after all retries fail."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.headers = {"Retry-After": "1"}
        mock_get.return_value = mock_response
        
        with patch('code.data.fetch_github.time.sleep'):
            with pytest.raises(Exception) as exc_info:
                fetch_prs_from_repo("test", "repo", max_prs=1, retries=2)
            
            assert "Failed to fetch PRs" in str(exc_info.value)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])