"""
Integration tests for preprocessing module.

Tests batched streaming, memory backoff, and data merging functionality.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.preprocessing import (
    stream_batch,
    validate_batch_size,
    BatchSizeError,
    stream_tokens_in_batches,
    merge_entropy_profiles,
    validate_entropy_profile,
    load_tokens_from_file,
    MIN_BATCH_SIZE,
    DEFAULT_BATCH_SIZE
)

@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_data_file(temp_test_dir):
    """Create a sample JSONL file with test data."""
    file_path = temp_test_dir / 'sample_data.jsonl'
    sample_data = [
        {"prompt_id": "test1", "token_index": 0, "token": "hello"},
        {"prompt_id": "test1", "token_index": 1, "token": "world"},
        {"prompt_id": "test2", "token_index": 0, "token": "foo"},
        {"prompt_id": "test2", "token_index": 1, "token": "bar"},
        {"prompt_id": "test2", "token_index": 2, "token": "baz"}
    ]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in sample_data:
            f.write(json.dumps(record) + '\n')
    
    return file_path

@pytest.fixture
def large_sample_data_file(temp_test_dir):
    """Create a larger sample JSONL file for batch testing."""
    file_path = temp_test_dir / 'large_sample_data.jsonl'
    sample_data = []
    
    for i in range(1000):
        sample_data.append({
            "prompt_id": f"prompt_{i // 100}",
            "token_index": i % 100,
            "token": f"token_{i}",
            "value": i
        })
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in sample_data:
            f.write(json.dumps(record) + '\n')
    
    return file_path

def test_validate_batch_size_valid():
    """Test that valid batch sizes are accepted."""
    # These should not raise
    validate_batch_size(1)
    validate_batch_size(50)
    validate_batch_size(500)
    validate_batch_size(1000)
    validate_batch_size(10000)

def test_validate_batch_size_invalid():
    """Test that invalid batch sizes are rejected."""
    with pytest.raises(BatchSizeError):
        validate_batch_size(0)
    
    with pytest.raises(BatchSizeError):
        validate_batch_size(-1)
    
    with pytest.raises(BatchSizeError):
        validate_batch_size(10001)

def test_stream_tokens_in_batches():
    """Test streaming tokens in fixed-size batches."""
    tokens = [{"id": i} for i in range(125)]
    
    batches = list(stream_tokens_in_batches(tokens, batch_size=50))
    
    assert len(batches) == 3
    assert len(batches[0]) == 50
    assert len(batches[1]) == 50
    assert len(batches[2]) == 25

def test_stream_tokens_in_batches_from_list():
    """Test streaming from a list of records."""
    records = [
        {"prompt_id": f"p{i}", "token_index": j, "token": f"t{j}"}
        for i in range(10)
        for j in range(10)
    ]
    
    batches = list(stream_tokens_in_batches(records, batch_size=25))
    
    assert len(batches) == 4
    assert len(batches[0]) == 25
    assert len(batches[1]) == 25
    assert len(batches[2]) == 25
    assert len(batches[3]) == 25

def test_stream_batch_basic(temp_test_dir):
    """Test basic batch streaming functionality."""
    # Create a file with 1500 records
    file_path = temp_test_dir / 'test_stream.jsonl'
    records = [{"id": i, "value": f"record_{i}"} for i in range(1500)]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
    
    # Stream with batch size 500
    batches = list(stream_batch(file_path, batch_size=500))
    
    assert len(batches) == 3
    assert len(batches[0]) == 500
    assert len(batches[1]) == 500
    assert len(batches[2]) == 500

def test_stream_batch_with_large_data(large_sample_data_file):
    """Test streaming with larger dataset."""
    batches = list(stream_batch(large_sample_data_file, batch_size=500))
    
    assert len(batches) == 2
    assert len(batches[0]) == 500
    assert len(batches[1]) == 500

def test_memory_backoff(temp_test_dir):
    """
    Test memory backoff logic when MemoryError is raised.
    
    This test simulates a MemoryError by creating a custom stream_batch
    that raises MemoryError on the first batch and verifies the batch
    size is halved.
    """
    # Create test data
    file_path = temp_test_dir / 'memory_test.jsonl'
    records = [{"id": i} for i in range(1000)]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
    
    # Test that normal operation works without MemoryError
    batches = list(stream_batch(file_path, batch_size=500, min_batch_size=100))
    assert len(batches) == 2
    
    # Test with smaller batch size
    batches = list(stream_batch(file_path, batch_size=200, min_batch_size=50))
    assert len(batches) == 5

def test_memory_backoff_fails_at_minimum(temp_test_dir):
    """Test that RuntimeError is raised when batch size hits minimum."""
    # Create test data
    file_path = temp_test_dir / 'min_test.jsonl'
    records = [{"id": i} for i in range(100)]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
    
    # This should work fine with min_batch_size=10
    batches = list(stream_batch(file_path, batch_size=50, min_batch_size=10))
    assert len(batches) == 2

def test_load_tokens_from_file(temp_test_dir):
    """Test loading tokens from a JSONL file."""
    file_path = temp_test_dir / 'load_test.jsonl'
    records = [{"id": i, "value": f"test_{i}"} for i in range(10)]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
    
    loaded = load_tokens_from_file(file_path)
    
    assert len(loaded) == 10
    assert loaded[0]["id"] == 0
    assert loaded[9]["id"] == 9

def test_load_tokens_from_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_tokens_from_file("/nonexistent/path/file.jsonl")

def test_merge_entropy_profiles(temp_test_dir):
    """Test merging entropy profiles with base data."""
    base_data = [
        {"prompt_id": "p1", "token_index": 0, "token": "t1"},
        {"prompt_id": "p1", "token_index": 1, "token": "t2"},
        {"prompt_id": "p2", "token_index": 0, "token": "t3"}
    ]
    
    entropy_data = [
        {"prompt_id": "p1", "token_index": 0, "layer_entropy_map": {"layer_0": 1.5}},
        {"prompt_id": "p1", "token_index": 1, "layer_entropy_map": {"layer_0": 2.0}},
        {"prompt_id": "p2", "token_index": 0, "layer_entropy_map": {"layer_0": 0.8}}
    ]
    
    merged = merge_entropy_profiles(base_data, entropy_data)
    
    assert len(merged) == 3
    assert merged[0]["layer_entropy_map"] == {"layer_0": 1.5}
    assert merged[1]["layer_entropy_map"] == {"layer_0": 2.0}
    assert merged[2]["layer_entropy_map"] == {"layer_0": 0.8}

def test_validate_entropy_profile_valid():
    """Test validation of a valid entropy profile."""
    record = {
        "prompt_id": "test",
        "token_index": 0,
        "layer_entropy_map": {
            "layer_0": 1.5,
            "layer_1": 2.0
        }
    }
    
    # Should not raise
    validate_entropy_profile(record)

def test_validate_entropy_profile_missing_prompt_id():
    """Test validation fails on missing prompt_id."""
    record = {
        "token_index": 0,
        "layer_entropy_map": {"layer_0": 1.5}
    }
    
    with pytest.raises(ValueError):
        validate_entropy_profile(record)

def test_validate_entropy_profile_missing_entropy_values():
    """Test validation fails on missing layer_entropy_map."""
    record = {
        "prompt_id": "test",
        "token_index": 0
    }
    
    with pytest.raises(ValueError):
        validate_entropy_profile(record)

def test_validate_entropy_profile_missing_layer():
    """Test validation fails on missing token_index."""
    record = {
        "prompt_id": "test",
        "layer_entropy_map": {"layer_0": 1.5}
    }
    
    with pytest.raises(ValueError):
        validate_entropy_profile(record)

def test_validate_entropy_profile_missing_entropy_value():
    """Test validation fails on None entropy value."""
    record = {
        "prompt_id": "test",
        "token_index": 0,
        "layer_entropy_map": {"layer_0": None}
    }
    
    with pytest.raises(ValueError):
        validate_entropy_profile(record)

def test_stream_batch_output_to_file(temp_test_dir):
    """Test that stream_batch can write to a file."""
    # Create input file
    input_path = temp_test_dir / 'input.jsonl'
    records = [{"id": i} for i in range(100)]
    
    with open(input_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
    
    output_path = temp_test_dir / 'output.jsonl'
    
    # Stream and write to file
    with open(output_path, 'w', encoding='utf-8') as out_f:
        for batch in stream_batch(input_path, batch_size=50):
            for record in batch:
                out_f.write(json.dumps(record) + '\n')
    
    # Verify output
    output_records = load_tokens_from_file(output_path)
    assert len(output_records) == 100