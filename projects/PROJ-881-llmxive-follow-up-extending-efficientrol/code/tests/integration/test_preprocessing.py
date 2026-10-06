"""
Integration tests for preprocessing module.

These tests verify the 50-token batching logic and streaming functionality
of the preprocessing module.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.preprocessing import (
    stream_batch,
    token_batch_stream,
    load_tokens_from_file,
    stream_tokens_in_batches,
    validate_batch_size,
    BatchSizeError,
    merge_entropy_profiles,
    validate_entropy_profile
)

@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_data_file(temp_test_dir):
    """Create a sample JSONL file with test data."""
    file_path = temp_test_dir / "sample_data.jsonl"
    data = [{'id': i, 'value': f'test_{i}'} for i in range(100)]
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    return file_path

@pytest.fixture
def large_sample_data_file(temp_test_dir):
    """Create a large sample JSONL file with test data."""
    file_path = temp_test_dir / "large_sample_data.jsonl"
    data = [{'id': i, 'value': f'large_test_{i}'} for i in range(1000)]
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    return file_path

@pytest.fixture
def sample_token_file(temp_test_dir):
    """Create a sample token JSONL file."""
    file_path = temp_test_dir / "tokens.jsonl"
    data = [
        {'token_id': i, 'token': f'token_{i}', 'prompt_id': f'prompt_{i // 50}'}
        for i in range(150)
    ]
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    return file_path

def test_validate_batch_size_valid():
    """Test that valid batch sizes pass validation."""
    validate_batch_size(1)
    validate_batch_size(50)
    validate_batch_size(100)
    validate_batch_size(1000)

def test_validate_batch_size_invalid():
    """Test that invalid batch sizes raise BatchSizeError."""
    with pytest.raises(BatchSizeError):
        validate_batch_size(0)

    with pytest.raises(BatchSizeError):
        validate_batch_size(-1)

    with pytest.raises(BatchSizeError):
        validate_batch_size(20000)

def test_stream_batch_basic():
    """Test basic stream_batch functionality with fixed batch size."""
    def example_iterator():
        for i in range(100):
            yield {'id': i}

    batches = list(stream_batch(example_iterator(), batch_size=50))

    assert len(batches) == 2
    assert len(batches[0]) == 50
    assert len(batches[1]) == 50
    assert batches[0][0]['id'] == 0
    assert batches[0][49]['id'] == 49
    assert batches[1][0]['id'] == 50
    assert batches[1][49]['id'] == 99

def test_stream_batch_with_large_data():
    """Test stream_batch with large dataset."""
    def example_iterator():
        for i in range(1000):
            yield {'id': i}

    batches = list(stream_batch(example_iterator(), batch_size=50))

    assert len(batches) == 20
    for i, batch in enumerate(batches):
        assert len(batch) == 50
        assert batch[0]['id'] == i * 50
        assert batch[-1]['id'] == (i + 1) * 50 - 1

def test_stream_batch_partial_batch():
    """Test stream_batch with data that doesn't divide evenly."""
    def example_iterator():
        for i in range(115):
            yield {'id': i}

    batches = list(stream_batch(example_iterator(), batch_size=50))

    assert len(batches) == 3
    assert len(batches[0]) == 50
    assert len(batches[1]) == 50
    assert len(batches[2]) == 15

def test_stream_batch_empty_input():
    """Test stream_batch with empty input."""
    def empty_iterator():
        return
        yield  # Never reached

    batches = list(stream_batch(empty_iterator(), batch_size=50))
    assert len(batches) == 0

def test_stream_batch_single_item():
    """Test stream_batch with a single item."""
    def single_iterator():
        yield {'id': 1}

    batches = list(stream_batch(single_iterator(), batch_size=50))
    assert len(batches) == 1
    assert len(batches[0]) == 1
    assert batches[0][0]['id'] == 1

def test_token_batch_stream_basic():
    """Test basic token_batch_stream functionality."""
    def example_token_iterator():
        for i in range(150):
            yield {'token_id': i, 'token': f'token_{i}'}

    batches = list(token_batch_stream(example_token_iterator(), batch_size=50))

    assert len(batches) == 3
    assert len(batches[0]) == 50
    assert len(batches[1]) == 50
    assert len(batches[2]) == 50

