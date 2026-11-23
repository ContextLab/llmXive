"""
Unit tests for the stream_loader module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.lib.stream_loader import stream_jsonl_file, stream_and_batch, get_file_line_count


@pytest.fixture
def temp_jsonl_file():
    """Create a temporary JSONL file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        data = [
            {"id": 1, "text": "First record"},
            {"id": 2, "text": "Second record"},
            {"id": 3, "text": "Third record"},
            {"id": 4, "text": "Fourth record"},
            {"id": 5, "text": "Fifth record"}
        ]
        for item in data:
            f.write(json.dumps(item) + '\n')
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def empty_jsonl_file():
    """Create an empty temporary JSONL file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def malformed_jsonl_file():
    """Create a temporary JSONL file with malformed JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"id": 1, "text": "Valid"}\n')
        f.write('{"id": 2, text: "Invalid JSON"}\n') # Missing quotes around key
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


def test_stream_jsonl_file_success(temp_jsonl_file):
    """Test successful streaming of a valid JSONL file."""
    records = list(stream_jsonl_file(temp_jsonl_file))
    assert len(records) == 5
    assert records[0]["id"] == 1
    assert records[0]["text"] == "First record"
    assert records[4]["id"] == 5


def test_stream_jsonl_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        list(stream_jsonl_file("non_existent_file.jsonl"))


def test_stream_jsonl_file_malformed(malformed_jsonl_file):
    """Test that RuntimeError is raised for malformed JSON."""
    with pytest.raises(RuntimeError, match="Corrupt JSON data"):
        list(stream_jsonl_file(malformed_jsonl_file))


def test_stream_and_batch(temp_jsonl_file):
    """Test streaming with batching."""
    batches = list(stream_and_batch(temp_jsonl_file, batch_size=2))
    assert len(batches) == 3 # 2, 2, 1
    assert len(batches[0]) == 2
    assert len(batches[1]) == 2
    assert len(batches[2]) == 1


def test_stream_and_batch_empty_file(empty_jsonl_file):
    """Test streaming an empty file yields no batches."""
    batches = list(stream_and_batch(empty_jsonl_file))
    assert len(batches) == 0


def test_get_file_line_count(temp_jsonl_file):
    """Test line counting."""
    count = get_file_line_count(temp_jsonl_file)
    assert count == 5


def test_get_file_line_count_not_found():
    """Test line counting raises error for missing file."""
    with pytest.raises(FileNotFoundError):
        get_file_line_count("non_existent_file.jsonl")