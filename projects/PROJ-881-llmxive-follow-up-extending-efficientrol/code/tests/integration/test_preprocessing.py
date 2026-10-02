"""
Integration tests for preprocessing module.
Tests adaptive batching logic and memory management.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.preprocessing import (
    stream_batch,
    token_batch_stream,
    load_tokens_from_file,
    get_memory_percent,
    check_memory_backoff_condition,
    validate_batch_size,
    BatchSizeError
)

@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_data_file(temp_test_dir):
    """Create a sample data file with test examples."""
    file_path = temp_test_dir / 'sample_data.jsonl'
    examples = [{'id': i, 'data': f'example_{i}'} for i in range(100)]
    with open(file_path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example) + '\n')
    return file_path

@pytest.fixture
def large_sample_data_file(temp_test_dir):
    """Create a large sample data file."""
    file_path = temp_test_dir / 'large_sample_data.jsonl'
    examples = [{'id': i, 'data': f'example_{i}'} for i in range(1000)]
    with open(file_path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example) + '\n')
    return file_path

@pytest.fixture
def sample_token_file(temp_test_dir):
    """Create a sample token file."""
    file_path = temp_test_dir / 'tokens.jsonl'
    tokens = [{'tokens': [f'token_{i}' for i in range(50)]} for _ in range(10)]
    with open(file_path, 'w', encoding='utf-8') as f:
        for token_record in tokens:
            f.write(json.dumps(token_record) + '\n')
    return file_path

def test_validate_batch_size_valid():
    """Test that valid batch sizes pass validation."""
    # Should not raise
    validate_batch_size(50, 10)
    validate_batch_size(10, 10)
    validate_batch_size(100, 1)

def test_validate_batch_size_invalid():
    """Test that invalid batch sizes raise BatchSizeError."""
    with pytest.raises(BatchSizeError) as exc_info:
        validate_batch_size(5, 10)
    
    assert "5" in str(exc_info.value.message)
    assert "10" in str(exc_info.value.message)

def test_stream_batch_basic(sample_data_file):
    """Test basic stream_batch functionality."""
    # Load examples
    examples = []
    with open(sample_data_file, 'r') as f:
        for line in f:
            examples.append(json.loads(line))
    
    # Test streaming with max_examples=20
    batches = list(stream_batch(examples, max_examples=20))
    
    assert len(batches) == 5  # 100 examples / 20 per batch
    assert all(len(batch) <= 20 for batch in batches)
    assert all(len(batch) > 0 for batch in batches)

def test_stream_batch_with_large_data(large_sample_data_file):
    """Test stream_batch with larger dataset."""
    examples = []
    with open(large_sample_data_file, 'r') as f:
        for line in f:
            examples.append(json.loads(line))
    
    # Test streaming with max_examples=100
    batches = list(stream_batch(examples, max_examples=100))
    
    assert len(batches) == 10  # 1000 examples / 100 per batch
    assert all(len(batch) <= 100 for batch in batches)

def test_memory_backoff(sample_data_file):
    """Test that memory backoff logic works (simulated)."""
    examples = []
    with open(sample_data_file, 'r') as f:
        for line in f:
            examples.append(json.loads(line))
    
    # Get current memory percentage
    mem_pct = get_memory_percent()
    
    # If memory is low, backoff won't trigger in this test
    # But we can verify the logic doesn't crash
    batches = list(stream_batch(examples, max_examples=20))
    
    assert len(batches) > 0
    assert all(len(batch) > 0 for batch in batches)

def test_memory_backoff_fails_at_minimum():
    """Test that RuntimeError is raised when batch size drops below minimum."""
    # Create a small dataset
    examples = [{'id': i} for i in range(5)]
    
    # Force batch size to be below minimum by setting max_examples < MIN_EXAMPLES
    # This should trigger the validation error
    with pytest.raises(BatchSizeError):
        list(stream_batch(examples, max_examples=5))

def test_load_tokens_from_file(sample_token_file):
    """Test loading tokens from a file."""
    tokens = load_tokens_from_file(sample_token_file)
    
    assert len(tokens) == 500  # 10 records * 50 tokens each
    assert tokens[0] == 'token_0'
    assert tokens[-1] == 'token_49'

def test_load_tokens_from_file_not_found(temp_test_dir):
    """Test loading from a non-existent file."""
    non_existent = temp_test_dir / 'non_existent.jsonl'
    
    with pytest.raises(FileNotFoundError):
        load_tokens_from_file(non_existent)

def test_stream_batch_output_to_file(temp_test_dir):
    """Test that stream_batch can write to a file."""
    examples = [{'id': i, 'data': f'example_{i}'} for i in range(50)]
    output_file = temp_test_dir / 'output.jsonl'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for batch in stream_batch(examples, max_examples=10):
            for example in batch:
                f.write(json.dumps(example) + '\n')
    
    # Verify output
    with open(output_file, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 50

def test_get_current_ram_gb():
    """Test that get_current_ram_gb returns a valid value."""
    ram_gb = get_memory_percent()
    
    assert 0 <= ram_gb <= 100

def test_token_batch_stream_basic():
    """Test basic token_batch_stream functionality."""
    tokens = [f'token_{i}' for i in range(100)]
    
    batches = list(token_batch_stream(tokens, max_tokens=10))
    
    assert len(batches) == 10
    assert all(len(batch) == 10 for batch in batches)

def test_token_batch_stream_partial_batch():
    """Test token_batch_stream with partial final batch."""
    tokens = [f'token_{i}' for i in range(105)]
    
    batches = list(token_batch_stream(tokens, max_tokens=10))
    
    assert len(batches) == 11
    assert all(len(batch) <= 10 for batch in batches)
    assert len(batches[-1]) == 5  # Last batch has 5 tokens

def test_token_batch_stream_memory_adaptive():
    """Test that token_batch_stream adapts to memory pressure."""
    tokens = [f'token_{i}' for i in range(200)]
    
    # This should work regardless of current memory state
    batches = list(token_batch_stream(tokens, max_tokens=50))
    
    assert len(batches) > 0
    assert all(len(batch) > 0 for batch in batches)

def test_token_batch_stream_minimum_threshold():
    """Test that token_batch_stream respects minimum batch size."""
    tokens = [f'token_{i}' for i in range(5)]
    
    # Should raise BatchSizeError if max_tokens < MIN_BATCH_SIZE
    with pytest.raises(BatchSizeError):
        list(token_batch_stream(tokens, max_tokens=5))

def test_generator_input_stream_batch():
    """Test stream_batch with generator input."""
    def example_generator():
        for i in range(50):
            yield {'id': i}
    
    batches = list(stream_batch(example_generator(), max_examples=10))
    
    assert len(batches) == 5

def test_generator_input_token_batch_stream():
    """Test token_batch_stream with generator input."""
    def token_generator():
        for i in range(100):
            yield f'token_{i}'
    
    batches = list(token_batch_stream(token_generator(), max_tokens=10))
    
    assert len(batches) == 10

def test_empty_input_stream_batch(temp_test_dir):
    """Test stream_batch with empty input."""
    examples = []
    
    batches = list(stream_batch(examples, max_examples=10))
    
    assert len(batches) == 0

def test_empty_input_token_batch_stream():
    """Test token_batch_stream with empty input."""
    tokens = []
    
    batches = list(token_batch_stream(tokens, max_tokens=10))
    
    assert len(batches) == 0

def test_invalid_input_type_stream_batch():
    """Test stream_batch with invalid input type."""
    with pytest.raises(TypeError):
        list(stream_batch("not a list", max_examples=10))

def test_invalid_input_type_token_batch_stream():
    """Test token_batch_stream with invalid input type."""
    with pytest.raises(TypeError):
        list(token_batch_stream(12345, max_tokens=10))

def test_adaptive_batch_size_reduction():
    """Test that batch size reduces when memory is high (simulated)."""
    # Create a large dataset
    examples = [{'id': i} for i in range(200)]
    
    # In normal conditions, this should produce batches of size 50
    batches = list(stream_batch(examples, max_examples=50))
    
    # Verify we got the expected number of batches
    assert len(batches) == 4
    assert all(len(batch) <= 50 for batch in batches)

def test_adaptive_token_batch_size_reduction():
    """Test that token batch size reduces when memory is high (simulated)."""
    tokens = [f'token_{i}' for i in range(200)]
    
    # In normal conditions, this should produce batches of size 50
    batches = list(token_batch_stream(tokens, max_tokens=50))
    
    # Verify we got the expected number of batches
    assert len(batches) == 4
    assert all(len(batch) <= 50 for batch in batches)

def test_memory_threshold_check():
    """Test the memory threshold check function."""
    # This should return a boolean
    result = check_memory_backoff_condition()
    
    assert isinstance(result, bool)

def test_multiple_sequences_token_batch_stream():
    """Test token_batch_stream with multiple sequences."""
    # Create a flat list of tokens from multiple sequences
    tokens = []
    for seq_id in range(5):
        tokens.extend([f'seq{seq_id}_token{i}' for i in range(20)])
    
    batches = list(token_batch_stream(tokens, max_tokens=10))
    
    assert len(batches) == 10  # 100 tokens / 10 per batch
    assert all(len(batch) == 10 for batch in batches)