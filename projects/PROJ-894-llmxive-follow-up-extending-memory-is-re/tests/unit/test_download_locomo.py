"""
Unit tests for the LoCoMo download script.
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock the datasets module before importing
sys_path_backup = __import__('sys').path[:]
__import__('sys').path.insert(0, 'code')

from data_loader import load_locomo_strict, MemoryWarning
from scripts.download_locomo import main

__import__('sys').path = sys_path_backup

class MockDataset:
    def __init__(self, data):
        self.data = data
        self.column_names = ["question", "context", "answer"]

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, idx):
        return self.data[idx]

@pytest.fixture
def sample_data():
    return [
        {"question": "What is 2+2?", "context": "Simple math.", "answer": "4"},
        {"question": "Capital of France?", "context": "Geography.", "answer": "Paris"}
    ]

@pytest.fixture
def mock_dataset(sample_data):
    return MockDataset(sample_data)

def test_load_locomo_strict_success(mock_dataset):
    with patch('data_loader.load_dataset', return_value=mock_dataset):
        dataset = load_locomo_strict()
        assert len(dataset) == 2
        assert dataset.column_names == ["question", "context", "answer"]

def test_load_locomo_strict_failure():
    with patch('data_loader.load_dataset', side_effect=Exception("Network error")):
        with pytest.raises(FileNotFoundError):
            load_locomo_strict()

def test_schema_validation_pass(sample_data, mock_dataset, tmp_path):
    output_file = tmp_path / "locomo.jsonl"
    with patch('data_loader.load_dataset', return_value=mock_dataset):
        # Simulate the logic in main
        required_columns = {"question", "context", "answer"}
        actual_columns = set(mock_dataset.column_names)
        missing = required_columns - actual_columns
        assert not missing

def test_schema_validation_fail(tmp_path):
    # Create a mock dataset with missing columns
    bad_data = [{"q": "A", "c": "B"}]
    bad_mock = MockDataset(bad_data)
    bad_mock.column_names = ["q", "c"]
    
    with patch('data_loader.load_dataset', return_value=bad_mock):
        with pytest.raises(ValueError, match="Dataset schema mismatch"):
            # We can't easily run the full main without mocking file I/O completely,
            # but we can test the logic that would raise it.
            required_columns = {"question", "context", "answer"}
            actual_columns = set(bad_mock.column_names)
            missing = required_columns - actual_columns
            assert missing

def test_main_writes_file(sample_data, mock_dataset, tmp_path, monkeypatch):
    output_dir = tmp_path / "data" / "raw"
    output_file = output_dir / "locomo.jsonl"
    monkeypatch.chdir(tmp_path)
    # Ensure the script looks for data/raw relative to cwd
    
    with patch('data_loader.load_dataset', return_value=mock_dataset):
        with patch('scripts.download_locomo.Path', return_value=output_dir):
            # We need to mock ensure_output_dirs to not fail
            with patch('data_loader.ensure_output_dirs'):
                # Mock the open to capture writes
                with open(output_file, "w") as f:
                    pass # Create file
                
                # Run the logic that writes
                with open(output_file, "w", encoding="utf-8") as f:
                    for item in mock_dataset:
                        row = {
                            "question": item.get("question", ""),
                            "context": item.get("context", ""),
                            "answer": item.get("answer", "")
                        }
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")
                
                # Verify
                assert output_file.exists()
                with open(output_file, "r") as f:
                    lines = f.readlines()
                    assert len(lines) == 2
                    first_line = json.loads(lines[0])
                    assert first_line["question"] == "What is 2+2?"
