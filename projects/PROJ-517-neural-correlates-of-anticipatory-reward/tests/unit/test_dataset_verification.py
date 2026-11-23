"""
Unit tests for dataset_verification.py (T000b).
"""
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from dataset_verification import load_candidates, save_candidates, check_schema_compliance, verify_dataset

def test_load_candidates_success():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"dataset_id": "ds001", "url": "http://test.com"}, f)
        path = f.name
    
    try:
        data = load_candidates(path)
        assert data["dataset_id"] == "ds001"
        assert data["url"] == "http://test.com"
    finally:
        os.unlink(path)

def test_load_candidates_missing_file():
    with pytest.raises(FileNotFoundError):
        load_candidates("/nonexistent/path.json")

def test_save_candidates():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        path = f.name
    
    try:
        data = {"verified": True}
        save_candidates(path, data)
        with open(path, 'r') as f:
            loaded = json.load(f)
        assert loaded == data
    finally:
        os.unlink(path)

@patch('dataset_verification.verify_url_reachability')
def test_check_schema_compliance_unreachable(mock_reachability):
    mock_reachability.return_value = False
    result = check_schema_compliance("ds001", "http://broken.com")
    assert result["verified"] is False
    assert "url_reachability" in result["missing_columns"]

@patch('dataset_verification.verify_url_reachability')
@patch('dataset_verification.fetch_dataset_metadata')
def test_check_schema_compliance_success(mock_fetch, mock_reachability):
    mock_reachability.return_value = True
    mock_fetch.return_value = {"status": "found"}
    result = check_schema_compliance("ds001", "http://test.com")
    assert result["verified"] is True
    assert result["missing_columns"] == []

@patch('dataset_verification.verify_url_reachability')
@patch('dataset_verification.fetch_dataset_metadata')
def test_check_schema_compliance_no_metadata(mock_fetch, mock_reachability):
    mock_reachability.return_value = True
    mock_fetch.return_value = None
    result = check_schema_compliance("ds001", "http://test.com")
    assert result["verified"] is False
    assert "snr" in result["missing_columns"]
    assert "isolation_distance" in result["missing_columns"]
