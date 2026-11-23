"""
Unit tests for T012c: Data Integrity Check and Merge.
"""
import csv
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
# We need to adjust the import path since tests are in tests/unit/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from integrate_data import (
    load_csv_to_dicts,
    save_dicts_to_csv,
    load_truncated_repos,
    save_truncated_repos,
    integrate_data,
    append_to_quality_log
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_csv_to_dicts(temp_dir):
    """Test loading a CSV file into a list of dictionaries."""
    csv_file = temp_dir / "test.csv"
    data = [
        {"col1": "val1", "col2": "val2"},
        {"col1": "val3", "col2": "val4"}
    ]
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["col1", "col2"])
        writer.writeheader()
        writer.writerows(data)
    
    result = load_csv_to_dicts(csv_file)
    assert result == data

def test_load_csv_to_dicts_empty(temp_dir):
    """Test loading an empty CSV file."""
    csv_file = temp_dir / "empty.csv"
    csv_file.touch()
    
    result = load_csv_to_dicts(csv_file)
    assert result == []

def test_save_dicts_to_csv(temp_dir):
    """Test saving a list of dictionaries to a CSV file."""
    csv_file = temp_dir / "output.csv"
    data = [
        {"col1": "val1", "col2": "val2"},
        {"col1": "val3", "col2": "val4"}
    ]
    
    save_dicts_to_csv(data, csv_file)
    
    assert csv_file.exists()
    result = load_csv_to_dicts(csv_file)
    assert result == data

def test_load_truncated_repos(temp_dir):
    """Test loading repository names from a text file."""
    txt_file = temp_dir / "repos.txt"
    content = """# Comment
    repo1
    repo2
    # Another comment
    repo3
    """
    txt_file.write_text(content)
    
    result = load_truncated_repos(txt_file)
    assert result == {"repo1", "repo2", "repo3"}

def test_save_truncated_repos(temp_dir):
    """Test saving repository names to a text file."""
    txt_file = temp_dir / "repos.txt"
    repos = {"repo1", "repo2", "repo3"}
    
    save_truncated_repos(repos, txt_file)
    
    assert txt_file.exists()
    content = txt_file.read_text()
    assert "repo1" in content
    assert "repo2" in content
    assert "repo3" in content
    assert "repo1" in content # Check for sorted order or just presence

def test_append_to_quality_log(temp_dir):
    """Test appending to the quality log."""
    log_file = temp_dir / "log.txt"
    msg = "Test message"
    
    append_to_quality_log(msg, log_file)
    
    assert log_file.exists()
    assert msg in log_file.read_text()

def test_integrate_data_merge(temp_dir):
    """Test merging partial and canonical data."""
    # Setup paths
    processed_dir = temp_dir
    partial_file = processed_dir / "pr_turnaround_partial.csv"
    canonical_file = processed_dir / "pr_turnaround.csv"
    truncated_file = processed_dir / "truncated_repos.txt"
    log_file = processed_dir / "data_quality_warning.log"
    
    # Create partial data
    partial_data = [
        {"pr_id": "101", "repo_name": "repoA", "turnaround_hours": 10.0},
        {"pr_id": "102", "repo_name": "repoB", "turnaround_hours": 20.0}
    ]
    save_dicts_to_csv(partial_data, partial_file)
    
    # Create canonical data
    canonical_data = [
        {"pr_id": "001", "repo_name": "repoC", "turnaround_hours": 5.0}
    ]
    save_dicts_to_csv(canonical_data, canonical_file)
    
    # Create truncated repos list
    save_truncated_repos({"repoA", "repoB"}, truncated_file)
    
    # Mock the paths in the module
    with patch('integrate_data.PROCESSED_DIR', processed_dir), \
         patch('integrate_data.PARTIAL_FILE', partial_file), \
         patch('integrate_data.CANONICAL_FILE', canonical_file), \
         patch('integrate_data.TRUNCATED_REPOS_FILE', truncated_file), \
         patch('integrate_data.QUALITY_LOG_FILE', log_file):
        
        integrate_data()
    
    # Verify results
    assert not partial_file.exists(), "Partial file should be removed"
    assert canonical_file.exists(), "Canonical file should exist"
    
    final_data = load_csv_to_dicts(canonical_file)
    assert len(final_data) == 3, "Should have 3 rows (1 original + 2 partial)"
    
    # Check log
    assert log_file.exists()
    log_content = log_file.read_text()
    assert "TRUNCATED" in log_content
    assert "repoA" in log_content

def test_integrate_data_promote(temp_dir):
    """Test promoting partial to canonical when canonical is missing."""
    processed_dir = temp_dir
    partial_file = processed_dir / "pr_turnaround_partial.csv"
    canonical_file = processed_dir / "pr_turnaround.csv"
    truncated_file = processed_dir / "truncated_repos.txt"
    log_file = processed_dir / "data_quality_warning.log"
    
    partial_data = [
        {"pr_id": "101", "repo_name": "repoA", "turnaround_hours": 10.0}
    ]
    save_dicts_to_csv(partial_data, partial_file)
    
    with patch('integrate_data.PROCESSED_DIR', processed_dir), \
         patch('integrate_data.PARTIAL_FILE', partial_file), \
         patch('integrate_data.CANONICAL_FILE', canonical_file), \
         patch('integrate_data.TRUNCATED_REPOS_FILE', truncated_file), \
         patch('integrate_data.QUALITY_LOG_FILE', log_file):
        
        integrate_data()
    
    assert not partial_file.exists(), "Partial file should be removed"
    assert canonical_file.exists(), "Canonical file should exist"
    
    final_data = load_csv_to_dicts(canonical_file)
    assert len(final_data) == 1
    assert final_data[0]["pr_id"] == "101"
    
    # Check log
    assert log_file.exists()
    assert "TRUNCATED" in log_file.read_text()

def test_integrate_data_no_files(temp_dir):
    """Test behavior when no files exist."""
    processed_dir = temp_dir
    partial_file = processed_dir / "pr_turnaround_partial.csv"
    canonical_file = processed_dir / "pr_turnaround.csv"
    truncated_file = processed_dir / "truncated_repos.txt"
    log_file = processed_dir / "data_quality_warning.log"
    
    with patch('integrate_data.PROCESSED_DIR', processed_dir), \
         patch('integrate_data.PARTIAL_FILE', partial_file), \
         patch('integrate_data.CANONICAL_FILE', canonical_file), \
         patch('integrate_data.TRUNCATED_REPOS_FILE', truncated_file), \
         patch('integrate_data.QUALITY_LOG_FILE', log_file):
        
        integrate_data()
    
    assert canonical_file.exists(), "Canonical file should be created (empty)"
    assert len(load_csv_to_dicts(canonical_file)) == 0
    assert not log_file.exists() # No warning if no data found and no truncation