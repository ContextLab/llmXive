import os
import csv
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# We need to mock the get_project_root to point to a temp directory
# so we don't write to the actual project data during tests.
import utils.helpers as helpers_module
from utils.helpers import prepare_submission_row, append_to_submissions_csv, save_submission, ensure_data_dirs

def test_prepare_submission_row():
    """Test that prepare_submission_row creates a correctly formatted dictionary."""
    row = prepare_submission_row(
        user_id="test-123",
        stimulus_condition="Professional",
        credibility_rating=5,
        professionalism_rating=6,
        hashed_ip="abc123hash",
        duplicate_flag=False,
        age=25,
        education=2,
        user_agent="Mozilla/5.0 Test",
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
        submission_status="complete",
        session_timeout=False
    )
    
    assert row["user_id"] == "test-123"
    assert row["stimulus_condition"] == "Professional"
    assert row["credibility_rating"] == 5
    assert row["professionalism_rating"] == 6
    assert row["hashed_ip"] == "abc123hash"
    assert row["duplicate_flag"] == False
    assert row["age"] == 25
    assert row["education"] == 2
    assert row["user_agent"] == "Mozilla/5.0 Test"
    assert row["timestamp"] == "2023-01-01T12:00:00"
    assert row["submission_status"] == "complete"
    assert row["session_timeout"] == False

def test_append_to_submissions_csv():
    """Test that append_to_submissions_csv writes to the correct file with headers."""
    # Create a temporary directory to simulate project root
    temp_dir = tempfile.mkdtemp()
    data_raw_path = os.path.join(temp_dir, "data", "raw")
    os.makedirs(data_raw_path, exist_ok=True)
    
    # Mock the get_project_root function temporarily
    original_get_project_root = helpers_module.get_project_root
    
    def mock_get_project_root():
        return Path(temp_dir)
    
    helpers_module.get_project_root = mock_get_project_root
    
    try:
        csv_path = os.path.join(data_raw_path, "submissions.csv")
        
        # First write (should create header)
        row1 = prepare_submission_row(
            user_id="user-1",
            stimulus_condition="Neutral",
            credibility_rating=4,
            professionalism_rating=4,
            hashed_ip="hash1",
            duplicate_flag=False,
            timestamp=datetime(2023, 1, 1, 10, 0, 0)
        )
        append_to_submissions_csv(row1)
        
        # Verify file exists and content
        assert os.path.exists(csv_path)
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["user_id"] == "user-1"
            assert "user_id" in reader.fieldnames
            assert "stimulus_condition" in reader.fieldnames
        
        # Second write (should append, no new header)
        row2 = prepare_submission_row(
            user_id="user-2",
            stimulus_condition="Minimalist",
            credibility_rating=3,
            professionalism_rating=3,
            hashed_ip="hash2",
            duplicate_flag=True,
            timestamp=datetime(2023, 1, 1, 11, 0, 0)
        )
        append_to_submissions_csv(row2)
        
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[1]["user_id"] == "user-2"
            assert rows[1]["duplicate_flag"] == "True"
            
    finally:
        # Restore original function
        helpers_module.get_project_root = original_get_project_root
        # Cleanup
        shutil.rmtree(temp_dir)

def test_save_submission_integration():
    """Test the high-level save_submission function."""
    temp_dir = tempfile.mkdtemp()
    data_raw_path = os.path.join(temp_dir, "data", "raw")
    os.makedirs(data_raw_path, exist_ok=True)
    
    original_get_project_root = helpers_module.get_project_root
    
    def mock_get_project_root():
        return Path(temp_dir)
    
    helpers_module.get_project_root = mock_get_project_root
    
    try:
        csv_path = os.path.join(data_raw_path, "submissions.csv")
        
        save_submission(
            user_id="final-test",
            stimulus_condition="Low-Quality",
            credibility_rating=2,
            professionalism_rating=1,
            hashed_ip="final_hash",
            age=30,
            education=4,
            user_agent="TestAgent/1.0",
            timestamp=datetime(2023, 5, 5, 15, 30, 0)
        )
        
        assert os.path.exists(csv_path)
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["user_id"] == "final-test"
            assert rows[0]["age"] == "30"
            assert rows[0]["education"] == "4"
            
    finally:
        helpers_module.get_project_root = original_get_project_root
        shutil.rmtree(temp_dir)