"""
Unit tests for the acquire_conversations module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: We are testing the logic, not the actual HuggingFace download in unit tests.
# The real download is tested in integration or manually.
from acquire_conversations import (
    setup_output_directory,
    save_conversations_jsonl,
    OUTPUT_DIR,
    OUTPUT_FILE
)

class TestSetupOutputDirectory:
    def test_creates_directory_if_not_exists(self, tmp_path):
        # Mock the OUTPUT_DIR to use a temp directory
        test_dir = tmp_path / "data" / "raw"
        with patch('acquire_conversations.OUTPUT_DIR', test_dir):
            result = setup_output_directory()
            assert result.exists()
            assert result.is_dir()

    def test_does_not_fail_if_exists(self, tmp_path):
        test_dir = tmp_path / "data" / "raw"
        test_dir.mkdir(parents=True)
        with patch('acquire_conversations.OUTPUT_DIR', test_dir):
            result = setup_output_directory()
            assert result.exists()

class TestSaveConversationsJsonl:
    def test_saves_correct_format(self, tmp_path):
        test_file = tmp_path / "test.jsonl"
        mock_data = [
            {"conversation_id": "1", "text_content": "Hello world", "source": "test"},
            {"conversation_id": "2", "text_content": "Goodbye", "source": "test"}
        ]
        
        save_conversations_jsonl(mock_data, test_file)
        
        assert test_file.exists()
        with open(test_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        # Verify JSON structure
        row1 = json.loads(lines[0])
        assert row1["conversation_id"] == "1"
        assert row1["text_content"] == "Hello world"
        assert "authenticity_score" not in row1 # Expected missing

    def test_raises_on_empty_list(self, tmp_path):
        test_file = tmp_path / "test.jsonl"
        with pytest.raises(ValueError, match="No conversations to save"):
            save_conversations_jsonl([], test_file)

def test_fetch_conversations_logic():
    """
    Test the logic of fetch_conversations by mocking the datasets.load_dataset call.
    This ensures we don't actually hit the network during unit tests.
    """
    from acquire_conversations import fetch_conversations

    mock_item_1 = {"text": "This is a test conversation.", "id": 1}
    mock_item_2 = {"text": "Another conversation.", "id": 2}
    mock_item_3 = {"text": "", "id": 3} # Empty text, should be skipped
    
    # Create a mock iterator
    mock_ds = MagicMock()
    mock_ds.__iter__ = MagicMock(return_value=iter([mock_item_1, mock_item_2, mock_item_3]))

    with patch('acquire_conversations.load_dataset', return_value=mock_ds):
        result = fetch_conversations("fake_dataset", "validation", "text")
    
    assert len(result) == 2
    assert result[0]["text_content"] == "This is a test conversation."
    assert result[1]["text_content"] == "Another conversation."
    assert result[0]["conversation_id"].startswith("fake_dataset_")

def test_fetch_conversations_text_field():
    """
    Test fetching with a different text field name (e.g., 'dialogue').
    """
    from acquire_conversations import fetch_conversations

    mock_item = {"dialogue": "Movie dialogue text", "id": 1}
    mock_ds = MagicMock()
    mock_ds.__iter__ = MagicMock(return_value=iter([mock_item]))

    with patch('acquire_conversations.load_dataset', return_value=mock_ds):
        result = fetch_conversations("movie_dataset", "train", "dialogue")
    
    assert len(result) == 1
    assert result[0]["text_content"] == "Movie dialogue text"