def test_token_batch_stream_partial_batch():
    """Test token_batch_stream with partial final batch."""
    def example_token_iterator():
        for i in range(137):
            yield {'token_id': i, 'token': f'token_{i}'}

    batches = list(token_batch_stream(example_token_iterator(), batch_size=50))

    assert len(batches) == 3
    assert len(batches[0]) == 50
    assert len(batches[1]) == 50
    assert len(batches[2]) == 37

def test_token_batch_stream_empty_input():
    """Test token_batch_stream with empty input."""
    def empty_iterator():
        return
        yield

    batches = list(token_batch_stream(empty_iterator(), batch_size=50))
    assert len(batches) == 0

def test_token_batch_stream_single_item():
    """Test token_batch_stream with a single item."""
    def single_iterator():
        yield {'token_id': 1, 'token': 'token_1'}

    batches = list(token_batch_stream(single_iterator(), batch_size=50))
    assert len(batches) == 1
    assert len(batches[0]) == 1

def test_load_tokens_from_file(temp_test_dir, sample_token_file):
    """Test loading tokens from a JSONL file."""
    tokens = list(load_tokens_from_file(sample_token_file))

    assert len(tokens) == 150
    assert tokens[0]['token_id'] == 0
    assert tokens[149]['token_id'] == 149

def test_load_tokens_from_file_not_found(temp_test_dir):
    """Test that load_tokens_from_file raises FileNotFoundError for missing file."""
    non_existent = temp_test_dir / "non_existent.jsonl"
    with pytest.raises(FileNotFoundError):
        list(load_tokens_from_file(non_existent))

def test_stream_tokens_in_batches(temp_test_dir, sample_token_file):
    """Test streaming tokens from file in batches."""
    batches = list(stream_tokens_in_batches(sample_token_file, batch_size=50))

    assert len(batches) == 3
    assert len(batches[0]) == 50
    assert len(batches[1]) == 50
    assert len(batches[2]) == 50

def test_merge_entropy_profiles_success():
    """Test successful merge of generation and entropy data."""
    generation_data = [
        {'prompt_id': 'p1', 'token_index': 0, 'text': 'hello'},
        {'prompt_id': 'p1', 'token_index': 1, 'text': 'world'},
        {'prompt_id': 'p2', 'token_index': 0, 'text': 'foo'}
    ]

    entropy_data = [
        {'prompt_id': 'p1', 'token_index': 0, 'layer_entropy_map': {'0': 0.5}},
        {'prompt_id': 'p1', 'token_index': 1, 'layer_entropy_map': {'0': 0.3}},
        {'prompt_id': 'p2', 'token_index': 0, 'layer_entropy_map': {'0': 0.7}}
    ]

    merged = merge_entropy_profiles(generation_data, entropy_data)

    assert len(merged) == 3
    assert merged[0]['text'] == 'hello'
    assert merged[0]['layer_entropy_map'] == {'0': 0.5}
    assert merged[2]['text'] == 'foo'
    assert merged[2]['layer_entropy_map'] == {'0': 0.7}

def test_merge_missing_sequence_id():
    """Test merge when some entropy data is missing."""
    generation_data = [
        {'prompt_id': 'p1', 'token_index': 0, 'text': 'hello'},
        {'prompt_id': 'p1', 'token_index': 1, 'text': 'world'}
    ]

    entropy_data = [
        {'prompt_id': 'p1', 'token_index': 0, 'layer_entropy_map': {'0': 0.5}}
    ]

    merged = merge_entropy_profiles(generation_data, entropy_data)

    assert len(merged) == 2
    assert 'layer_entropy_map' in merged[0]
    assert 'layer_entropy_map' not in merged[1] or merged[1].get('layer_entropy_map') is None

def test_validate_entropy_profile_valid():
    """Test validation of a valid entropy profile."""
    record = {
        'prompt_id': 'p1',
        'token_index': 0,
        'sequence_length': 10,
        'layer_entropy_map': {
            '0': 0.5,
            '1': 0.3,
            '2': 0.7
        }
    }

    assert validate_entropy_profile(record) is True

def test_validate_entropy_profile_missing_values():
    """Test validation fails for missing required values."""
    record = {
        'prompt_id': 'p1',
        'token_index': 0,
        'sequence_length': None,
        'layer_entropy_map': {'0': 0.5}
    }

    with pytest.raises(ValueError):
        validate_entropy_profile(record)

