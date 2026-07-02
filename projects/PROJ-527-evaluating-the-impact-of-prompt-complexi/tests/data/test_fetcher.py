"""
Tests for the HumanEval dataset fetcher.
"""
import pytest
from pathlib import Path
import json
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.fetcher import fetch_humaneval_dataset, compute_file_sha256
from code.utils.logger import DataFetchError
from code.config import DATA_RAW_DIR

@patch('code.data.fetcher.load_dataset')
def test_fetch_humaneval_success(mock_load_dataset, tmp_path):
    """Test successful fetch and save of HumanEval dataset."""
    # Mock dataset
    mock_dataset = MagicMock()
    mock_dataset.__len__ = lambda self: 2
    mock_dataset.__iter__ = lambda self: iter([
        {"problem_id": "test1", "prompt": "def test(): pass", "canonical_solution": "pass", "test": "pass", "entry_point": "test"},
        {"problem_id": "test2", "prompt": "def foo(): pass", "canonical_solution": "pass", "test": "pass", "entry_point": "foo"}
    ])
    mock_load_dataset.return_value = mock_dataset

    # Mock path to use temp directory
    with patch('code.data.fetcher.OUTPUT_PATH', tmp_path / "test_humaneval.json"):
        with patch('code.data.fetcher.EXPECTED_DATASET_HASH', None):  # Skip hash check
            result_path = fetch_humaneval_dataset()

    assert result_path.exists()
    with open(result_path, 'r') as f:
        data = json.load(f)
    assert len(data) == 2
    assert data[0]["problem_id"] == "test1"

def test_compute_file_sha256(tmp_path):
    """Test SHA-256 computation."""
    test_file = tmp_path / "test.txt"
    test_content = "Hello, World!"
    test_file.write_text(test_content)

    hash_val = compute_file_sha256(test_file)
    assert len(hash_val) == 64  # SHA-256 hex length
    assert isinstance(hash_val, str)

@patch('code.data.fetcher.load_dataset')
def test_fetch_humaneval_failure(mock_load_dataset, tmp_path):
    """Test fetch failure handling."""
    mock_load_dataset.side_effect = Exception("Network error")

    with patch('code.data.fetcher.OUTPUT_PATH', tmp_path / "test_humaneval.json"):
        with pytest.raises(DataFetchError):
            fetch_humaneval_dataset()
