"""
Unit tests for vocabulary alignment validation logic (T065).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from model_analyzer import validate_cross_lingual_vocab_alignment, VocabularyAlignmentError

class MockTokenizer:
    def __init__(self, vocab_dict):
        self.vocab = vocab_dict
        self._vocab_values = set(vocab_dict.values())
    
    def get_vocab(self):
        return self.vocab

def test_vocab_alignment_passes():
    """Test that validation passes when intersection is sufficient."""
    # Create mock tokenizers with large intersection
    vocab_a = {f"token_{i}": i for i in range(15000)}
    vocab_b = {f"token_{i}": i for i in range(15000)}
    vocab_c = {f"token_{i}": i for i in range(15000)}
    
    tokenizer_map = {
        "model_a": MockTokenizer(vocab_a),
        "model_b": MockTokenizer(vocab_b),
        "model_c": MockTokenizer(vocab_c)
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "vocab_warning.json"
        result = validate_cross_lingual_vocab_alignment(
            tokenizer_map, 
            min_intersection_size=10000,
            output_path=output_path
        )
        
        assert result is True
        assert not output_path.exists()

def test_vocab_alignment_fails_writes_warning():
    """Test that validation fails and writes warning JSON when intersection is small."""
    # Create mock tokenizers with small intersection (only 5000 common tokens)
    vocab_a = {f"token_{i}": i for i in range(10000)}
    vocab_b = {f"token_{i}": i for i in range(5000, 15000)}  # Overlap: 5000
    vocab_c = {f"token_{i}": i for i in range(5000, 15000)}  # Overlap: 5000
    
    tokenizer_map = {
        "model_a": MockTokenizer(vocab_a),
        "model_b": MockTokenizer(vocab_b),
        "model_c": MockTokenizer(vocab_c)
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "vocab_warning.json"
        result = validate_cross_lingual_vocab_alignment(
            tokenizer_map,
            min_intersection_size=10000,
            output_path=output_path
        )
        
        assert result is False
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            warning_data = json.load(f)
        
        assert warning_data["status"] == "warning"
        assert warning_data["intersection_size"] == 5000
        assert warning_data["min_required"] == 10000
        assert "CRITICAL" in warning_data["message"]

def test_vocab_alignment_empty_intersection():
    """Test validation with no common vocabulary."""
    vocab_a = {f"token_{i}": i for i in range(10000)}
    vocab_b = {f"token_{i}": i + 100000 for i in range(10000)}  # No overlap
    
    tokenizer_map = {
        "model_a": MockTokenizer(vocab_a),
        "model_b": MockTokenizer(vocab_b)
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "vocab_warning.json"
        result = validate_cross_lingual_vocab_alignment(
            tokenizer_map,
            min_intersection_size=10000,
            output_path=output_path
        )
        
        assert result is False
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            warning_data = json.load(f)
        
        assert warning_data["intersection_size"] == 0
        assert "CRITICAL" in warning_data["message"]

def test_vocab_alignment_insufficient_models():
    """Test validation with only one model."""
    vocab_a = {f"token_{i}": i for i in range(10000)}
    
    tokenizer_map = {
        "model_a": MockTokenizer(vocab_a)
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "vocab_warning.json"
        result = validate_cross_lingual_vocab_alignment(
            tokenizer_map,
            min_intersection_size=10000,
            output_path=output_path
        )
        
        # Should return True (no error) but log warning
        assert result is True
        assert not output_path.exists()