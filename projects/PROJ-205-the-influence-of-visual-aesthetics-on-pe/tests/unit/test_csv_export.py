import pytest
import os
import csv
import tempfile
import shutil
from pathlib import Path
import sys

# Add the project root to the path to allow imports
# This assumes the test is run from the project root or via pytest discovery
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.helpers import (
    prepare_submission_row,
    append_to_submissions_csv,
    save_submission,
    get_submissions_csv_path,
    get_project_root
)

@pytest.fixture
def temp_data_dir(monkeypatch):
    """Creates a temporary directory structure for data and patches the helper functions."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Patch the get_project_root function to return our temp directory
    def mock_get_project_root():
        return Path(temp_dir)
    
    # We need to monkeypatch the function in the module where it's used
    # Since helpers.py defines it, we patch it there
    import utils.helpers
    original_get_project_root = utils.helpers.get_project_root
    utils.helpers.get_project_root = mock_get_project_root
    
    # Also need to ensure ensure_data_dirs creates dirs in temp
    original_ensure = utils.helpers.ensure_data_dirs
    def mock_ensure():
        (Path(temp_dir) / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (Path(temp_dir) / "data" / "processed").mkdir(parents=True, exist_ok=True)
    
    utils.helpers.ensure_data_dirs = mock_ensure

    yield temp_dir

    # Cleanup
    utils.helpers.get_project_root = original_get_project_root
    utils.helpers.ensure_data_dirs = original_ensure
    shutil.rmtree(temp_dir)

def test_prepare_submission_row_truncates_user_agent(temp_data_dir):
    """Test that user_agent is truncated to 255 characters."""
    long_ua = "A" * 300
    row = prepare_submission_row(
        participant_id="p1",
        stimulus_id="s1",
        credibility=5,
        professionalism=4,
        timestamp="2023-01-01T00:00:00",
        hashed_ip="hash123",
        age=25,
        education_code=2,
        duplicate_flag=False,
        session_status="completed",
        submission_status="success",
        user_agent=long_ua
    )
    assert len(row["user_agent"]) == 255
    assert row["user_agent"] == "A" * 255

def test_save_submission_creates_csv(temp_data_dir):
    """Test that save_submission creates the CSV file with correct headers and data."""
    save_submission(
        participant_id="p1",
        stimulus_id="s1",
        credibility=5,
        professionalism=4,
        hashed_ip="hash123",
        age=25,
        education_label="Bachelor's",
        session_status="completed",
        submission_status="success",
        user_agent="Mozilla/5.0"
    )

    csv_path = get_submissions_csv_path()
    assert os.path.exists(csv_path), f"CSV file not created at {csv_path}"

    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == 1
        row = rows[0]
        assert row["participant_id"] == "p1"
        assert row["stimulus_id"] == "s1"
        assert row["credibility"] == "5"
        assert row["professionalism"] == "4"
        assert row["hashed_ip"] == "hash123"
        assert row["age"] == "25"
        assert row["education"] == "2"
        assert row["session_status"] == "completed"
        assert row["submission_status"] == "success"
        assert "user_agent" in row

def test_save_submission_appends_to_existing(temp_data_dir):
    """Test that save_submission appends to an existing CSV."""
    # First call
    save_submission(
        participant_id="p1",
        stimulus_id="s1",
        credibility=5,
        professionalism=4,
        hashed_ip="hash123",
        age=25,
        education_label="Bachelor's",
        session_status="completed",
        submission_status="success"
    )

    # Second call
    save_submission(
        participant_id="p2",
        stimulus_id="s2",
        credibility=3,
        professionalism=2,
        hashed_ip="hash456",
        age=30,
        education_label="Master's",
        session_status="completed",
        submission_status="success"
    )

    csv_path = get_submissions_csv_path()
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]["participant_id"] == "p1"
        assert rows[1]["participant_id"] == "p2"

def test_save_submission_handles_null_user_agent(temp_data_dir):
    """Test that save_submission handles None user_agent gracefully."""
    save_submission(
        participant_id="p1",
        stimulus_id="s1",
        credibility=5,
        professionalism=4,
        hashed_ip="hash123",
        age=25,
        education_label="High School",
        session_status="completed",
        submission_status="success",
        user_agent=None
    )

    csv_path = get_submissions_csv_path()
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["user_agent"] == ""

def test_schema_columns_present(temp_data_dir):
    """Verify all required schema columns are present."""
    save_submission(
        participant_id="p1",
        stimulus_id="s1",
        credibility=5,
        professionalism=4,
        hashed_ip="hash123",
        age=25,
        education_label="PhD",
        session_status="timeout",
        submission_status="incomplete"
    )

    csv_path = get_submissions_csv_path()
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        required_columns = [
            "participant_id", "stimulus_id", "credibility", "professionalism",
            "timestamp", "hashed_ip", "age", "education", "duplicate_flag",
            "session_status", "submission_status", "user_agent"
        ]
        
        for col in required_columns:
            assert col in headers, f"Missing column: {col}"