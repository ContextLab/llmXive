import json
import os
import tempfile
from pathlib import Path
import pytest

from data.preprocess import (
    build_vocabulary, 
    apply_vocabulary_filter, 
    UNKNOWN_TOKEN, 
    DEFAULT_VOCAB_SIZE
)

def test_build_vocabulary_top_n():
    """Test that vocabulary is limited to top-N stations."""
    data = [
        {"stops": ["A", "A", "A", "B", "B", "C"]},
        {"stops": ["A", "B", "C", "D"]}
    ]
    # A appears 4 times, B 3 times, C 2 times, D 1 time
    
    # Request top 2
    vocab = build_vocabulary(data, top_n=2)
    
    assert len(vocab) == 2
    assert "A" in vocab
    assert "B" in vocab
    assert "C" not in vocab
    assert "D" not in vocab

def test_apply_vocabulary_filter_replaces_unknown():
    """Test that stations not in vocab are replaced with UNKNOWN."""
    data = [
        {"stops": ["A", "B", "C", "D"]},
        {"stops": ["A", "A", "E"]}
    ]
    
    # Create vocab with only A and B
    vocab = {"A": 0, "B": 1}
    
    result = apply_vocabulary_filter(data, vocab)
    
    # First route: C and D should be UNKNOWN
    assert result[0]["stops"] == ["A", "B", UNKNOWN_TOKEN, UNKNOWN_TOKEN]
    # Second route: E should be UNKNOWN
    assert result[1]["stops"] == ["A", "A", UNKNOWN_TOKEN]

def test_apply_vocabulary_filter_preserves_known():
    """Test that stations in vocab are preserved."""
    data = [
        {"stops": ["A", "B", "C"]}
    ]
    
    vocab = {"A": 0, "B": 1, "C": 2}
    
    result = apply_vocabulary_filter(data, vocab)
    
    assert result[0]["stops"] == ["A", "B", "C"]

def test_apply_vocabulary_filter_empty_stops():
    """Test handling of routes with no stops."""
    data = [
        {"stops": []},
        {"other_field": "value"}
    ]
    
    vocab = {"A": 0}
    
    result = apply_vocabulary_filter(data, vocab)
    
    assert result[0]["stops"] == []
    # Route without stops key should remain unchanged (or handled gracefully)
    assert "other_field" in result[1]

def test_integration_vocab_restriction():
    """Integration test: Build vocab and filter in one flow."""
    # Create sample data
    data = [
        {"city": "Beijing", "stops": ["Station1"] * 100 + ["StationRare"]},
        {"city": "Shanghai", "stops": ["Station1"] * 50 + ["Station2"] * 40 + ["Station3"]},
    ]
    
    # Build vocab of top 2
    vocab = build_vocabulary(data, top_n=2)
    
    # Apply filter
    filtered = apply_vocabulary_filter(data, vocab)
    
    # Check that StationRare and Station3 are replaced
    assert filtered[0]["stops"][-1] == UNKNOWN_TOKEN
    assert filtered[1]["stops"][-1] == UNKNOWN_TOKEN
    
    # Check that Station1 and Station2 are preserved
    assert filtered[0]["stops"][0] == "Station1"
    assert "Station1" in filtered[1]["stops"]
    assert "Station2" in filtered[1]["stops"]
