import pytest
import os
import sys
import csv
from pathlib import Path
import tempfile
import shutil

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.helpers import (
    prepare_submission_row,
    append_to_submissions_csv,
    ensure_data_dirs,
    truncate_user_agent
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for data/raw."""
    temp_root = tempfile.mkdtemp()
    original_raw = Path("data/raw")
    
    # Mock the DATA_RAW_DIR in helpers
    import utils.helpers
    original_dir = utils.helpers.DATA_RAW_DIR
    utils.helpers.DATA_RAW_DIR = Path(temp_root)
    utils.helpers.CONSENT_LOG_PATH = Path(temp_root) / "consent_log.csv"
    utils.helpers.SUBMISSIONS_PATH = Path(temp_root) / "submissions.csv"
    
    yield Path(temp_root)
    
    # Restore
    utils.helpers.DATA_RAW_DIR = original_dir
    utils.helpers.CONSENT_LOG_PATH = Path("data/raw/consent_log.csv")
    utils.helpers.SUBMISSIONS_PATH = Path("data/raw/submissions.csv")
    shutil.rmtree(temp_root)

def test_prepare_submission_row_basic(temp_data_dir):
    """Test that prepare_submission_row creates a valid dictionary."""
    ratings = {
        "cred_Professional": 5.0,
        "prof_Professional": 6.0,
        "cred_Minimalist": 3.0,
        "prof_Minimalist": 4.0,
        "cred_Low-Quality": 2.0,
        "prof_Low-Quality": 2.0,
        "cred_Neutral": 4.0,
        "prof_Neutral": 5.0
    }
    
    row = prepare_submission_row(
        user_id="test-uuid",
        stimulus_condition="Professional;Minimalist;Low-Quality;Neutral",
        ratings=ratings,
        demographic_age=30,
        demographic_education=3,
        hashed_ip="hashed_ip_value",
        user_agent="Mozilla/5.0 (Test)",
        submission_status="complete",
        session_timeout=False
    )
    
    assert row["user_id"] == "test-uuid"
    assert row["age"] == 30
    assert row["education"] == 3
    assert row["hashed_ip"] == "hashed_ip_value"
    assert row["submission_status"] == "complete"
    assert row["rating_count"] == 8
    assert "cred_Professional" in row
    assert row["cred_Professional"] == 5.0

def test_truncate_user_agent():
    """Test that user agent is truncated correctly."""
    long_ua = "A" * 300
    truncated = truncate_user_agent(long_ua, max_length=100)
    assert len(truncated) == 100
    
    short_ua = "Short UA"
    assert truncate_user_agent(short_ua) == short_ua

def test_append_to_submissions_csv(temp_data_dir):
    """Test that data is appended to CSV correctly."""
    row_data = {
        "user_id": "uuid-1",
        "age": 25,
        "education": 2,
        "hashed_ip": "hash1",
        "user_agent": "Agent1",
        "submission_status": "complete",
        "session_timeout": "false",
        "rating_count": 8,
        "cred_Professional": 5.0
    }
    
    # First write (creates file)
    append_to_submissions_csv(row_data)
    
    # Second write (appends)
    row_data["user_id"] = "uuid-2"
    append_to_submissions_csv(row_data)
    
    # Verify file content
    csv_path = temp_data_dir / "submissions.csv"
    assert csv_path.exists()
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]["user_id"] == "uuid-1"
    assert rows[1]["user_id"] == "uuid-2"
    assert "cred_Professional" in rows[0].keys()