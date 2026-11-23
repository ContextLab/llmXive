import os
import tempfile
import json
import pandas as pd
from pathlib import Path
import pytest

# Import the function we are testing
# Note: We are testing the logic inside ingestion.py
# Since ingestion.py is a script, we import the function if it's exposed or mock the module
# The API surface says: from ingestion import extract_metadata_and_log_exclusions
from ingestion import extract_metadata_and_log_exclusions

def test_filter_null_labels():
    """Test that records with null labels are excluded and logged."""
    data = {
        'participant_id': ['P1', 'P2', 'P3'],
        'label': ['Control', None, 'AD'],
        'text': ['This is a long enough text for testing purposes.', 'Short', 'Another valid text here.']
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "exclusions.log"
        result = extract_metadata_and_log_exclusions(df, log_path)
        
        # P2 should be excluded
        assert len(result) == 2
        assert 'P2' not in result['participant_id'].values
        
        # Check log file
        assert log_path.exists()
        with open(log_path, 'r') as f:
            content = f.read()
        assert 'P2,NULL_LABEL' in content

def test_filter_short_text():
    """Test that records with text < 50 words are excluded and logged."""
    # Create a text with 49 words
    short_text = " ".join(["word"] * 49)
    long_text = " ".join(["word"] * 51)
    
    data = {
        'participant_id': ['P1', 'P2', 'P3'],
        'label': ['Control', 'AD', 'Control'],
        'text': [long_text, short_text, long_text]
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "exclusions.log"
        result = extract_metadata_and_log_exclusions(df, log_path)
        
        # P2 should be excluded
        assert len(result) == 2
        assert 'P2' not in result['participant_id'].values
        
        # Check log file
        assert log_path.exists()
        with open(log_path, 'r') as f:
            content = f.read()
        assert 'P2,TEXT_TOO_SHORT' in content

def test_filter_both_conditions():
    """Test exclusion when both conditions might apply (priority to null label)."""
    short_text = " ".join(["word"] * 10)
    
    data = {
        'participant_id': ['P1', 'P2'],
        'label': [None, 'AD'],
        'text': [short_text, short_text]
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "exclusions.log"
        result = extract_metadata_and_log_exclusions(df, log_path)
        
        # Both should be excluded
        assert len(result) == 0
        
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        # P1: NULL_LABEL
        assert any('P1,NULL_LABEL' in line for line in lines)
        # P2: TEXT_TOO_SHORT (since label is not null)
        assert any('P2,TEXT_TOO_SHORT' in line for line in lines)

def test_no_exclusions():
    """Test that valid records are kept."""
    long_text = " ".join(["word"] * 60)
    
    data = {
        'participant_id': ['P1', 'P2'],
        'label': ['Control', 'AD'],
        'text': [long_text, long_text]
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "exclusions.log"
        result = extract_metadata_and_log_exclusions(df, log_path)
        
        assert len(result) == 2
        assert set(result['participant_id']) == {'P1', 'P2'}
        
        # Log should only have header
        with open(log_path, 'r') as f:
            content = f.read()
        assert content.count('\n') == 1 # Header only
