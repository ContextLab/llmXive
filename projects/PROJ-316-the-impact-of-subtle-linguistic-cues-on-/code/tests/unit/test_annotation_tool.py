"""
Unit tests for the annotation tool.
"""

import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import csv
import os

from src.utils.annotation_tool import (
    load_raw_conversations,
    parse_instructions,
    save_rater_log,
    generate_gold_standard
)

# Fixtures
@pytest.fixture
def sample_jsonl(tmp_path):
    """Create a temporary JSONL file with sample conversations."""
    filepath = tmp_path / "conversations.jsonl"
    data = [
        {"conversation_id": "c1", "text": "Maybe I think it is so."},
        {"conversation_id": "c2", "text": "It is definitely true."},
        {"conversation_id": "c3", "text": "Perhaps we should try."}
    ]
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    return filepath

@pytest.fixture
def sample_instructions(tmp_path):
    """Create a temporary instructions markdown file."""
    filepath = tmp_path / "instructions.md"
    content = """
    # Annotation Instructions

    ## Likert Scale
    1: Not Authentic
    2: Somewhat Not Authentic
    3: Neutral
    4: Somewhat Authentic
    5: Very Authentic

    ## Hedges
    Mark words like 'maybe', 'perhaps', 'think'.
    """
    filepath.write_text(content)
    return filepath

# Tests for load_raw_conversations
def test_load_raw_conversations(sample_jsonl):
    conversations = load_raw_conversations(sample_jsonl)
    assert len(conversations) == 3
    assert conversations[0]["conversation_id"] == "c1"
    assert conversations[0]["text"] == "Maybe I think it is so."

def test_load_raw_conversations_missing_file():
    with pytest.raises(FileNotFoundError):
        load_raw_conversations(Path("nonexistent.jsonl"))

# Tests for parse_instructions
def test_parse_instructions(sample_instructions):
    instructions = parse_instructions(sample_instructions)
    assert "Likert" in instructions["raw_content"]
    assert 1 in instructions["likert_scale"]
    assert instructions["likert_scale"][1] == "Not Authentic"
    assert instructions["likert_scale"][5] == "Very Authentic"

# Tests for save_rater_log
def test_save_rater_log(tmp_path):
    logs = [
        {
            "conversation_id": "c1",
            "text_content": "Hello",
            "authenticity_score": 4,
            "rater_id": "r1",
            "timestamp": "2023-01-01T00:00:00"
        }
    ]
    output_dir = tmp_path / "logs"
    filepath = save_rater_log(logs, output_dir, "authenticity", "r1")

    assert filepath.exists()
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["conversation_id"] == "c1"
        assert rows[0]["authenticity_score"] == "4"

def test_save_rater_log_hedges(tmp_path):
    logs = [
        {
            "conversation_id": "c1",
            "text_content": "Maybe hello",
            "hedge_flags": [0],
            "rater_id": "r1",
            "timestamp": "2023-01-01T00:00:00"
        }
    ]
    output_dir = tmp_path / "logs"
    filepath = save_rater_log(logs, output_dir, "hedges", "r1")

    assert filepath.exists()
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert json.loads(rows[0]["hedge_flags"]) == [0]

# Tests for generate_gold_standard
def test_generate_gold_standard():
    logs = [
        {
            "conversation_id": "c1",
            "text_content": "Hello",
            "authenticity_score": 5,
            "rater_id": "r1",
            "timestamp": "2023-01-01T00:00:00"
        },
        {
            "conversation_id": "c2",
            "text_content": "World",
            "authenticity_score": 3,
            "rater_id": "r1",
            "timestamp": "2023-01-01T00:00:01"
        }
    ]
    gold = generate_gold_standard(logs, "authenticity")
    assert len(gold) == 2
    assert gold[0]["authenticity_score"] == 5
    assert gold[1]["authenticity_score"] == 3

def test_generate_gold_standard_insufficient_samples():
    logs = []
    gold = generate_gold_standard(logs, "authenticity")
    assert len(gold) == 0