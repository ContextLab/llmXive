"""
Unit tests for the annotation tool module.

These tests verify the core functionality of T001c:
- Loading raw conversations
- Calculating mock authenticity scores
- Generating the gold standard dataset
"""
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import csv
import os
from code.src.utils.annotation_tool import (
    load_raw_conversations,
    calculate_mock_authenticity,
    generate_gold_standard
)

@pytest.fixture
def sample_jsonl(tmp_path):
    """Create a temporary JSONL file with sample conversations."""
    file_path = tmp_path / "conversations.jsonl"
    data = [
        {"conversation_id": "conv_001", "text_content": "I think this might work."},
        {"conversation_id": "conv_002", "text_content": "This is definitely the answer."},
        {"conversation_id": "conv_003", "text_content": "Perhaps we should consider other options."},
        {"conversation_id": "conv_004", "text_content": "I believe the data suggests otherwise."},
        {"conversation_id": "conv_005", "text_content": "It seems like a reasonable approach."},
    ]
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    return file_path

def test_load_raw_conversations(sample_jsonl):
    """Test loading conversations from a JSONL file."""
    conversations = load_raw_conversations(sample_jsonl)
    
    assert len(conversations) == 5
    assert conversations[0]['conversation_id'] == 'conv_001'
    assert 'text_content' in conversations[0]

def test_load_raw_conversations_missing_file(tmp_path):
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        load_raw_conversations(tmp_path / "nonexistent.jsonl")

def test_calculate_mock_authenticity_hedges():
    """Test that text with hedges gets higher authenticity scores."""
    text_with_hedges = "I think this might be correct, perhaps."
    text_without_hedges = "This is definitely correct."
    
    score_with = calculate_mock_authenticity(text_with_hedges, seed=42)
    score_without = calculate_mock_authenticity(text_without_hedges, seed=42)
    
    # Scores should be different due to hedge presence
    assert score_with != score_without

def test_calculate_mock_authenticity_no_hedges():
    """Test scoring of text without hedges."""
    text = "The answer is clear and definite."
    score = calculate_mock_authenticity(text, seed=42)
    
    assert 1.0 <= score <= 5.0

def test_generate_gold_standard(sample_jsonl, tmp_path):
    """Test generation of the gold standard dataset."""
    output_path = tmp_path / "gold_standard.csv"
    metadata_path = tmp_path / "metadata.json"
    
    conversations = load_raw_conversations(sample_jsonl)
    df = generate_gold_standard(
        conversations,
        output_path,
        metadata_path,
        n_samples=3,
        seed=42
    )
    
    # Check DataFrame
    assert len(df) == 3
    assert 'conversation_id' in df.columns
    assert 'text_content' in df.columns
    assert 'authenticity_score' in df.columns
    assert 'rater_id' in df.columns
    assert 'timestamp' in df.columns
    
    # Check CSV file exists
    assert output_path.exists()
    
    # Check metadata file exists
    assert metadata_path.exists()
    
    # Verify metadata content
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    assert 'rater_id' in metadata
    assert 'scale' in metadata

def test_generate_gold_standard_insufficient_samples(sample_jsonl, tmp_path):
    """Test error when requesting more samples than available."""
    output_path = tmp_path / "gold_standard.csv"
    metadata_path = tmp_path / "metadata.json"
    
    conversations = load_raw_conversations(sample_jsonl)
    
    with pytest.raises(ValueError, match="Cannot sample 10 turns from 5 available"):
        generate_gold_standard(
            conversations,
            output_path,
            metadata_path,
            n_samples=10,
            seed=42
        )
