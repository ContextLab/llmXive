import os
import csv
import tempfile
import shutil
from pathlib import Path
import pytest
from datetime import datetime

# Import the functions we are testing
# We need to adjust the import path to match the project structure
# Assuming tests are at root, and code is at code/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.helpers import (
    append_to_submissions_csv,
    check_duplicate_ip,
    prepare_submission_row,
    get_project_root,
    ensure_data_dirs
)

@pytest.fixture
def temp_csv_path():
    """Create a temporary CSV file for testing."""
    temp_dir = tempfile.mkdtemp()
    csv_path = Path(temp_dir) / "submissions.csv"
    yield csv_path
    shutil.rmtree(temp_dir)

def test_append_to_submissions_csv_creates_file(temp_csv_path):
    """Test that append_to_submissions_csv creates a new file with headers."""
    row = {
        'user_id': 'test-123',
        'sequence_id': 1,
        'condition': 'Professional',
        'credibility_rating': 5,
        'professionalism_rating': 5,
        'timestamp': datetime.utcnow().isoformat(),
        'hashed_ip': 'abc123',
        'age': 25,
        'education': 2,
        'user_agent': 'TestAgent',
        'duplicate_flag': False,
        'submission_status': 'complete',
        'session_timeout': False
    }
    
    append_to_submissions_csv(row, temp_csv_path)
    
    assert temp_csv_path.exists()
    with open(temp_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['user_id'] == 'test-123'

def test_append_to_submissions_csv_appends(temp_csv_path):
    """Test that append_to_submissions_csv appends to existing file."""
    row1 = {
        'user_id': 'test-123',
        'sequence_id': 1,
        'condition': 'Professional',
        'credibility_rating': 5,
        'professionalism_rating': 5,
        'timestamp': datetime.utcnow().isoformat(),
        'hashed_ip': 'abc123',
        'age': 25,
        'education': 2,
        'user_agent': 'TestAgent',
        'duplicate_flag': False,
        'submission_status': 'complete',
        'session_timeout': False
    }
    row2 = {
        'user_id': 'test-456',
        'sequence_id': 2,
        'condition': 'Minimalist',
        'credibility_rating': 3,
        'professionalism_rating': 4,
        'timestamp': datetime.utcnow().isoformat(),
        'hashed_ip': 'def456',
        'age': 30,
        'education': 3,
        'user_agent': 'TestAgent2',
        'duplicate_flag': False,
        'submission_status': 'complete',
        'session_timeout': False
    }
    
    append_to_submissions_csv(row1, temp_csv_path)
    append_to_submissions_csv(row2, temp_csv_path)
    
    with open(temp_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[1]['user_id'] == 'test-456'

def test_check_duplicate_ip_not_found(temp_csv_path):
    """Test duplicate check returns False when IP not found."""
    # Create empty file with headers
    with open(temp_csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['hashed_ip', 'user_id'])
        writer.writeheader()
        writer.writerow({'hashed_ip': 'existing_hash', 'user_id': '1'})
    
    assert not check_duplicate_ip('new_hash', temp_csv_path)

def test_check_duplicate_ip_found(temp_csv_path):
    """Test duplicate check returns True when IP found."""
    with open(temp_csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['hashed_ip', 'user_id'])
        writer.writeheader()
        writer.writerow({'hashed_ip': 'existing_hash', 'user_id': '1'})
    
    assert check_duplicate_ip('existing_hash', temp_csv_path)