import pytest
import json
import csv
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from retrieve_crowd_judgments import (
    load_job_ids,
    fetch_submissions_from_prolific,
    format_judgments,
    save_judgments_csv,
    generate_mock_submissions
)

@pytest.fixture
def temp_job_ids_file(tmp_path):
    """Create a temporary job IDs file for testing."""
    job_ids_data = ["job_001", "job_002", "job_003"]
    file_path = tmp_path / "crowd_job_ids.json"
    with open(file_path, "w") as f:
        json.dump(job_ids_data, f)
    return file_path

@pytest.fixture
def mock_job_ids_dict(tmp_path):
    """Create a temporary job IDs file with dict format."""
    job_ids_data = [
        {"job_id": "job_001", "status": "completed"},
        {"job_id": "job_002", "status": "completed"},
        {"job_id": "job_003", "status": "completed"}
    ]
    file_path = tmp_path / "crowd_job_ids.json"
    with open(file_path, "w") as f:
        json.dump(job_ids_data, f)
    return file_path

def test_load_job_ids_list_format(temp_job_ids_file):
    """Test loading job IDs from a simple list format."""
    with patch("retrieve_crowd_judgments.JOB_IDS_FILE", temp_job_ids_file):
        job_ids = load_job_ids()
        assert job_ids == ["job_001", "job_002", "job_003"]

def test_load_job_ids_dict_format(mock_job_ids_dict):
    """Test loading job IDs from a dict format."""
    with patch("retrieve_crowd_judgments.JOB_IDS_FILE", mock_job_ids_dict):
        job_ids = load_job_ids()
        assert job_ids == ["job_001", "job_002", "job_003"]

def test_load_job_ids_file_not_found():
    """Test error handling when job IDs file is missing."""
    with patch("retrieve_crowd_judgments.JOB_IDS_FILE", Path("/nonexistent/file.json")):
        with pytest.raises(FileNotFoundError):
            load_job_ids()

def test_generate_mock_submissions():
    """Test mock submission generation."""
    job_ids = ["job_001"]
    submissions = generate_mock_submissions(job_ids)
    
    assert len(submissions) == 150
    assert all("sample_id" in s for s in submissions)
    assert all("domain" in s for s in submissions)
    assert all("human_judgment" in s for s in submissions)
    
    # Check domain distribution
    domains = [s["domain"] for s in submissions]
    assert len(set(domains)) == 3
    assert "speech" in domains
    assert "music" in domains
    assert "env" in domains

def test_format_judgments():
    """Test formatting of submissions to required schema."""
    raw_submissions = [
        {
            "job_id": "job_001",
            "sample_id": "sample_001",
            "domain": "speech",
            "human_judgment": 1,
            "timestamp": "2024-01-15T10:00:00Z",
            "worker_id": "worker_1"
        },
        {
            "job_id": "job_001",
            "sample_id": "sample_002",
            "domain": "music",
            "human_judgment": 0,
            "timestamp": "2024-01-15T10:01:00Z",
            "worker_id": "worker_2"
        }
    ]
    
    formatted = format_judgments(raw_submissions)
    
    assert len(formatted) == 2
    assert formatted[0]["sample_id"] == "sample_001"
    assert formatted[0]["domain"] == "speech"
    assert formatted[0]["human_judgment"] == 1
    assert formatted[1]["sample_id"] == "sample_002"
    assert formatted[1]["domain"] == "music"
    assert formatted[1]["human_judgment"] == 0

def test_save_judgments_csv(tmp_path):
    """Test saving judgments to CSV."""
    judgments = [
        {"sample_id": "sample_001", "domain": "speech", "human_judgment": 1},
        {"sample_id": "sample_002", "domain": "music", "human_judgment": 0}
    ]
    output_path = tmp_path / "human_judgments.csv"
    
    save_judgments_csv(judgments, output_path)
    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]["sample_id"] == "sample_001"
    assert rows[0]["human_judgment"] == "1"  # CSV reads as string
    assert rows[1]["domain"] == "music"

def test_fetch_submissions_mock_mode():
    """Test that mock mode is used when API key is missing."""
    with patch.dict(os.environ, {}, clear=True):  # Remove PROLIFIC_API_KEY
        with patch("retrieve_crowd_judgments.MOCK_MODE", True):
            job_ids = ["job_001"]
            submissions = fetch_submissions_from_prolific(job_ids)
            
            assert len(submissions) == 150
            assert all(isinstance(s, dict) for s in submissions)