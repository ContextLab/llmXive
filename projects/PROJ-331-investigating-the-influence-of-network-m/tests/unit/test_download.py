import pytest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
import tempfile
import os

from download import (
    load_subject_list,
    download_subject_data,
    check_hcp_availability,
    verify_checksum
)

def test_load_subject_list_json(tmp_path):
    """Test loading subject list from JSON file"""
    subject_ids_file = tmp_path / "subjects.json"
    subject_ids = ["100307", "100408", "100509"]
    subject_ids_file.write_text(json.dumps(subject_ids))
    
    manifest = load_subject_list(subject_ids_file)
    
    assert manifest['total_subjects'] == len(subject_ids)
    assert manifest['subject_ids'] == subject_ids
    assert manifest['subjects_attempted'] == 0

def test_load_subject_list_txt(tmp_path):
    """Test loading subject list from text file (one per line)"""
    subject_ids_file = tmp_path / "subjects.txt"
    subject_ids = ["100307", "100408", "100509"]
    subject_ids_file.write_text("\n".join(subject_ids))
    
    manifest = load_subject_list(subject_ids_file)
    
    assert manifest['total_subjects'] == len(subject_ids)
    assert manifest['subject_ids'] == subject_ids

def test_load_subject_list_missing_file(tmp_path):
    """Test loading subject list from non-existent file"""
    subject_ids_file = tmp_path / "nonexistent.txt"
    
    with pytest.raises(FileNotFoundError):
        load_subject_list(subject_ids_file)

@patch('download.requests.head')
def test_check_hcp_availability_success(mock_head):
    """Test HCP availability check when accessible"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_head.return_value = mock_response
    
    result = check_hcp_availability()
    assert result is True

@patch('download.requests.head')
def test_check_hcp_availability_failure(mock_head):
    """Test HCP availability check when not accessible"""
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_head.return_value = mock_response
    
    result = check_hcp_availability()
    assert result is False

@patch('download.requests.head')
def test_check_hcp_availability_timeout(mock_head):
    """Test HCP availability check when timeout occurs"""
    mock_head.side_effect = Exception("Timeout")
    
    result = check_hcp_availability()
    assert result is False