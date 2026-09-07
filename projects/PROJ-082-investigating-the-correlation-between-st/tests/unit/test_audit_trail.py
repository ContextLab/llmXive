"""
Unit tests for the audit_trail module (T076).
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We need to mock the project root to avoid needing the full project structure
# during unit tests.
@pytest.fixture
def temp_audit_dir():
    """Create a temporary directory for audit trail testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audit_path = Path(tmpdir) / "data" / "derived"
        audit_path.mkdir(parents=True, exist_ok=True)
        yield audit_path

@pytest.fixture
def mock_project_root(temp_audit_dir):
    """Mock get_project_root to return our temp directory."""
    with patch('data.audit_trail.get_project_root', return_value=temp_audit_dir.parent.parent):
        yield temp_audit_dir.parent.parent

def test_log_attempt(mock_project_root, temp_audit_dir):
    """Test that log_attempt correctly appends an entry."""
    from data.audit_trail import log_attempt, load_audit_trail

    # Clear any existing entries
    from data.audit_trail import save_audit_trail
    save_audit_trail([])

    log_attempt('file', '/path/to/data.csv', 'success')

    entries = load_audit_trail()
    assert len(entries) == 1
    assert entries[0]['source_type'] == 'file'
    assert entries[0]['source_identifier'] == '/path/to/data.csv'
    assert entries[0]['status'] == 'success'
    assert 'timestamp' in entries[0]

def test_log_file_attempt(mock_project_root, temp_audit_dir):
    """Test logging a file attempt."""
    from data.audit_trail import log_file_attempt, load_audit_trail
    from data.audit_trail import save_audit_trail
    save_audit_trail([])

    log_file_attempt('/missing/file.csv', 'fail', 'FileNotFoundError')

    entries = load_audit_trail()
    assert len(entries) == 1
    assert entries[0]['status'] == 'fail'
    assert entries[0]['details']['error'] == 'FileNotFoundError'

def test_log_url_attempt(mock_project_root, temp_audit_dir):
    """Test logging a URL attempt."""
    from data.audit_trail import log_url_attempt, load_audit_trail
    from data.audit_trail import save_audit_trail
    save_audit_trail([])

    log_url_attempt('https://example.com/data.json', 'fail', http_code=404, error_message='Not Found')

    entries = load_audit_trail()
    assert len(entries) == 1
    assert entries[0]['details']['http_code'] == 404
    assert entries[0]['details']['error'] == 'Not Found'

def test_log_mock_usage(mock_project_root, temp_audit_dir):
    """Test logging mock data usage."""
    from data.audit_trail import log_mock_usage, load_audit_trail
    from data.audit_trail import save_audit_trail
    save_audit_trail([])

    log_mock_usage('quant_config', 'testing', is_synthetic=True)

    entries = load_audit_trail()
    assert len(entries) == 1
    assert entries[0]['details']['is_synthetic'] is True
    assert entries[0]['details']['purpose'] == 'testing'

def test_load_empty_audit_trail(mock_project_root, temp_audit_dir):
    """Test loading a non-existent audit trail returns empty list."""
    from data.audit_trail import load_audit_trail
    # Ensure file doesn't exist
    audit_path = temp_audit_dir / "audit_trail.json"
    if audit_path.exists():
        audit_path.unlink()

    entries = load_audit_trail()
    assert entries == []

def test_save_and_load_audit_trail(mock_project_root, temp_audit_dir):
    """Test saving and loading a populated audit trail."""
    from data.audit_trail import save_audit_trail, load_audit_trail

    test_data = [
        {"timestamp": "2023-01-01T00:00:00Z", "source_type": "file", "status": "success"}
    ]
    save_audit_trail(test_data)

    loaded = load_audit_trail()
    assert len(loaded) == 1
    assert loaded[0]['source_type'] == 'file'

def test_corrupted_audit_trail(mock_project_root, temp_audit_dir):
    """Test handling of corrupted JSON in audit trail."""
    from data.audit_trail import save_audit_trail, load_audit_trail
    import logging

    # Create a corrupted file
    audit_path = temp_audit_dir / "audit_trail.json"
    with open(audit_path, 'w') as f:
        f.write("{ invalid json }")

    # Should return empty list and log error
    with patch.object(logging.Logger, 'error') as mock_log:
        entries = load_audit_trail()
        assert entries == []
        mock_log.assert_called()