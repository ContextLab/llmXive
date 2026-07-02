import os
import csv
import tempfile
import shutil
import sys
from pathlib import Path

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.helpers import (
    check_duplicate_ip, 
    hash_ip, 
    append_to_submissions_csv, 
    CSV_HEADER,
    ensure_data_dirs
)

def setup_test_environment():
    """Create a temporary directory for test data."""
    test_dir = tempfile.mkdtemp()
    raw_dir = os.path.join(test_dir, "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    return test_dir, raw_dir

def teardown_test_environment(test_dir):
    """Remove temporary directory."""
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

def test_check_duplicate_ip_no_file():
    """Test duplicate check when no file exists."""
    test_dir, _ = setup_test_environment()
    original_cwd = os.getcwd()
    try:
        os.chdir(test_dir)
        # Temporarily override the path in helpers by mocking or testing logic directly
        # Since helpers uses a hardcoded constant, we test the logic in isolation
        # by ensuring the function returns False if file is missing
        result = check_duplicate_ip("abc123")
        assert result is False, "Should return False if file does not exist"
    finally:
        os.chdir(original_cwd)
        teardown_test_environment(test_dir)

def test_check_duplicate_ip_new_hash():
    """Test duplicate check when hash is new."""
    test_dir, raw_dir = setup_test_environment()
    original_cwd = os.getcwd()
    try:
        os.chdir(test_dir)
        # Create a dummy CSV with a different hash
        csv_path = os.path.join(raw_dir, "submissions.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
            writer.writeheader()
            writer.writerow({
                "ip_hash": hash_ip("1.1.1.1"),
                "user_id": "user1",
                "timestamp": "2023-01-01",
                "duplicate_flag": 0,
                "condition": "Professional",
                "credibility_rating": 5,
                "professionalism_rating": 5,
                "age": 25,
                "education_code": 1,
                "user_agent": "test",
                "session_timeout": "false",
                "submission_status": "complete",
                "rating_count": 2
            })
        
        # Check for a new hash
        new_hash = hash_ip("2.2.2.2")
        result = check_duplicate_ip(new_hash)
        assert result is False, "Should return False for new hash"
    finally:
        os.chdir(original_cwd)
        teardown_test_environment(test_dir)

def test_check_duplicate_ip_existing_hash():
    """Test duplicate check when hash already exists."""
    test_dir, raw_dir = setup_test_environment()
    original_cwd = os.getcwd()
    try:
        os.chdir(test_dir)
        # Create a dummy CSV with a specific hash
        csv_path = os.path.join(raw_dir, "submissions.csv")
        existing_ip = "192.168.1.100"
        existing_hash = hash_ip(existing_ip)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
            writer.writeheader()
            writer.writerow({
                "ip_hash": existing_hash,
                "user_id": "user1",
                "timestamp": "2023-01-01",
                "duplicate_flag": 0,
                "condition": "Professional",
                "credibility_rating": 5,
                "professionalism_rating": 5,
                "age": 25,
                "education_code": 1,
                "user_agent": "test",
                "session_timeout": "false",
                "submission_status": "complete",
                "rating_count": 2
            })
        
        # Check for the existing hash
        result = check_duplicate_ip(existing_hash)
        assert result is True, "Should return True for existing hash"
    finally:
        os.chdir(original_cwd)
        teardown_test_environment(test_dir)

def test_duplicate_flag_in_csv():
    """Test that the duplicate flag is correctly written to CSV."""
    test_dir, raw_dir = setup_test_environment()
    original_cwd = os.getcwd()
    try:
        os.chdir(test_dir)
        csv_path = os.path.join(raw_dir, "submissions.csv")
        
        # Write first submission
        hash1 = hash_ip("10.0.0.1")
        row1 = {
            "ip_hash": hash1,
            "user_id": "user1",
            "timestamp": "2023-01-01",
            "duplicate_flag": 0,
            "condition": "Professional",
            "credibility_rating": 5,
            "professionalism_rating": 5,
            "age": 25,
            "education_code": 1,
            "user_agent": "test",
            "session_timeout": "false",
            "submission_status": "complete",
            "rating_count": 2
        }
        append_to_submissions_csv(row1)
        
        # Write second submission with same IP
        row2 = {
            "ip_hash": hash1,
            "user_id": "user2",
            "timestamp": "2023-01-02",
            "duplicate_flag": 1, # Expected to be 1
            "condition": "Minimalist",
            "credibility_rating": 4,
            "professionalism_rating": 4,
            "age": 30,
            "education_code": 2,
            "user_agent": "test",
            "session_timeout": "false",
            "submission_status": "complete",
            "rating_count": 2
        }
        append_to_submissions_csv(row2)
        
        # Verify file contents
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["duplicate_flag"] == "0"
            assert rows[1]["duplicate_flag"] == "1"
    finally:
        os.chdir(original_cwd)
        teardown_test_environment(test_dir)
