"""
Tests for the data download module.
"""

import os
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import requests

from data.download import (
    ensure_directories,
    log_download_attempt,
    fetch_from_pushshift,
    fetch_from_reddit_api,
    fetch_from_internet_archive,
    download_data,
    validate_origin_types
)


class TestEnsureDirectories:
    def test_ensure_directories_creates_folders(self, tmp_path):
        """Test that ensure_directories creates required folders."""
        # Change to temp directory for testing
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            data_raw, data_processed = ensure_directories()
            assert data_raw.exists()
            assert data_processed.exists()
            assert data_raw.name == "raw"
            assert data_processed.name == "processed"
        finally:
            os.chdir(original_cwd)


class TestLogDownloadAttempt:
    def test_log_download_attempt_writes_json(self, tmp_path):
        """Test that log_download_attempt writes valid JSON entries."""
        log_path = tmp_path / "test_log.log"
        
        log_download_attempt(
            log_path=log_path,
            endpoint="test_endpoint",
            status_code=200,
            success=True,
            origin_type="api",
            thread_id="test_thread_123"
        )
        
        assert log_path.exists()
        with open(log_path, 'r') as f:
            line = f.readline()
            entry = json.loads(line)
            
        assert entry['endpoint'] == "test_endpoint"
        assert entry['status_code'] == 200
        assert entry['success'] is True
        assert entry['origin_type'] == "api"
        assert entry['thread_id'] == "test_thread_123"
        assert 'timestamp' in entry


class TestFetchFromPushshift:
    @patch('data.download.requests.get')
    def test_fetch_from_pushshift_success(self, mock_get):
        """Test successful Pushshift fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'id': 'test1', 'title': 'Test 1'},
                {'id': 'test2', 'title': 'Test 2'}
            ]
        }
        mock_get.return_value = mock_response
        
        threads, success = fetch_from_pushshift('testsub', limit=10)
        
        assert success is True
        assert len(threads) == 2
        assert threads[0]['id'] == 'test1'
        
    @patch('data.download.requests.get')
    def test_fetch_from_pushshift_failure(self, mock_get):
        """Test failed Pushshift fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        threads, success = fetch_from_pushshift('nonexistent', limit=10)
        
        assert success is False
        assert len(threads) == 0


class TestFetchFromRedditAPI:
    @patch('data.download.requests.post')
    @patch('data.download.requests.get')
    def test_fetch_from_reddit_api_success(self, mock_get, mock_post):
        """Test successful Reddit API fetch."""
        # Mock OAuth token response
        mock_auth_response = MagicMock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value = mock_auth_response
        
        # Mock subreddit data response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'children': [
                    {'data': {'id': 'test1', 'title': 'Test 1'}},
                    {'data': {'id': 'test2', 'title': 'Test 2'}}
                ]
            }
        }
        mock_get.return_value = mock_response
        
        # Set environment variables
        os.environ['REDDIT_CLIENT_ID'] = 'test_client_id'
        os.environ['REDDIT_CLIENT_SECRET'] = 'test_secret'
        os.environ['REDDIT_USER_AGENT'] = 'test_agent'
        
        threads, success = fetch_from_reddit_api('testsub', limit=10)
        
        assert success is True
        assert len(threads) == 2
        assert threads[0]['id'] == 'test1'
        
        # Cleanup
        del os.environ['REDDIT_CLIENT_ID']
        del os.environ['REDDIT_CLIENT_SECRET']
        del os.environ['REDDIT_USER_AGENT']
        
    def test_fetch_from_reddit_api_no_credentials(self):
        """Test Reddit API fetch without credentials."""
        # Ensure no credentials
        if 'REDDIT_CLIENT_ID' in os.environ:
            del os.environ['REDDIT_CLIENT_ID']
        if 'REDDIT_CLIENT_SECRET' in os.environ:
            del os.environ['REDDIT_CLIENT_SECRET']
        
        threads, success = fetch_from_reddit_api('testsub', limit=10)
        
        assert success is False
        assert len(threads) == 0


class TestFetchFromInternetArchive:
    def test_fetch_from_internet_archive_not_implemented(self):
        """Test that Internet Archive fetch returns empty (not implemented)."""
        threads, success = fetch_from_internet_archive('testsub', limit=10)
        
        assert success is False
        assert len(threads) == 0


class TestValidateOriginTypes:
    def test_validate_origin_types_success(self, tmp_path):
        """Test successful origin type validation."""
        # Create test data with valid origin_type
        raw_data = tmp_path / "raw"
        raw_data.mkdir()
        raw_file = raw_data / "test_threads.jsonl"
        
        threads = [
            {'id': '1', 'title': 'Test 1', 'origin_type': 'api'},
            {'id': '2', 'title': 'Test 2', 'origin_type': 'archive'},
            {'id': '3', 'title': 'Test 3', 'origin_type': 'api'}
        ]
        
        with open(raw_file, 'w') as f:
            for thread in threads:
                f.write(json.dumps(thread) + '\n')
        
        # Create log file
        log_file = tmp_path / "download_attempts.log"
        log_entries = [
            {'timestamp': '2024-01-01', 'endpoint': 'test', 'status_code': 200, 'success': True, 'origin_type': 'api'},
            {'timestamp': '2024-01-01', 'endpoint': 'test', 'status_code': 200, 'success': True, 'origin_type': 'archive'}
        ]
        with open(log_file, 'w') as f:
            for entry in log_entries:
                f.write(json.dumps(entry) + '\n')
        
        result = validate_origin_types(raw_file, log_file)
        assert result is True
        
    def test_validate_origin_types_missing_field(self, tmp_path):
        """Test validation fails when origin_type is missing."""
        raw_data = tmp_path / "raw"
        raw_data.mkdir()
        raw_file = raw_data / "test_threads.jsonl"
        
        threads = [
            {'id': '1', 'title': 'Test 1'},  # Missing origin_type
            {'id': '2', 'title': 'Test 2', 'origin_type': 'api'}
        ]
        
        with open(raw_file, 'w') as f:
            for thread in threads:
                f.write(json.dumps(thread) + '\n')
        
        log_file = tmp_path / "download_attempts.log"
        with open(log_file, 'w') as f:
            f.write(json.dumps({'timestamp': '2024-01-01'}) + '\n')
        
        result = validate_origin_types(raw_file, log_file)
        assert result is False
        
    def test_validate_origin_types_invalid_value(self, tmp_path):
        """Test validation fails when origin_type has invalid value."""
        raw_data = tmp_path / "raw"
        raw_data.mkdir()
        raw_file = raw_data / "test_threads.jsonl"
        
        threads = [
            {'id': '1', 'title': 'Test 1', 'origin_type': 'invalid_type'},
            {'id': '2', 'title': 'Test 2', 'origin_type': 'api'}
        ]
        
        with open(raw_file, 'w') as f:
            for thread in threads:
                f.write(json.dumps(thread) + '\n')
        
        log_file = tmp_path / "download_attempts.log"
        with open(log_file, 'w') as f:
            f.write(json.dumps({'timestamp': '2024-01-01'}) + '\n')
        
        result = validate_origin_types(raw_file, log_file)
        assert result is False