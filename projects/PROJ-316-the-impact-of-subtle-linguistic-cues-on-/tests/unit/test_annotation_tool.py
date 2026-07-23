"""
Unit tests for the annotation_tool module.
"""
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import csv
import os
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils.annotation_tool import (
    load_raw_conversations,
    parse_instructions,
    save_rater_log,
    generate_gold_standard
)

@pytest.fixture
def sample_jsonl(tmp_path):
    """Creates a temporary JSONL file with sample conversation turns."""
    data = [
        {"conversation_id": "c1", "text": "I think the sky is blue."},
        {"conversation_id": "c2", "text": "Perhaps it will rain."},
        {"conversation_id": "c3", "text": "The data is clear."}
    ]
    file_path = tmp_path / "sample.jsonl"
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    return str(file_path)

@pytest.fixture
def sample_instructions(tmp_path):
    """Creates a temporary markdown file with sample instructions."""
    content = "# Instructions\n\nRate authenticity 1-5."
    file_path = tmp_path / "instructions.md"
    file_path.write_text(content)
    return str(file_path)

def test_load_raw_conversations(sample_jsonl):
    """Test loading a valid JSONL file."""
    turns = load_raw_conversations(sample_jsonl)
    assert len(turns) == 3
    assert turns[0]['conversation_id'] == 'c1'
    assert turns[0]['text'] == "I think the sky is blue."

def test_load_raw_conversations_missing_file():
    """Test loading a non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_raw_conversations("/nonexistent/path.jsonl")

def test_parse_instructions(sample_instructions):
    """Test reading instructions."""
    content = parse_instructions(sample_instructions)
    assert "# Instructions" in content
    assert "Rate authenticity" in content

def test_save_rater_log(tmp_path):
    """Test saving results to CSV."""
    results = [
        {
            'timestamp': '2023-01-01T00:00:00',
            'conversation_id': 'c1',
            'text_content': 'Test text',
            'authenticity_score': 4,
            'hedge_indices': [1]
        }
    ]
    output_path = tmp_path / "log.csv"
    save_rater_log(str(output_path), "test_rater", results)

    assert output_path.exists()
    with open(output_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['rater_id'] == 'test_rater'
        assert rows[0]['authenticity_score'] == '4'
        assert rows[0]['hedge_indices'] == '[1]'

def test_generate_gold_standard(sample_jsonl):
    """Test sampling turns for gold standard."""
    sample = generate_gold_standard(sample_jsonl, "dummy_output", sample_size=2)
    assert len(sample) == 2
    assert all('conversation_id' in t for t in sample)

def test_generate_gold_standard_insufficient_samples(sample_jsonl):
    """Test sampling when requested size > available."""
    # We have 3 items, request 5
    sample = generate_gold_standard(sample_jsonl, "dummy_output", sample_size=5)
    assert len(sample) == 3