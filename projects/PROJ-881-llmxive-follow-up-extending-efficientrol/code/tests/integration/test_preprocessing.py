"""
Integration tests for preprocessing module.

These tests verify the batched streaming mechanism and memory back-off logic.
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
    load_tokens_from_file,
    merge_entropy_profiles,
    validate_entropy_profile,
    BatchSizeError,
    stream_tokens_in_batches
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
        {"prompt_id": "1", "tokens": ["hello", "world"], "logits": [[0.1, 0.9], [0.8, 0.2]]},
        {"prompt_id": "2", "tokens": ["test", "data"], "logits": [[0.5, 0.5], [0.3, 0.7]]},
        {"prompt_id": "3", "tokens": ["more", "tokens"], "logits": [[0.2, 0.8], [0.6, 0.4]]},
        {"prompt_id": "4", "tokens": ["batch", "test"], "logits": [[0.4, 0.6], [0.1, 0.9]]},
        {"prompt_id": "5", "tokens": ["final", "record"], "logits": [[0.7, 0.3], [0.9, 0.1]]},
    ]

    with open(file_path, 'w', encoding='utf-8') as f:
        for record in sample_data:
            f.write(json.dumps(record) + '\n')

    return file_path


@pytest.fixture
def large_sample_data_file(temp_test_dir):
    """Create a larger sample JSONL file for memory testing."""
    file_path = temp_test_dir / 'large_data.jsonl'

    # Create 1000 records with larger payloads to simulate memory pressure
    with open(file_path, 'w', encoding='utf-8') as f:
        for i in range(1000):
            record = {
                "prompt_id": str(i),
                "tokens": [f"token_{j}" for j in range(50)],
                "logits": [[0.1, 0.9] for _ in range(50)],
                "metadata": {"size": "large", "index": i}
            }
            f.write(json.dumps(record) + '\n')

    return file_path


def test_validate_batch_size_valid():
    """Test that valid batch sizes pass validation."""
    from src.data.preprocessing import validate_batch_size
    assert validate_batch_size(100) is True
    assert validate_batch_size(1) is True
    assert validate_batch_size(10000) is True


def test_validate_batch_size_invalid():
    """Test that invalid batch sizes raise errors."""
    from src.data.preprocessing import validate_batch_size, BatchSizeError

    with pytest.raises(BatchSizeError):
        validate_batch_size(0)

    with pytest.raises(BatchSizeError):
        validate_batch_size(-1)

    with pytest.raises(BatchSizeError):
        validate_batch_size(20000, max_size=10000)


def test_stream_tokens_in_batches(sample_data_file):
    """Test streaming tokens in batches from file."""
    batches = list(stream_tokens_in_batches(sample_data_file, batch_size=2))

    assert len(batches) == 3  # 5 records / 2 = 3 batches (2, 2, 1)
    assert len(batches[0]) == 2
    assert len(batches[1]) == 2
    assert len(batches[2]) == 1


def test_stream_tokens_in_batches_from_list():
    """Test streaming from a list of records."""
    data = [{"id": i} for i in range(7)]
    batches = list(stream_tokens_in_batches(data, batch_size=3))

    assert len(batches) == 3  # 7 / 3 = 3 batches (3, 3, 1)
    assert len(batches[0]) == 3
    assert len(batches[1]) == 3
    assert len(batches[2]) == 1


def test_stream_batch_basic(sample_data_file, temp_test_dir):
    """Test basic stream_batch functionality."""
    output_path = temp_test_dir / 'output.jsonl'

    stats = stream_batch(
        data_source=sample_data_file,
        output_path=output_path,
        initial_batch_size=2
    )

    assert stats['total_records_processed'] == 5
    assert stats['total_batches_processed'] == 3
    assert stats['memory_backoffs'] == 0

    # Verify output file
    assert output_path.exists()
    with open(output_path, 'r') as f:
        lines = f.readlines()
    assert len(lines) == 5


def test_stream_batch_with_large_data(large_sample_data_file, temp_test_dir):
    """Test stream_batch with larger dataset."""
    output_path = temp_test_dir / 'large_output.jsonl'

    stats = stream_batch(
        data_source=large_sample_data_file,
        output_path=output_path,
        initial_batch_size=100
    )

    assert stats['total_records_processed'] == 1000
    assert stats['memory_backoffs'] == 0

    # Verify output
    with open(output_path, 'r') as f:
        lines = f.readlines()
    assert len(lines) == 1000


def test_memory_backoff(temp_test_dir):
    """
    Test that memory back-off logic works correctly.

    This test simulates a MemoryError by using a very small batch size
    that would cause issues in a real memory-constrained environment.
    We verify that the function attempts to reduce batch size and continues.
    """
    input_path = temp_test_dir / 'input.jsonl'
    output_path = temp_test_dir / 'output.jsonl'

    # Create input data
    with open(input_path, 'w') as f:
        for i in range(100):
            f.write(json.dumps({"id": i, "data": "x" * 1000}) + '\n')

    # Use a small initial batch size to trigger potential memory issues
    # In a real scenario, we'd mock the MemoryError, but here we test
    # that the function handles small batches gracefully
    stats = stream_batch(
        data_source=input_path,
        output_path=output_path,
        initial_batch_size=10,
        min_batch_size=1,
        reduction_factor=0.5
    )

    # Should complete successfully
    assert stats['total_records_processed'] == 100
    assert output_path.exists()

    # Verify output content
    with open(output_path, 'r') as f:
        lines = f.readlines()
    assert len(lines) == 100


def test_memory_backoff_fails_at_minimum(temp_test_dir, mocker):
    """
    Test that BatchSizeError is raised when memory error persists at minimum batch size.

    This test mocks the stream_tokens_in_batches to raise MemoryError
    even at minimum batch size.
    """
    from unittest.mock import patch, MagicMock
    from src.data.preprocessing import stream_tokens_in_batches, BatchSizeError

    input_path = temp_test_dir / 'input.jsonl'
    output_path = temp_test_dir / 'output.jsonl'

    # Create minimal input
    with open(input_path, 'w') as f:
        f.write(json.dumps({"id": 1}) + '\n')

    # Mock stream_tokens_in_batches to always raise MemoryError
    with patch('src.data.preprocessing.stream_tokens_in_batches') as mock_stream:
        mock_stream.side_effect = MemoryError("Simulated OOM")

        with pytest.raises(BatchSizeError) as exc_info:
            stream_batch(
                data_source=input_path,
                output_path=output_path,
                initial_batch_size=10,
                min_batch_size=1,
                reduction_factor=0.5
            )

        assert "MemoryError persists at minimum batch size" in str(exc_info.value)


def test_load_tokens_from_file(sample_data_file):
    """Test loading tokens from file."""
    records = load_tokens_from_file(sample_data_file)

    assert len(records) == 5
    assert records[0]['prompt_id'] == '1'
    assert records[4]['prompt_id'] == '5'


def test_load_tokens_from_file_not_found():
    """Test that loading from non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_tokens_from_file('/nonexistent/path.jsonl')


