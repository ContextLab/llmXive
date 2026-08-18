import os
import sys
import csv
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.helpers import (
    check_duplicate_ip, 
    hash_ip, 
    append_to_submissions_csv, 
    get_submissions_csv_path,
    ensure_data_dirs
)

def test_check_duplicate_ip_no_file():
    """Test that check_duplicate_ip returns False when CSV does not exist."""
    # We cannot easily delete the real file in a test without side effects,
    # so we mock the existence check.
    with patch('utils.helpers.get_submissions_csv_path') as mock_path:
        mock_path.return_value = Path("/fake/path/submissions.csv")
        # Ensure the mock path doesn't exist
        assert not mock_path.return_value.exists()
        
        result = check_duplicate_ip("fake_hash")
        assert result is False

def test_check_duplicate_ip_not_found():
    """Test that check_duplicate_ip returns False when IP is not found."""
    with patch('utils.helpers.get_submissions_csv_path') as mock_path:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            writer = csv.DictWriter(tmp, fieldnames=['hashed_ip', 'user_id'])
            writer.writeheader()
            writer.writerow({'hashed_ip': 'hash1', 'user_id': 'user1'})
            writer.writerow({'hashed_ip': 'hash2', 'user_id': 'user2'})
            tmp_path = tmp.name

        mock_path.return_value = Path(tmp_path)
        
        result = check_duplicate_ip("non_existent_hash")
        assert result is False
        
        os.unlink(tmp_path)

def test_check_duplicate_ip_found():
    """Test that check_duplicate_ip returns True when IP is found."""
    with patch('utils.helpers.get_submissions_csv_path') as mock_path:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            writer = csv.DictWriter(tmp, fieldnames=['hashed_ip', 'user_id'])
            writer.writeheader()
            writer.writerow({'hashed_ip': 'target_hash', 'user_id': 'user1'})
            tmp_path = tmp.name

        mock_path.return_value = Path(tmp_path)
        
        result = check_duplicate_ip("target_hash")
        assert result is True
        
        os.unlink(tmp_path)

def test_duplicate_flag_integration():
    """
    Integration test: Append a row, then check if it is detected as duplicate.
    This verifies the full flow of T023c.
    """
    # Create a temporary directory for this test
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Patch the get_submissions_csv_path to use our temp dir
        temp_csv_path = Path(tmp_dir) / "submissions.csv"
        
        with patch('utils.helpers.get_submissions_csv_path', return_value=temp_csv_path):
            # 1. Create the CSV with a header and one row
            ensure_data_dirs() # This might fail if we don't patch root, but we are mocking path
            
            # Manually write initial data to simulate existing submissions
            with open(temp_csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['hashed_ip', 'user_id', 'duplicate_flag'])
                writer.writeheader()
                writer.writerow({'hashed_ip': 'existing_hash', 'user_id': 'existing_user', 'duplicate_flag': 'False'})
            
            # 2. Check for the existing hash
            is_dup = check_duplicate_ip("existing_hash")
            assert is_dup is True, "Should detect existing hash"
            
            # 3. Check for a new hash
            is_dup_new = check_duplicate_ip("new_hash")
            assert is_dup_new is False, "Should not detect new hash"

            # 4. Append a new row with the new hash
            row = {
                'user_id': 'new_user',
                'condition': 'Professional',
                'credibility_rating': 5,
                'professionalism_rating': 5,
                'timestamp': '2023-01-01T00:00:00.000Z',
                'device_info': 'Desktop',
                'hashed_ip': 'new_hash',
                'age': 25,
                'education_code': 2,
                'submission_status': 'complete',
                'session_timeout': False,
                'duplicate_flag': False
            }
            append_to_submissions_csv(row)
            
            # 5. Verify the file content
            with open(temp_csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 2, "Should have 2 rows"
            assert rows[1]['hashed_ip'] == 'new_hash'
            assert rows[1]['duplicate_flag'] == 'False'

            # 6. Append the SAME hash again
            row['user_id'] = 'new_user_2'
            row['duplicate_flag'] = check_duplicate_ip('new_hash') # Should be True now
            append_to_submissions_csv(row)
            
            # 7. Verify the duplicate flag was set
            with open(temp_csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 3
            assert rows[2]['duplicate_flag'] == 'True', "Third row should be flagged as duplicate"