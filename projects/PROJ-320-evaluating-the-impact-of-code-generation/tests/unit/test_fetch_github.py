"""
Unit tests for fetch_github.py (T007)
"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
from code.data.fetch_github import (
    fetch_batch,
    calculate_checksum,
    get_next_repo,
    save_prs_to_raw,
    get_repo_list
)

class TestCalculateChecksum:
    def test_calculate_checksum_deterministic(self):
        """Test that checksum is deterministic."""
        data = "test data"
        checksum1 = calculate_checksum(data)
        checksum2 = calculate_checksum(data)
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex length

    def test_calculate_checksum_unique(self):
        """Test that different data produces different checksums."""
        checksum1 = calculate_checksum("data1")
        checksum2 = calculate_checksum("data2")
        assert checksum1 != checksum2

class TestGetNextRepo:
    def test_get_next_repo_valid(self):
        """Test getting next repo from list."""
        repos = ['a/b', 'c/d', 'e/f']
        assert get_next_repo('a/b', repos) == 'c/d'
        assert get_next_repo('c/d', repos) == 'e/f'

    def test_get_next_repo_last(self):
        """Test getting next repo when at end of list."""
        repos = ['a/b', 'c/d']
        assert get_next_repo('c/d', repos) is None

    def test_get_next_repo_not_found(self):
        """Test getting next repo when current not in list."""
        repos = ['a/b', 'c/d']
        assert get_next_repo('x/y', repos) is None

class TestSavePrsToRaw:
    @patch('code.data.fetch_github.os.makedirs')
    @patch('code.data.fetch_github.open')
    def test_save_prs_creates_files(self, mock_open, mock_makedirs):
        """Test that save_prs_to_raw creates JSON and checksum files."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        prs = [{'id': 1, 'title': 'Test'}]
        path = '/tmp/test.json'
        repo = 'test/repo'
        
        checksum = save_prs_to_raw(prs, path, repo)
        
        # Verify JSON was written
        assert mock_open.call_count >= 1
        # Verify checksum was returned
        assert len(checksum) == 64

class TestFetchBatch:
    @patch('code.data.fetch_github.get_session')
    @patch('code.data.fetch_github.fetch_prs_from_repo')
    def test_fetch_batch_returns_list(self, mock_fetch, mock_session):
        """Test that fetch_batch returns a list of PRs."""
        mock_session.return_value = MagicMock()
        mock_fetch.return_value = [{'id': 1}, {'id': 2}]
        
        result = fetch_batch('test/repo', limit=10, max_retries=3)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]['id'] == 1

    @patch('code.data.fetch_github.get_session')
    @patch('code.data.fetch_github.fetch_prs_from_repo')
    def test_fetch_batch_respects_limit(self, mock_fetch, mock_session):
        """Test that fetch_batch respects the limit."""
        mock_session.return_value = MagicMock()
        mock_fetch.return_value = [{'id': i} for i in range(100)]
        
        result = fetch_batch('test/repo', limit=5, max_retries=3)
        
        assert len(result) == 5

class TestIntegration:
    def test_module_imports(self):
        """Test that all expected public names are importable."""
        from code.data.fetch_github import (
            watchdog_handler,
            setup_watchdog,
            check_watchdog,
            get_session,
            calculate_checksum,
            fetch_prs_from_repo,
            get_next_repo,
            save_prs_to_raw,
            run_batch_fetch,
            main
        )
        # If we get here, imports are successful
        assert True