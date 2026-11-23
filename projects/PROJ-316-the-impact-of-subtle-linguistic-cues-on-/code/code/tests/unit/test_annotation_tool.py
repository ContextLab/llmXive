"""
Unit tests for the annotation_tool.py module (T002/T001e).

Tests verify:
1. Loading raw conversations from JSONL.
2. Parsing instruction files.
3. Saving rater logs to JSON.
4. Generating the Gold Standard CSVs from aggregated data.
"""

import json
import tempfile
import csv
from pathlib import Path
import pytest
import pandas as pd

# Import the module under test
from code.src.utils.annotation_tool import (
    load_raw_conversations,
    parse_instructions,
    save_rater_log,
    generate_gold_standard
)


@pytest.fixture
def sample_jsonl(tmp_path):
    """Create a temporary JSONL file with sample conversations."""
    file_path = tmp_path / "conversations.jsonl"
    data = [
        {"conversation_id": "c1", "text": "I think this is good."},
        {"conversation_id": "c2", "text": "Maybe we should try."},
        {"conversation_id": "c3", "text": "It seems correct."}
    ]
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    return file_path


@pytest.fixture
def sample_instructions(tmp_path):
    """Create a temporary instructions file."""
    file_path = tmp_path / "instructions.md"
    content = "# Instructions\nPlease rate authenticity."
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path


def test_load_raw_conversations(sample_jsonl):
    """Test loading conversations from a valid JSONL file."""
    conversations = load_raw_conversations(sample_jsonl)
    assert len(conversations) == 3
    assert conversations[0]["conversation_id"] == "c1"
    assert conversations[0]["text"] == "I think this is good."


def test_load_raw_conversations_missing_file(tmp_path):
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_raw_conversations(tmp_path / "nonexistent.jsonl")


def test_parse_instructions(sample_instructions):
    """Test parsing instructions file."""
    content = parse_instructions(sample_instructions)
    assert "Instructions" in content
    assert "authenticity" in content


def test_save_rater_log(tmp_path):
    """Test saving rater logs to a JSON file."""
    log_path = tmp_path / "rater_log.json"
    rater_id = "R001"
    ratings = [
        {"conversation_id": "c1", "text_content": "Hello", "authenticity_score": 4, "rater_id": "R001", "timestamp": "2023-01-01T00:00:00"}
    ]
    hedges = [
        {"conversation_id": "c1", "text_content": "Hello", "hedge_flags": []}
    ]
    
    save_rater_log(log_path, rater_id, ratings, hedges)
    
    assert log_path.exists()
    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data["rater_id"] == "R001"
    assert len(data["ratings"]) == 1
    assert len(data["hedges"]) == 1


def test_generate_gold_standard(tmp_path):
    """Test generating the final Gold Standard CSVs."""
    output_auth = tmp_path / "gold_standard_50.csv"
    output_hedge = tmp_path / "gold_standard_hedges.csv"
    
    ratings = [
        {
            "conversation_id": "c1",
            "text_content": "I think so.",
            "authenticity_score": 4,
            "rater_id": "R001",
            "timestamp": "2023-01-01"
        },
        {
            "conversation_id": "c2",
            "text_content": "Maybe.",
            "authenticity_score": 3,
            "rater_id": "R001",
            "timestamp": "2023-01-01"
        }
    ]
    
    hedges = [
        {
            "conversation_id": "c1",
            "text_content": "I think so.",
            "hedge_flags": [1] # Index of "think"
        },
        {
            "conversation_id": "c2",
            "text_content": "Maybe.",
            "hedge_flags": [0] # Index of "Maybe"
        }
    ]
    
    generate_gold_standard(ratings, hedges, output_auth, output_hedge)
    
    # Verify Authenticity CSV
    assert output_auth.exists()
    df_auth = pd.read_csv(output_auth)
    assert len(df_auth) == 2
    assert "authenticity_score" in df_auth.columns
    assert df_auth.iloc[0]["authenticity_score"] == 4
    
    # Verify Hedge CSV
    assert output_hedge.exists()
    df_hedge = pd.read_csv(output_hedge)
    assert len(df_hedge) == 2
    assert "hedge_flags" in df_hedge.columns
    # The hedge_flags are stored as JSON strings in CSV
    assert json.loads(df_hedge.iloc[0]["hedge_flags"]) == [1]
    assert json.loads(df_hedge.iloc[1]["hedge_flags"]) == [0]


def test_generate_gold_standard_insufficient_samples(tmp_path):
    """Test that generation works even with empty lists (edge case)."""
    output_auth = tmp_path / "gold_standard_50_empty.csv"
    output_hedge = tmp_path / "gold_standard_hedges_empty.csv"
    
    generate_gold_standard([], [], output_auth, output_hedge)
    
    assert output_auth.exists()
    assert output_hedge.exists()
    
    df_auth = pd.read_csv(output_auth)
    assert len(df_auth) == 0
    assert "conversation_id" in df_auth.columns