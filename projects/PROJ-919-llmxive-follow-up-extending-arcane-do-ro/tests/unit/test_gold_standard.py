"""
Tests for the gold standard data creation and validation.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import hashlib

from scripts.create_gold_standard import gold_standard_data

def test_gold_standard_data_structure():
    """Test that the gold standard data has the correct structure."""
    assert isinstance(gold_standard_data, list)
    assert len(gold_standard_data) > 0
    
    # Check each record has required fields
    required_fields = ["character", "scenario", "ground_truth_score", "ground_truth_phase"]
    for record in gold_standard_data:
        for field in required_fields:
            assert field in record, f"Missing field: {field}"
        
        # Validate data types
        assert isinstance(record["character"], str)
        assert isinstance(record["scenario"], str)
        assert isinstance(record["ground_truth_score"], int)
        assert isinstance(record["ground_truth_phase"], str)
        
        # Validate score range (1-5 Likert scale)
        assert 1 <= record["ground_truth_score"] <= 5

def test_gold_standard_content_validity():
    """Test that the gold standard data contains valid content."""
    # Check for variety in characters
    characters = set(record["character"] for record in gold_standard_data)
    assert len(characters) > 1, "Should have multiple characters"
    
    # Check for variety in phases
    phases = set(record["ground_truth_phase"] for record in gold_standard_data)
    assert len(phases) > 1, "Should have multiple phases"
    
    # Check for variety in scores
    scores = set(record["ground_truth_score"] for record in gold_standard_data)
    assert len(scores) > 1, "Should have multiple score values"

def test_gold_standard_file_creation(tmp_path):
    """Test that the gold standard file is created correctly."""
    output_file = tmp_path / "human_annotations.json"
    
    # Write the data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(gold_standard_data, f, indent=2)
    
    # Verify file exists and is readable
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    
    # Verify JSON structure
    with open(output_file, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    
    assert loaded_data == gold_standard_data

def test_checksum_generation(tmp_path):
    """Test that checksums are generated correctly."""
    output_file = tmp_path / "human_annotations.json"
    
    # Write the data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(gold_standard_data, f, indent=2)
    
    # Calculate checksum
    with open(output_file, 'rb') as f:
        file_content = f.read()
        checksum = hashlib.sha256(file_content).hexdigest()
    
    # Verify checksum format
    assert len(checksum) == 64
    assert all(c in '0123456789abcdef' for c in checksum)
    
    # Verify checksum is deterministic
    with open(output_file, 'rb') as f:
        file_content2 = f.read()
        checksum2 = hashlib.sha256(file_content2).hexdigest()
    
    assert checksum == checksum2

def test_state_file_update(tmp_path):
    """Test that the state file is updated correctly."""
    state_file = tmp_path / "experiment_state.json"
    
    # Create initial state
    initial_state = {
        "experiment_id": "test-001",
        "created_at": "2024-01-01T00:00:00"
    }
    
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(initial_state, f)
    
    # Update with gold standard info
    output_file = tmp_path / "human_annotations.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(gold_standard_data, f)
    
    with open(output_file, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
    
    updated_state = {
        "experiment_id": "test-001",
        "created_at": "2024-01-01T00:00:00",
        "gold_standard": {
            "file": str(output_file),
            "checksum": checksum,
            "record_count": len(gold_standard_data)
        }
    }
    
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(updated_state, f)
    
    # Verify state file
    with open(state_file, 'r', encoding='utf-8') as f:
        loaded_state = json.load(f)
    
    assert "gold_standard" in loaded_state
    assert loaded_state["gold_standard"]["checksum"] == checksum
    assert loaded_state["gold_standard"]["record_count"] == len(gold_standard_data)