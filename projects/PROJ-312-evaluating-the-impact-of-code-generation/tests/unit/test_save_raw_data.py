import json
import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from save_raw_data import load_raw_pr_data, save_raw_data
from utils import validate_json_schema

@pytest.fixture
def sample_pr_data():
    """Sample PR data for testing"""
    return [
        {
            "pr_id": "PR-001",
            "repo_name": "test/repo",
            "created_at": "2023-01-01T00:00:00Z",
            "merged_at": "2023-01-02T00:00:00Z",
            "labels": ["ai-generated"],
            "commit_messages": ["feat: add feature", "copilot suggestion"],
            "turnaround_hours": 24.0
        },
        {
            "pr_id": "PR-002",
            "repo_name": "test/repo",
            "created_at": "2023-01-03T00:00:00Z",
            "merged_at": "2023-01-04T12:00:00Z",
            "labels": [],
            "commit_messages": ["fix: bug fix"],
            "turnaround_hours": 36.0
        }
    ]

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files"""
    return tmp_path

def test_load_raw_pr_data(sample_pr_data, temp_dir):
    """Test loading raw PR data from JSON file"""
    # Create a test file
    test_file = temp_dir / "test_pr_data.json"
    with open(test_file, 'w') as f:
        json.dump(sample_pr_data, f)
    
    # Load the data
    loaded_data = load_raw_pr_data(str(test_file))
    
    # Verify
    assert len(loaded_data) == len(sample_pr_data)
    assert loaded_data[0]["pr_id"] == "PR-001"
    assert loaded_data[1]["turnaround_hours"] == 36.0

def test_save_raw_data(sample_pr_data, temp_dir):
    """Test saving raw PR data to JSON file with schema validation"""
    output_file = temp_dir / "output_pr_data.json"
    
    # Save the data
    save_raw_data(sample_pr_data, str(output_file))
    
    # Verify file exists
    assert output_file.exists()
    
    # Verify content
    with open(output_file, 'r') as f:
        saved_data = json.load(f)
    
    assert len(saved_data) == len(sample_pr_data)
    assert saved_data[0]["pr_id"] == "PR-001"

def test_save_raw_data_invalid_schema(sample_pr_data, temp_dir):
    """Test saving data with invalid schema (missing required fields)"""
    # Create data with missing required field
    invalid_data = [
        {
            "pr_id": "PR-003",
            # Missing required fields: repo_name, turnaround_hours
            "created_at": "2023-01-01T00:00:00Z"
        }
    ]
    
    output_file = temp_dir / "invalid_output.json"
    
    # This should still save but log warnings (based on current implementation)
    # In a stricter implementation, this might raise an error
    save_raw_data(invalid_data, str(output_file))
    
    assert output_file.exists()

def test_load_nonexistent_file(temp_dir):
    """Test loading from a non-existent file raises FileNotFoundError"""
    nonexistent_file = temp_dir / "does_not_exist.json"
    
    with pytest.raises(FileNotFoundError):
        load_raw_pr_data(str(nonexistent_file))

def test_load_invalid_json_format(temp_dir):
    """Test loading data that is not a list"""
    test_file = temp_dir / "invalid_format.json"
    with open(test_file, 'w') as f:
        json.dump({"not": "a list"}, f)
    
    with pytest.raises(ValueError, match="Expected list of PR data"):
        load_raw_pr_data(str(test_file))

def test_save_creates_directory(temp_dir):
    """Test that save_raw_data creates the output directory if it doesn't exist"""
    nested_output = temp_dir / "subdir" / "output.json"
    
    save_raw_data([], str(nested_output))
    
    assert nested_output.exists()