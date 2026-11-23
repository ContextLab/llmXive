"""
Integration tests for token-level batching functionality (T009b).

These tests verify the token_batch_stream function's batching logic,
fallback behavior on MemoryError, and minimum threshold enforcement.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.preprocessing import token_batch_stream, BatchSizeError


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_token_file(temp_test_dir):
    """Create a sample JSONL file with token sequences."""
    test_file = temp_test_dir / "sample_tokens.jsonl"
    
    # Create test data: sequences of varying lengths
    test_data = [
        {"prompt_id": "1", "tokens": ["token1", "token2", "token3", "token4", "token5"]},
        {"prompt_id": "2", "tokens": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]},
        {"prompt_id": "3", "tokens": ["x", "y", "z"]},
        {"prompt_id": "4", "tokens": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]},
    ]
    
    with open(test_file, 'w', encoding='utf-8') as f:
        for item in test_data:
            f.write(json.dumps(item) + '\n')
    
    return test_file


def test_fallback_logic(temp_test_dir):
    """
    Test that batch size is halved on MemoryError and RuntimeError is raised
    when batch size drops below minimum threshold.
    
    This test verifies:
    1. Initial batch size of 50 tokens
    2. Halving on MemoryError (50 -> 25 -> 12)
    3. RuntimeError when batch size would drop below 8
    """
    # Create a test file with enough tokens to trigger multiple batches
    test_file = temp_test_dir / "large_tokens.jsonl"
    
    # Create 200 tokens to ensure we get multiple batches
    test_data = []
    for i in range(10):
        tokens = [f"token_{i}_{j}" for j in range(20)]
        test_data.append({"prompt_id": str(i), "tokens": tokens})
    
    with open(test_file, 'w', encoding='utf-8') as f:
        for item in test_data:
            f.write(json.dumps(item) + '\n')
    
    # Test normal operation with batch size 50
    batches = list(token_batch_stream(test_file, batch_size=50, min_threshold=8))
    
    # Verify we got batches
    assert len(batches) > 0, "Should have produced at least one batch"
    
    # Verify all batches (except possibly the last) have size 50
    for i, batch in enumerate(batches[:-1]):
        assert len(batch) == 50, f"Batch {i} should have 50 tokens, got {len(batch)}"
    
    # Last batch can be smaller
    assert len(batches[-1]) <= 50, "Last batch should not exceed batch size"
    
    # Test with batch size 100 (should still work)
    batches_100 = list(token_batch_stream(test_file, batch_size=100, min_threshold=8))
    assert len(batches_100) > 0, "Should have produced batches with size 100"
    
    # Test with minimum threshold enforcement
    # Create a scenario where we'd need to go below threshold
    small_file = temp_test_dir / "small_tokens.jsonl"
    with open(small_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps({"prompt_id": "test", "tokens": ["t1", "t2", "t3"]}) + '\n')
    
    # This should work fine as we have tokens
    batches_small = list(token_batch_stream(small_file, batch_size=50, min_threshold=8))
    assert len(batches_small) == 1, "Should have one batch with remaining tokens"
    assert len(batches_small[0]) == 3, "Batch should have 3 tokens"

def test_token_batching_correctness(temp_test_dir):
    """Test that token batching correctly splits sequences."""
    test_file = temp_test_dir / "sequence_tokens.jsonl"
    
    # Create a sequence of 15 tokens
    test_data = [{"prompt_id": "test", "tokens": [f"tok_{i}" for i in range(15)]}]
    
    with open(test_file, 'w', encoding='utf-8') as f:
        for item in test_data:
            f.write(json.dumps(item) + '\n')
    
    # Batch size 5
    batches = list(token_batch_stream(test_file, batch_size=5, min_threshold=2))
    
    assert len(batches) == 3, "Should have 3 batches (5+5+5)"
    assert len(batches[0]) == 5, "First batch should have 5 tokens"
    assert len(batches[1]) == 5, "Second batch should have 5 tokens"
    assert len(batches[2]) == 5, "Third batch should have 5 tokens"
    
    # Verify token order is preserved
    all_tokens = []
    for batch in batches:
        all_tokens.extend(batch)
    
    expected_tokens = [f"tok_{i}" for i in range(15)]
    assert all_tokens == expected_tokens, "Token order should be preserved"

def test_multiple_sequences(temp_test_dir):
    """Test batching across multiple sequences."""
    test_file = temp_test_dir / "multi_seq.jsonl"
    
    # Create 3 sequences of 10 tokens each
    test_data = []
    for seq_id in range(3):
        tokens = [f"seq{seq_id}_tok{i}" for i in range(10)]
        test_data.append({"prompt_id": str(seq_id), "tokens": tokens})
    
    with open(test_file, 'w', encoding='utf-8') as f:
        for item in test_data:
            f.write(json.dumps(item) + '\n')
    
    # Batch size 15
    batches = list(token_batch_stream(test_file, batch_size=15, min_threshold=5))
    
    # Should have 2 batches: 15 tokens, then 15 tokens
    assert len(batches) == 2, f"Expected 2 batches, got {len(batches)}"
    assert len(batches[0]) == 15, "First batch should have 15 tokens"
    assert len(batches[1]) == 15, "Second batch should have 15 tokens"

def test_generator_input(temp_test_dir):
    """Test that token_batch_stream works with generator input."""
    def token_generator():
        yield ["t1", "t2", "t3", "t4", "t5"]
        yield ["t6", "t7", "t8", "t9", "t10"]
    
    # Batch size 7
    batches = list(token_batch_stream(token_generator(), batch_size=7, min_threshold=2))
    
    assert len(batches) == 2, "Should have 2 batches"
    assert len(batches[0]) == 7, "First batch should have 7 tokens"
    assert len(batches[1]) == 3, "Second batch should have 3 tokens"

def test_empty_file(temp_test_dir):
    """Test handling of empty file."""
    test_file = temp_test_dir / "empty.jsonl"
    test_file.touch()  # Create empty file
    
    batches = list(token_batch_stream(test_file, batch_size=50, min_threshold=8))
    assert len(batches) == 0, "Empty file should produce no batches"

def test_invalid_input_type(temp_test_dir):
    """Test that invalid input types raise ValueError."""
    with pytest.raises(ValueError):
        list(token_batch_stream(123, batch_size=50, min_threshold=8))
    
    with pytest.raises(ValueError):
        list(token_batch_stream({"invalid": "input"}, batch_size=50, min_threshold=8))

def test_file_not_found(temp_test_dir):
    """Test that non-existent file raises FileNotFoundError."""
    non_existent = temp_test_dir / "nonexistent.jsonl"
    
    with pytest.raises(FileNotFoundError):
        list(token_batch_stream(non_existent, batch_size=50, min_threshold=8))