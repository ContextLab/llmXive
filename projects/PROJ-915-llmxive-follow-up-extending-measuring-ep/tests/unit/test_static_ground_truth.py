"""
Unit tests for static_ground_truth.py (T020).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# Note: We assume the test runner is executed from the project root or code/ directory
# Adjust import path if necessary based on test execution environment
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from static_ground_truth import download_medqa_facts, verify_and_save_static_facts, compute_sha256
from error_handling import DatasetDownloadError

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_dataset_item():
    return {
        "question": "Test question?",
        "options": ["A", "B", "C", "D", "E"],
        "answer": "A"
    }

def test_download_medqa_facts_creates_file(temp_output_dir, mock_dataset_item):
    """Test that download_medqa_facts creates a valid JSON file."""
    output_path = temp_output_dir / "test_facts.json"
    
    # Mock the load_dataset and iteration
    with patch("static_ground_truth.load_dataset") as mock_load:
        mock_dataset = MagicMock()
        # Create an iterator that yields the mock item a few times
        mock_dataset.__iter__ = MagicMock(return_value=iter([mock_dataset_item] * 5))
        mock_load.return_value = mock_dataset

        result = download_medqa_facts(output_path, limit=5)

        assert result is True
        assert output_path.exists()
        
        with open(output_path, "r") as f:
            data = json.load(f)
        
        assert len(data) == 5
        assert data[0]["question"] == "Test question?"
        assert data[0]["correct_answer"] == "A"
        assert data[0]["answer_letter"] == "A"

def test_download_medqa_facts_fails_on_empty_dataset(temp_output_dir):
    """Test that download_medqa_facts raises DatasetDownloadError on empty dataset."""
    output_path = temp_output_dir / "test_facts.json"
    
    with patch("static_ground_truth.load_dataset") as mock_load:
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([]))
        mock_load.return_value = mock_dataset

        with pytest.raises(DatasetDownloadError, match="Downloaded 0 samples"):
            download_medqa_facts(output_path, limit=5)

def test_verify_and_save_static_facts(temp_output_dir):
    """Test verification and state file creation."""
    # Create a dummy file
    output_path = temp_output_dir / "facts.json"
    data = [{"question": "Q", "options": [], "correct_answer": "A", "answer_letter": "A", "source": "test"}]
    with open(output_path, "w") as f:
        json.dump(data, f)
    
    state_path = temp_output_dir / "state.yaml"

    # First run: should create state file
    result = verify_and_save_static_facts(output_path, state_path)
    assert result is True
    assert state_path.exists()

    # Second run: should verify against stored hash
    # (In a real scenario, we'd check if the hash matches)
    result2 = verify_and_save_static_facts(output_path, state_path)
    assert result2 is True

def test_compute_sha256(temp_output_dir):
    """Test SHA-256 computation."""
    test_file = temp_output_dir / "hash_test.txt"
    content = "Hello, World!"
    with open(test_file, "w") as f:
        f.write(content)
    
    hash1 = compute_sha256(test_file)
    hash2 = compute_sha256(test_file)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length