def test_validate_entropy_profile_missing_layer():
    """Test validation fails for missing layer entropy."""
    record = {
        'prompt_id': 'p1',
        'token_index': 0,
        'sequence_length': 10,
        'layer_entropy_map': {'0': None}
    }

    with pytest.raises(ValueError):
        validate_entropy_profile(record)

def test_validate_entropy_profile_missing_field():
    """Test validation fails for missing required field."""
    record = {
        'prompt_id': 'p1',
        'token_index': 0,
        'layer_entropy_map': {'0': 0.5}
    }

    with pytest.raises(ValueError):
        validate_entropy_profile(record)

def test_50_token_batching(temp_test_dir, sample_token_file):
    """
    Verify the 50-token batching logic.

    This test ensures that the stream_batch and token_batch_stream functions
    correctly yield batches of exactly 50 tokens (except for the final batch
    which may be smaller).
    """
    batches = list(stream_tokens_in_batches(sample_token_file, batch_size=50))

    # Verify batch count: 150 tokens / 50 = 3 batches
    assert len(batches) == 3

    # Verify each batch size
    for i in range(2):  # First two batches should be exactly 50
        assert len(batches[i]) == 50

    # Verify final batch size (remainder)
    assert len(batches[2]) == 50  # 150 is divisible by 50

    # Verify token IDs are sequential within batches
    for batch_idx, batch in enumerate(batches):
        start_id = batch_idx * 50
        for i, token_data in enumerate(batch):
            assert token_data['token_id'] == start_id + i

def test_memory_backoff():
    """Test memory backoff condition checking."""
    from src.data.preprocessing import check_memory_backoff_condition, get_memory_percent

    # This test just verifies the function runs without error
    # The actual threshold check depends on system state
    current_percent = get_memory_percent()
    is_over_threshold = check_memory_backoff_condition(threshold_percent=99.0)

    # If memory is not at 99%, it should be False
    if current_percent < 99.0:
        assert is_over_threshold is False

def test_memory_backoff_fails_at_minimum():
    """Test that memory backoff condition works at minimum threshold."""
    from src.data.preprocessing import check_memory_backoff_condition

    # Test with very low threshold - should almost always be True
    # unless system is completely idle
    result = check_memory_backoff_condition(threshold_percent=0.0)
    assert result is True  # Memory usage is always > 0%

def test_adaptive_batch_size_reduction():
    """Test that batch size validation works for various sizes."""
    # Valid sizes
    validate_batch_size(1)
    validate_batch_size(10)
    validate_batch_size(50)
    validate_batch_size(100)

    # Invalid sizes
    with pytest.raises(BatchSizeError):
        validate_batch_size(0)

    with pytest.raises(BatchSizeError):
        validate_batch_size(-10)

def test_generator_input_stream_batch():
    """Test stream_batch with generator input."""
    def gen():
        for i in range(75):
            yield {'value': i}

    batches = list(stream_batch(gen(), batch_size=25))

    assert len(batches) == 3
    assert len(batches[0]) == 25
    assert len(batches[1]) == 25
    assert len(batches[2]) == 25

def test_empty_input_stream_batch():
    """Test stream_batch with empty generator."""
    def empty_gen():
        return
        yield

    batches = list(stream_batch(empty_gen(), batch_size=50))
    assert len(batches) == 0

def test_invalid_input_type_stream_batch():
    """Test stream_batch with invalid input type."""
    with pytest.raises(TypeError):
        list(stream_batch("not an iterator", batch_size=50))

    with pytest.raises(TypeError):
        list(stream_batch([1, 2, 3], batch_size=50))  # List is iterable but not iterator

def test_multiple_sequences_token_batch_stream():
    """Test token_batch_stream with multiple sequences."""
    def multi_seq_iterator():
        for seq_id in range(3):
            for token_id in range(20):
                yield {
                    'sequence_id': seq_id,
                    'token_id': token_id,
                    'token': f'seq{seq_id}_tok{token_id}'
                }

    batches = list(token_batch_stream(multi_seq_iterator(), batch_size=50))

    # 3 sequences * 20 tokens = 60 tokens total
    # 60 / 50 = 1 full batch + 1 partial batch
    assert len(batches) == 2
    assert len(batches[0]) == 50
    assert len(batches[1]) == 10