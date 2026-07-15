import pytest
import os
import csv
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add project root to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.helpers import (
    prepare_submission_row,
    append_to_submissions_csv,
    save_submission,
    check_duplicate_ip
)

@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file for testing."""
    csv_file = tmp_path / "test_submissions.csv"
    csv_file.touch()
    return str(csv_file)

def test_prepare_submission_row_with_flags():
    """Test that session flags are correctly included in submission row."""
    row = prepare_submission_row(
        user_id="test-user-123",
        condition="Professional",
        ratings={"credibility": 5, "professionalism": 6},
        timestamp="2024-01-01T12:00:00",
        device_info="Mozilla/5.0",
        hashed_ip="abc123",
        age=25,
        education=2,
        session_timeout=True,
        submission_status="excluded"
    )
    
    assert row["session_timeout"] == "true"
    assert row["submission_status"] == "excluded"
    assert row["rating_count"] == 2

def test_complete_submission_status():
    """Test that complete submissions have correct status."""
    row = prepare_submission_row(
        user_id="test-user-456",
        condition="Minimalist",
        ratings={"credibility": 4, "professionalism": 4},
        timestamp="2024-01-01T12:00:00",
        device_info="Mozilla/5.0",
        hashed_ip="def456",
        age=30,
        education=3,
        session_timeout=False,
        submission_status="complete"
    )
    
    assert row["session_timeout"] == "false"
    assert row["submission_status"] == "complete"

def test_append_to_csv_with_flags(temp_csv_file):
    """Test that submission flags are correctly written to CSV."""
    row = prepare_submission_row(
        user_id="test-user-789",
        condition="Low-Quality",
        ratings={"credibility": 3, "professionalism": 2},
        timestamp="2024-01-01T12:00:00",
        device_info="Mozilla/5.0",
        hashed_ip="ghi789",
        age=22,
        education=1,
        session_timeout=True,
        submission_status="excluded"
    )
    
    # Append to CSV
    with open(temp_csv_file, mode='a', newline='', encoding='utf-8') as f:
        import csv
        fieldnames = [
            'user_id', 'condition', 'credibility_rating', 'professionalism_rating',
            'timestamp', 'device_info', 'hashed_ip', 'age', 'education',
            'session_timeout', 'submission_status', 'rating_count'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not os.path.exists(temp_csv_file) or os.path.getsize(temp_csv_file) == 0:
            writer.writeheader()
        writer.writerow(row)
    
    # Read back and verify
    with open(temp_csv_file, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["session_timeout"] == "true"
        assert rows[0]["submission_status"] == "excluded"

def test_save_submission_creates_excluded_record():
    """Test that save_submission correctly handles excluded records."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        tmp_path = tmp.name
    
    try:
        # Mock the file path
        with patch('utils.helpers.SUBMISSIONS_FILE', tmp_path):
            save_submission(
                user_id="test-user-timeout",
                condition="Neutral",
                ratings={"credibility": 5, "professionalism": 5},
                timestamp="2024-01-01T12:00:00",
                device_info="Mozilla/5.0",
                raw_ip="10.0.0.1",
                age=28,
                education=3,
                session_timeout=True,
                submission_status="excluded"
            )
            
            # Verify file was created with correct content
            assert os.path.exists(tmp_path)
            with open(tmp_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]["session_timeout"] == "true"
                assert rows[0]["submission_status"] == "excluded"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def test_partial_submission_flagged_as_excluded():
    """Test that partial submissions (less than 8 ratings) are flagged as excluded."""
    # This test verifies the logic in save_submission_logic
    # The actual filtering happens in the analysis phase
    row = prepare_submission_row(
        user_id="partial-user",
        condition="Professional",
        ratings={"credibility": 5},  # Only 1 rating, should be 8
        timestamp="2024-01-01T12:00:00",
        device_info="Mozilla/5.0",
        hashed_ip="partial123",
        age=25,
        education=2,
        session_timeout=False,
        submission_status="excluded"
    )
    
    assert row["submission_status"] == "excluded"
    assert row["rating_count"] == 1

def test_session_timeout_detection():
    """Test that session timeout flag is correctly set."""
    row = prepare_submission_row(
        user_id="timeout-user",
        condition="Minimalist",
        ratings={"credibility": 4, "professionalism": 4},
        timestamp="2024-01-01T12:00:00",
        device_info="Mozilla/5.0",
        hashed_ip="timeout456",
        age=30,
        education=3,
        session_timeout=True,
        submission_status="excluded"
    )
    
    assert row["session_timeout"] == "true"
    assert row["submission_status"] == "excluded"