"""
Tests for Google Earth Engine Authentication (Task T009a).

These tests verify that the authentication logic correctly handles:
1. Missing environment variables.
2. Valid JSON strings.
3. File paths.
4. Malformed JSON.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Mock the ee module before importing ingestion to avoid import errors in test env
# if earthengine-api is not installed or GEE is not configured in the test runner
sys = pytest.importorskip('sys')
sys.modules['ee'] = MagicMock()

from src.data.ingestion import initialize_earth_engine, GEE_CREDENTIALS_ENV_VAR


def test_missing_credentials_env_var(monkeypatch):
    """Test that initialization fails gracefully when env var is missing."""
    # Ensure the env var is not set
    monkeypatch.delenv(GEE_CREDENTIALS_ENV_VAR, raising=False)
    monkeypatch.delenv("GEE_PRIVATE_KEY_PATH", raising=False)

    # Mock ee.ServiceAccountCredentials to track calls
    with patch('src.data.ingestion.ee.ServiceAccountCredentials') as mock_creds:
        with patch('src.data.ingestion.ee.Initialize') as mock_init:
            result = initialize_earth_engine()
            assert result is False
            mock_creds.assert_not_called()
            mock_init.assert_not_called()


def test_valid_json_string_credentials(monkeypatch):
    """Test initialization with a valid JSON string in the env var."""
    fake_key = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key123",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    json_str = json.dumps(fake_key)
    
    monkeypatch.setenv(GEE_CREDENTIALS_ENV_VAR, json_str)

    with patch('src.data.ingestion.ee.ServiceAccountCredentials') as mock_creds:
        with patch('src.data.ingestion.ee.Initialize') as mock_init:
            # Mock the return value of ServiceAccountCredentials
            mock_creds.return_value = MagicMock()
            
            result = initialize_earth_engine()
            
            assert result is True
            mock_creds.assert_called_once()
            mock_init.assert_called_once()


def test_file_path_credentials(monkeypatch):
    """Test initialization when env var points to a valid file."""
    fake_key = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "key123",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----\n",
        "client_email": "test@test-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(fake_key, f)
        temp_path = f.name

    try:
        monkeypatch.setenv(GEE_CREDENTIALS_ENV_VAR, temp_path)
        
        with patch('src.data.ingestion.ee.ServiceAccountCredentials') as mock_creds:
            with patch('src.data.ingestion.ee.Initialize') as mock_init:
                mock_creds.return_value = MagicMock()
                
                result = initialize_earth_engine()
                
                assert result is True
                mock_creds.assert_called_once()
    finally:
        os.remove(temp_path)


def test_invalid_json_string(monkeypatch):
    """Test that initialization fails with invalid JSON string."""
    monkeypatch.setenv(GEE_CREDENTIALS_ENV_VAR, "not a json string {")
    
    # Mock file existence to ensure we don't accidentally fallback to file check
    with patch('os.path.exists', return_value=False):
        with patch('src.data.ingestion.ee.ServiceAccountCredentials') as mock_creds:
            with patch('src.data.ingestion.ee.Initialize') as mock_init:
                result = initialize_earth_engine()
                
                assert result is False
                mock_creds.assert_not_called()
                mock_init.assert_not_called()


def test_file_not_found(monkeypatch):
    """Test that initialization fails if the file path in env var doesn't exist."""
    monkeypatch.setenv(GEE_CREDENTIALS_ENV_VAR, "/nonexistent/path/key.json")
    
    with patch('os.path.exists', return_value=False):
        with patch('src.data.ingestion.ee.ServiceAccountCredentials') as mock_creds:
            with patch('src.data.ingestion.ee.Initialize') as mock_init:
                result = initialize_earth_engine()
                
                assert result is False
                mock_creds.assert_not_called()
                mock_init.assert_not_called()
