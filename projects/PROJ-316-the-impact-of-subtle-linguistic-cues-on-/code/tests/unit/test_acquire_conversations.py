import json
import os
import tempfile
from pathlib import Path
import pytest

# Mock the datasets library to avoid actual network calls during unit tests
# This ensures the logic of the script is tested without external dependencies
from unittest.mock import patch, MagicMock

# Import the functions to test
# Note: The script is in code/code/acquire_conversations.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from acquire_conversations import setup_output_directory, save_conversations_jsonl

class TestSetupOutputDirectory:
    def test_creates_directory(self, tmp_path):
        output_file = tmp_path / "sub" / "data.jsonl"
        setup_output_directory(output_file)
        assert output_file.parent.exists()

    def test_existing_directory(self, tmp_path):
        output_file = tmp_path / "data.jsonl"
        setup_output_directory(output_file)
        assert output_file.parent.exists()

class TestSaveConversationsJsonl:
    def test_saves_correctly(self, tmp_path):
        output_file = tmp_path / "conversations.jsonl"
        data = [
            {"conversation_id": "1", "text_content": "Hello world"},
            {"conversation_id": "2", "text_content": "Goodbye"}
        ]
        save_conversations_jsonl(data, output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 2
        
        # Verify JSON validity
        parsed = [json.loads(line) for line in lines]
        assert parsed[0]["conversation_id"] == "1"
        assert parsed[1]["text_content"] == "Goodbye"

    def test_empty_list(self, tmp_path):
        output_file = tmp_path / "empty.jsonl"
        save_conversations_jsonl([], output_file)
        assert output_file.exists()
        assert output_file.stat().st_size == 0

@pytest.fixture
def mock_dataset_item():
    return {
        "dialogue": ["Hello", "Hi there", "How are you?"],
        "id": 123
    }

@pytest.fixture
def mock_dataset_text_item():
    return {
        "text": "This is a single text block conversation.",
        "id": 456
    }

# Integration-style test for the fetch logic (mocked)
@patch('acquire_conversations.load_dataset')
def test_fetch_conversations_logic(mock_load_dataset, mock_dataset_item):
    from acquire_conversations import fetch_conversations
    
    # Setup mock
    mock_dataset = MagicMock()
    mock_dataset.__iter__ = MagicMock(return_value=iter([mock_dataset_item, mock_dataset_item]))
    mock_load_dataset.return_value = mock_dataset
    
    result = fetch_conversations(dataset_name="convai2", split="train")
    
    assert len(result) == 2
    assert "conversation_id" in result[0]
    assert "text_content" in result[0]
    assert "Hello Hi there How are you?" in result[0]["text_content"]

@patch('acquire_conversations.load_dataset')
def test_fetch_conversations_text_field(mock_load_dataset, mock_dataset_text_item):
    from acquire_conversations import fetch_conversations
    
    mock_dataset = MagicMock()
    mock_dataset.__iter__ = MagicMock(return_value=iter([mock_dataset_text_item]))
    mock_load_dataset.return_value = mock_dataset
    
    result = fetch_conversations(dataset_name="cornell", split="train")
    
    assert len(result) == 1
    assert result[0]["text_content"] == "This is a single text block conversation."