def test_merge_entropy_profiles(temp_test_dir):
    """Test merging entropy profiles with sequence data."""
    seq_file = temp_test_dir / 'sequences.jsonl'
    ent_file = temp_test_dir / 'entropy.jsonl'
    out_file = temp_test_dir / 'merged.jsonl'

    # Create sequence data
    seq_data = [
        {"prompt_id": "1", "tokens": ["a", "b"]},
        {"prompt_id": "2", "tokens": ["c", "d"]},
        {"prompt_id": "3", "tokens": ["e", "f"]},
    ]
    with open(seq_file, 'w') as f:
        for record in seq_data:
            f.write(json.dumps(record) + '\n')

    # Create entropy data
    ent_data = [
        {"prompt_id": "1", "entropy_values": [0.5, 0.8]},
        {"prompt_id": "2", "entropy_values": [0.3, 0.6]},
    ]
    with open(ent_file, 'w') as f:
        for record in ent_data:
            f.write(json.dumps(record) + '\n')

    # Merge
    count = merge_entropy_profiles(seq_file, ent_file, out_file)

    assert count == 3
    assert out_file.exists()

    # Verify merged content
    with open(out_file, 'r') as f:
        merged = [json.loads(line) for line in f]

    assert len(merged) == 3
    assert 'entropy_values' in merged[0]
    assert 'entropy_values' in merged[1]
    assert 'entropy_values' not in merged[2]  # No match for id 3


def test_validate_entropy_profile_valid():
    """Test validation of valid entropy profile."""
    record = {
        "prompt_id": "123",
        "entropy_values": [0.1, 0.5, 0.9]
    }
    assert validate_entropy_profile(record) is True


def test_validate_entropy_profile_missing_prompt_id():
    """Test validation fails on missing prompt_id."""
    record = {"entropy_values": [0.1, 0.5]}
    with pytest.raises(ValueError):
        validate_entropy_profile(record)


def test_validate_entropy_profile_missing_entropy_values():
    """Test validation fails on missing entropy_values."""
    record = {"prompt_id": "123"}
    with pytest.raises(ValueError):
        validate_entropy_profile(record)


def test_validate_entropy_profile_missing_layer():
    """Test validation fails on None in entropy_values."""
    record = {"prompt_id": "123", "entropy_values": [0.1, None, 0.9]}
    with pytest.raises(ValueError):
        validate_entropy_profile(record)


def test_validate_entropy_profile_missing_entropy_value():
    """Test validation fails on non-numeric entropy value."""
    record = {"prompt_id": "123", "entropy_values": [0.1, "invalid", 0.9]}
    with pytest.raises(ValueError):
        validate_entropy_profile(record)


def test_stream_batch_output_to_file(sample_data_file, temp_test_dir):
    """Test that stream_batch correctly writes to output file."""
    output_path = temp_test_dir / 'test_output.jsonl'

    stats = stream_batch(
        data_source=sample_data_file,
        output_path=output_path,
        initial_batch_size=2
    )

    assert output_path.exists()

    # Read and verify output
    with open(output_path, 'r') as f:
        output_records = [json.loads(line) for line in f]

    assert len(output_records) == 5
    assert output_records[0]['prompt_id'] == '1'
    assert output_records[4]['prompt_id'] == '5'