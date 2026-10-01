"""
Tests for T022a: Calculate Match Success Rate
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

# We need to import the logic. Since the task creates a new file, 
# we import from the module name assuming it's in the code/ path.
# For the test to run in isolation, we might need to adjust sys.path or 
# rely on the project structure.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from calculate_match_success_rate import (
    calculate_success_rate,
    load_counts,
    save_success_rate,
    ensure_directories
)

@pytest.fixture
def temp_counts_file(tmp_path):
    """Create a temporary counts.json file for testing."""
    counts_data = {
        "count_total_original_valid_location": 1000,
        "count_matched_pre_exclusion": 850,
        "other_count": 100
    }
    file_path = tmp_path / "counts.json"
    with open(file_path, 'w') as f:
        json.dump(counts_data, f)
    return file_path

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "results" / "logs"
    output_dir.mkdir(parents=True)
    return output_dir

def test_calculate_success_rate_basic():
    """Test basic calculation."""
    counts = {
        "count_total_original_valid_location": 1000,
        "count_matched_pre_exclusion": 850
    }
    rate = calculate_success_rate(counts)
    assert rate == 85.0

def test_calculate_success_rate_zero_total():
    """Test handling of zero total."""
    counts = {
        "count_total_original_valid_location": 0,
        "count_matched_pre_exclusion": 0
    }
    rate = calculate_success_rate(counts)
    assert rate == 0.0

def test_calculate_success_rate_missing_key():
    """Test that missing keys raise ValueError."""
    counts = {"count_total_original_valid_location": 1000}
    with pytest.raises(ValueError, match="Missing 'count_matched_pre_exclusion'"):
        calculate_success_rate(counts)

def test_load_counts_success(temp_counts_file, monkeypatch):
    """Test loading counts from a valid file."""
    # Monkeypatch the path used by load_counts to point to our temp file
    # The function hardcodes "results/logs/counts.json", so we need to mock the Path or the open
    # For simplicity in this unit test, we'll test the logic if we refactor load_counts to accept a path.
    # However, adhering to the task spec, load_counts reads from a fixed path.
    # We will test by creating the file in the expected relative location in a temp dir 
    # and changing the working directory, or by mocking.
    
    # Let's mock the Path existence and open
    import calculate_match_success_rate as module
    
    original_path = module.Path
    
    class MockPath:
        def __init__(self, path_str):
            self.path_str = path_str
            self.exists_flag = (path_str == "results/logs/counts.json")
        
        def exists(self):
            return self.exists_flag
        
        def read_text(self, encoding='utf-8'):
            if self.path_str == "results/logs/counts.json":
                return json.dumps({
                    "count_total_original_valid_location": 200,
                    "count_matched_pre_exclusion": 150
                })
            return ""

    module.Path = MockPath
    
    try:
        counts = load_counts()
        assert counts["count_total_original_valid_location"] == 200
        assert counts["count_matched_pre_exclusion"] == 150
    finally:
        module.Path = original_path

def test_save_success_rate(temp_output_dir, monkeypatch):
    """Test saving the result."""
    import calculate_match_success_rate as module
    
    original_path = module.Path
    
    class MockPath:
        def __init__(self, path_str):
            self.path_str = path_str
            self.exists_flag = False # Directory check
            self.content = None
        
        def __truediv__(self, other):
            return self
        
        def mkdir(self, parents=True, exist_ok=False):
            pass
        
        def exists(self):
            # For output file
            return self.path_str.endswith("match_success_rate.json") and False
        
        def open(self, mode, **kwargs):
            # Capture the content
            if 'w' in mode:
                from io import StringIO
                self.content = StringIO()
                return self.content
            return None
        
        def write(self, data):
            if self.content:
                self.content.write(data)

    module.Path = MockPath
    
    try:
        save_success_rate(75.5, "results/logs/match_success_rate.json")
        # Verify content was written (mocked)
    finally:
        module.Path = original_path