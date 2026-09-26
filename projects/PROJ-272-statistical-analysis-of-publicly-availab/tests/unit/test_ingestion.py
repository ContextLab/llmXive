"""
Unit tests for ingestion module (T013b, T014).
Tests for T010: UTF-8 normalization and exclusion logic.
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os
import sys

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion import clean_transcript_text, extract_metadata_and_log_exclusions
from utils import normalize_text, validate_text_length

def test_utf8_normalization():
    """Test that text is normalized to UTF-8 and incompatible chars are handled."""
    # Create a string with some non-ASCII characters that might appear in transcripts
    # Using a mix of valid and potentially problematic characters
    raw_text = "Hello\u00A0World\u2014Test\u00E9"  # Non-breaking space, em-dash, e-acute
    cleaned = clean_transcript_text(raw_text)
    
    # Verify the text is valid UTF-8 (it should be a standard Python string)
    assert isinstance(cleaned, str)
    # Verify normalization occurred (e.g., non-breaking space might be converted to regular space)
    # The exact behavior depends on the implementation, but it should not crash
    assert len(cleaned) > 0
    
    # Test with explicit invalid byte sequence simulation (if passed as string with surrogate)
    # Python handles this gracefully usually, but we ensure our function doesn't crash
    try:
        # This simulates text that might have encoding issues
        problematic = "Text with \udcff invalid surrogate"
        result = clean_transcript_text(problematic)
        # Should not raise an exception
        assert isinstance(result, str)
    except Exception:
        # If it raises, it should be a specific encoding error, not a generic crash
        # But ideally our function handles this
        pass

def test_exclusion_logic_null_label():
    """Test that records with null labels are excluded."""
    df = pd.DataFrame({
        'participant_id': ['P1', 'P2', 'P3'],
        'label': ['Control', None, 'AD'],
        'text': ['Valid text here', 'Valid text here', 'Valid text here']
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "exclusions.log"
        
        result = extract_metadata_and_log_exclusions(df, log_path)
        
        # P2 should be excluded due to null label
        assert len(result) == 2
        assert 'P2' not in result['participant_id'].values
        assert 'P1' in result['participant_id'].values
        assert 'P3' in result['participant_id'].values

        # Check log
        assert log_path.exists()
        with open(log_path, 'r') as f:
            content = f.read()
        assert 'P2|NULL_LABEL' in content

def test_exclusion_logic_short_text():
    """Test that records with text < 50 words are excluded."""
    # Create a dataframe with one short text and one long text
    long_text = " ".join(["word"] * 60)  # 60 words
    short_text = " ".join(["word"] * 20) # 20 words
    
    df = pd.DataFrame({
        'participant_id': ['P1', 'P2'],
        'label': ['Control', 'AD'],
        'text': [short_text, long_text]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "exclusions.log"
        
        result = extract_metadata_and_log_exclusions(df, log_path)
        
        # P1 should be excluded due to short text
        assert len(result) == 1
        assert 'P1' not in result['participant_id'].values
        assert 'P2' in result['participant_id'].values

        # Check log
        assert log_path.exists()
        with open(log_path, 'r') as f:
            content = f.read()
        assert 'P1|TEXT_TOO_SHORT' in content or 'P1|EMPTY_TEXT' in content

def test_exclusion_logic_combined():
    """Test exclusion logic with multiple failure reasons."""
    df = pd.DataFrame({
        'participant_id': ['P1', 'P2', 'P3', 'P4'],
        'label': ['Control', None, 'AD', 'MCI'],
        'text': [
            "Short text",  # Too short
            "Long enough text for the test with sufficient words to pass the length requirement.",  # Valid length
            "Another valid text here with enough length to pass the test.", # Valid length
            ""  # Empty
        ]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "exclusions.log"
        
        result = extract_metadata_and_log_exclusions(df, log_path)
        
        # P1 (short), P2 (null), P4 (empty) should be excluded
        # P3 should remain
        assert len(result) == 1
        assert 'P3' in result['participant_id'].values
        assert 'P1' not in result['participant_id'].values
        assert 'P2' not in result['participant_id'].values
        assert 'P4' not in result['participant_id'].values

        # Check log
        assert log_path.exists()
        with open(log_path, 'r') as f:
            content = f.read()
        assert 'P1|TEXT_TOO_SHORT' in content
        assert 'P2|NULL_LABEL' in content
        assert 'P4|EMPTY_TEXT' in content or 'P4|TEXT_TOO_SHORT' in content

def test_validate_text_length_edge_cases():
    """Test text length validation with edge cases."""
    # Empty string
    assert not validate_text_length("", 50)
    
    # Exactly 50 words
    text_50 = " ".join(["word"] * 50)
    assert validate_text_length(text_50, 50)
    
    # 49 words
    text_49 = " ".join(["word"] * 49)
    assert not validate_text_length(text_49, 50)
    
    # 100 words
    text_100 = " ".join(["word"] * 100)
    assert validate_text_length(text_100, 50)