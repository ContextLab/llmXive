"""
Integration tests for preprocessing module.

Tests memory backoff, batching, and merging logic.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pytest
from unittest.mock import patch, MagicMock
import psutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.preprocessing import (
    stream_batch,
    stream_tokens_in_batches,
    validate_batch_size,
    BatchSizeError,
    check_memory_backoff_condition,
    get_current_ram_gb,
    load_tokens_from_file,
    merge_entropy_profiles,
    validate_entropy_profile
)
from src.utils.validators import EntropyProfile

@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_data_file(temp_test_dir):
    """Create a sample JSONL file with test data."""
    file_path = temp_test_dir / "sample.jsonl"
    data = [
        {"sequence_id": "seq_001", "tokens": [1, 2, 3, 4, 5], "prompt": "test1"},
        {"sequence_id": "seq_002", "tokens": [10, 20, 30, 40, 50], "prompt": "test2"},
        {"sequence_id": "seq_003", "tokens": [100, 200, 300], "prompt": "test3"}
    ]
    with open(file_path, "w") as f:
        for record in data:
            f.write(json.dumps(record) + "\n")
    return file_path

@pytest.fixture
def large_sample_data_file(temp_test_dir):
    """Create a larger sample file to test batching."""
    file_path = temp_test_dir / "large_sample.jsonl"
    data = []
    for i in range(100):
        tokens = list(range(i * 10, (i + 1) * 10))
        data.append({
            "sequence_id": f"seq_{i:03d}",
            "tokens": tokens,
            "prompt": f"prompt_{i}"
        })
    with open(file_path, "w") as f:
        for record in data:
            f.write(json.dumps(record) + "\n")
    return file_path

def test_validate_batch_size_valid():
    """Test that valid batch size (50) passes validation."""
    assert validate_batch_size(50) is True

def test_validate_batch_size_invalid():
    """Test that invalid batch sizes raise BatchSizeError."""
    with pytest.raises(BatchSizeError):
        validate_batch_size(100)
    with pytest.raises(BatchSizeError):
        validate_batch_size(10)

def test_stream_tokens_in_batches():
    """Test token streaming in batches."""
    tokens = list(range(120))
    batches = list(stream_tokens_in_batches(tokens, 50))
    
    assert len(batches) == 3
    assert len(batches[0]) == 50
    assert len(batches[1]) == 50
    assert len(batches[2]) == 20
    
    assert batches[0] == list(range(50))
    assert batches[1] == list(range(50, 100))
    assert batches[2] == list(range(100, 120))

def test_stream_tokens_in_batches_from_list(sample_data_file):
    """Test streaming from a list of records."""
    with open(sample_data_file, "r") as f:
        data = [json.loads(line) for line in f]
    
    # Flatten all tokens
    all_tokens = []
    for record in data:
        all_tokens.extend(record["tokens"])
    
    batches = list(stream_tokens_in_batches(all_tokens, 5))
    assert len(batches) == 3  # 13 tokens / 5 = 3 batches

def test_stream_batch_basic(temp_test_dir):
    """Test basic stream_batch functionality."""
    output_path = temp_test_dir / "output.jsonl"
    
    # Create test data
    test_data = [
        {"sequence_id": "test_1", "tokens": list(range(50))},
        {"sequence_id": "test_2", "tokens": list(range(50, 100))}
    ]
    
    results = list(stream_batch(iter(test_data), output_path, batch_size=50))
    
    assert len(results) == 2
    assert results[0]["sequence_id"] == "test_1"
    assert results[1]["sequence_id"] == "test_2"
    
    # Verify file was written
    assert output_path.exists()
    with open(output_path, "r") as f:
        lines = f.readlines()
    assert len(lines) == 2

def test_stream_batch_with_large_data(large_sample_data_file, temp_test_dir):
    """Test stream_batch with large dataset."""
    output_path = temp_test_dir / "large_output.jsonl"
    
    # Load data
    with open(large_sample_data_file, "r") as f:
        data = [json.loads(line) for line in f]
    
    results = list(stream_batch(iter(data), output_path, batch_size=50))
    
    # Should process all 100 records
    assert len(results) == 100

def test_memory_backoff(temp_test_dir):
    """
    Test memory backoff logic.
    
    Verifies that stream_batch handles memory pressure correctly
    by flushing buffers when RAM exceeds threshold.
    """
    output_path = temp_test_dir / "backoff_test.jsonl"
    
    # Mock psutil to simulate high memory usage
    with patch('src.data.preprocessing.psutil.Process') as mock_process:
        mock_instance = MagicMock()
        mock_instance.memory_info.return_value.rss = (6.5 * 1024 ** 3)  # 6.5 GB
        mock_process.return_value = mock_instance
        
        # Create data that will trigger backoff
        test_data = [
            {"sequence_id": f"seq_{i}", "tokens": list(range(100))}
            for i in range(10)
        ]
        
        # Should not raise, but should trigger backoff logic
        results = list(stream_batch(iter(test_data), output_path, batch_size=50))
        
        # Verify results were still produced
        assert len(results) > 0

def test_memory_backoff_fails_at_minimum(temp_test_dir):
    """Test that memory error is raised if backoff cannot recover."""
    output_path = temp_test_dir / "fail_test.jsonl"
    
    # Mock psutil to always show high memory
    with patch('src.data.preprocessing.psutil.Process') as mock_process:
        mock_instance = MagicMock()
        mock_instance.memory_info.return_value.rss = (10.0 * 1024 ** 3)  # 10 GB
        mock_process.return_value = mock_instance
        
        test_data = [{"sequence_id": "seq_1", "tokens": list(range(100))}]
        
        # Should raise MemoryError
        with pytest.raises(MemoryError):
            list(stream_batch(iter(test_data), output_path, batch_size=50))

def test_load_tokens_from_file(sample_data_file):
    """Test loading tokens from file."""
    records = load_tokens_from_file(sample_data_file)
    
    assert len(records) == 3
    assert records[0]["sequence_id"] == "seq_001"
    assert len(records[0]["tokens"]) == 5

def test_load_tokens_from_file_not_found():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_tokens_from_file("/nonexistent/path/file.jsonl")

def test_merge_entropy_profiles(temp_test_dir):
    """Test merging entropy profiles with labeled data."""
    entropy_data = [
        {"sequence_id": "seq_1", "token_index": 0, "entropy": 0.5},
        {"sequence_id": "seq_1", "token_index": 1, "entropy": 0.8}
    ]
    
    labeled_data = [
        {"sequence_id": "seq_1", "token_index": 0, "validity": True},
        {"sequence_id": "seq_1", "token_index": 1, "validity": False}
    ]
    
    merged = merge_entropy_profiles(entropy_data, labeled_data)
    
    assert len(merged) == 2
    assert merged[0]["entropy"] == 0.5
    assert merged[0]["validity"] is True
    assert merged[1]["entropy"] == 0.8
    assert merged[1]["validity"] is False

def test_validate_entropy_profile_valid():
    """Test validation of a valid entropy profile."""
    valid_profile = {
        "sequence_id": "test_1",
        "layer_entropies": [0.1, 0.2, 0.3],
        "avg_entropy": 0.2,
        "max_entropy": 0.3
    }
    assert validate_entropy_profile(valid_profile) is True

def test_validate_entropy_profile_missing_prompt_id():
    """Test validation fails with missing sequence_id."""
    invalid_profile = {
        "layer_entropies": [0.1, 0.2],
        "avg_entropy": 0.15
    }
    with pytest.raises(ValueError):
        validate_entropy_profile(invalid_profile)

def test_validate_entropy_profile_missing_entropy_values():
    """Test validation fails with missing entropy values."""
    invalid_profile = {
        "sequence_id": "test_1",
        "layer_entropies": [],
        "avg_entropy": None
    }
    with pytest.raises(ValueError):
        validate_entropy_profile(invalid_profile)

def test_validate_entropy_profile_missing_layer():
    """Test validation fails with missing layer data."""
    invalid_profile = {
        "sequence_id": "test_1",
        "avg_entropy": 0.5
    }
    with pytest.raises(ValueError):
        validate_entropy_profile(invalid_profile)

def test_validate_entropy_profile_missing_entropy_value():
    """Test validation fails with None entropy value in layer."""
    invalid_profile = {
        "sequence_id": "test_1",
        "layer_entropies": [0.1, None, 0.3],
        "avg_entropy": 0.2
    }
    with pytest.raises(ValueError):
        validate_entropy_profile(invalid_profile)

def test_stream_batch_output_to_file(temp_test_dir):
    """Test that stream_batch writes output to file correctly."""
    output_path = temp_test_dir / "stream_output.jsonl"
    
    test_data = [
        {"sequence_id": "seq_1", "tokens": list(range(50))},
        {"sequence_id": "seq_2", "tokens": list(range(50, 100))}
    ]
    
    list(stream_batch(iter(test_data), output_path, batch_size=50))
    
    assert output_path.exists()
    with open(output_path, "r") as f:
        lines = f.readlines()
    
    assert len(lines) == 2
    
    # Verify JSON validity
    for line in lines:
        record = json.loads(line)
        assert "sequence_id" in record
        assert "tokens" in record

if __name__ == "__main__":
    pytest.main([__file__, "-v"])