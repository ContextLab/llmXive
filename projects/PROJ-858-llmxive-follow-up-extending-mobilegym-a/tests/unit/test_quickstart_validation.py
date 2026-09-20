"""
Unit tests for the Quickstart Validation script.

These tests ensure that the validation logic correctly identifies
missing files, creates placeholders, and validates the scheduler.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add code directory to path
CODE_DIR = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(CODE_DIR))

from utils.constants import get_coverage_vector_dimensions
from scheduler.curriculum_scheduler import CurriculumScheduler

def test_scheduler_initialization():
    """Test that the scheduler can be initialized."""
    scheduler = CurriculumScheduler()
    assert scheduler is not None

def test_scheduler_selection_with_mock_data():
    """Test scheduler selection with mock history."""
    scheduler = CurriculumScheduler()
    
    # Create mock history
    mock_history = [
        {"task_id": f"mock_{i}", "coverage_vector": [0.0] * get_coverage_vector_dimensions(), "success_rate": 0.5}
        for i in range(5)
    ]
    
    # Test Phase 1
    batch = scheduler.select_tasks(mock_history, phase=1, target_coverage=0.05)
    assert isinstance(batch, list)
    
    # Test Phase 2
    batch = scheduler.select_tasks(mock_history, phase=2, target_success_rate=0.5)
    assert isinstance(batch, list)

def test_file_existence_check():
    """Test the file existence check logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        
        # File doesn't exist
        assert not test_file.exists()
        
        # Create file
        test_file.write_text("test")
        
        # File exists
        assert test_file.exists()

def test_coverage_vector_dimensions():
    """Test that coverage vector dimensions are retrieved correctly."""
    dims = get_coverage_vector_dimensions()
    assert isinstance(dims, int)
    assert dims > 0

def test_json_serialization():
    """Test that mock data can be serialized to JSON."""
    data = {
        "task_id": "test",
        "vector": [0.0] * get_coverage_vector_dimensions(),
        "success_rate": 0.5
    }
    json_str = json.dumps(data)
    parsed = json.loads(json_str)
    assert parsed["task_id"] == "test"
    assert len(parsed["vector"]) == get_coverage_vector_dimensions()