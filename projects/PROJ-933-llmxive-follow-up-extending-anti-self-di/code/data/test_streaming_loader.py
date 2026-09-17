"""
Unit tests for streaming dataset loading and chunked processing utilities.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from data.streaming_loader import (
    stream_dataset,
    stream_dataset_multiple,
    process_in_chunks,
    accumulate_statistics,
    compute_dataset_checksum,
    filter_stream,
    sample_stream,
    write_chunked_output,
    merge_chunked_outputs
)


class TestStreamingLoader:
    """Test cases for streaming loader functions."""

    def test_stream_dataset_raises_on_failure(self):
        """Test that stream_dataset raises an error if loading fails."""
        with patch("data.streaming_loader.load_dataset") as mock_load:
            mock_load.side_effect = Exception("Network error")
            with pytest.raises(RuntimeError, match="Failed to stream dataset"):
                list(stream_dataset("fake/dataset"))

    def test_process_in_chunks(self):
        """Test that process_in_chunks yields correct chunk sizes."""
        data = [{"id": i} for i in range(10)]
        chunks = list(process_in_chunks(iter(data), chunk_size=3))

        assert len(chunks) == 4  # 3, 3, 3, 1
        assert len(chunks[0]) == 3
        assert len(chunks[-1]) == 1

    def test_process_in_chunks_with_fn(self):
        """Test process_in_chunks with a processing function."""
        data = [{"value": i} for i in range(5)]
        def double_values(chunk):
            return [item["value"] * 2 for item in chunk]

        results = list(process_in_chunks(iter(data), chunk_size=2, process_fn=double_values))
        assert results == [[0, 2], [4, 6], [8]]

    def test_accumulate_statistics_basic(self):
        """Test basic statistics accumulation."""
        data = [
            {"text": "hello world"},
            {"text": "foo bar baz"},
            {"prompt": "short"}
        ]

        stats = accumulate_statistics(iter(data))

        assert stats["count"] == 3
        assert stats["total_tokens"] == 6  # 2 + 3 + 1
        assert stats["min_tokens"] == 1
        assert stats["max_tokens"] == 3

    def test_accumulate_statistics_with_source(self):
        """Test statistics accumulation with source tracking."""
        data = [
            {"text": "a", "source": "ultrafeedback"},
            {"text": "b", "source": "ultrafeedback"},
            {"text": "c", "source": "dolly"}
        ]

        stats = accumulate_statistics(iter(data))

        assert stats["source_counts"]["ultrafeedback"] == 2
        assert stats["source_counts"]["dolly"] == 1

    def test_filter_stream(self):
        """Test filtering a stream."""
        data = [{"id": i, "value": i * 2} for i in range(10)]
        filtered = list(filter_stream(iter(data), lambda x: x["value"] > 5))

        assert len(filtered) == 7
        assert filtered[0]["id"] == 3

    def test_sample_stream_reservoir(self):
        """Test reservoir sampling."""
        data = [{"id": i} for i in range(100)]
        sample = sample_stream(iter(data), sample_size=10, seed=42)

        assert len(sample) == 10
        # Check that all sampled items are from the original data
        ids = [item["id"] for item in sample]
        assert all(0 <= i < 100 for i in ids)

    def test_compute_dataset_checksum(self):
        """Test checksum computation."""
        data = [{"id": 1}, {"id": 2}]
        checksum1 = compute_dataset_checksum(iter(data))

        data_same = [{"id": 1}, {"id": 2}]
        checksum2 = compute_dataset_checksum(iter(data_same))

        assert checksum1 == checksum2

        data_diff = [{"id": 1}, {"id": 3}]
        checksum3 = compute_dataset_checksum(iter(data_diff))
        assert checksum1 != checksum3

    def test_write_chunked_output(self):
        """Test writing chunked output to file."""
        data = [{"id": i} for i in range(5)]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"
            result_path = write_chunked_output(iter(data), str(output_path), chunk_size=2)

            assert Path(result_path).exists()
            with open(result_path, "r") as f:
                content = json.load(f)
            assert len(content) == 5

    def test_merge_chunked_outputs(self):
        """Test merging multiple chunk files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            chunk1 = Path(tmpdir) / "chunk1.json"
            chunk2 = Path(tmpdir) / "chunk2.json"
            merged = Path(tmpdir) / "merged.json"

            # Create chunk files
            with open(chunk1, "w") as f:
                json.dump([{"id": 1}, {"id": 2}], f)
            with open(chunk2, "w") as f:
                json.dump([{"id": 3}, {"id": 4}], f)

            result_path = merge_chunked_outputs([str(chunk1), str(chunk2)], str(merged))

            assert Path(result_path).exists()
            with open(result_path, "r") as f:
                content = json.load(f)
            assert len(content) == 4
            assert content[0]["id"] == 1
            assert content[3]["id"] == 4


class TestEdgeCases:
    """Test edge cases for streaming loader functions."""

    def test_empty_stream_statistics(self):
        """Test statistics on empty stream."""
        stats = accumulate_statistics(iter([]))
        assert stats["count"] == 0
        assert stats["min_tokens"] == 0
        assert stats["max_tokens"] == 0

    def test_empty_stream_filter(self):
        """Test filtering empty stream."""
        result = list(filter_stream(iter([]), lambda x: True))
        assert result == []

    def test_sample_stream_empty(self):
        """Test sampling from empty stream."""
        sample = sample_stream(iter([]), sample_size=5)
        assert sample == []

    def test_process_in_chunks_empty(self):
        """Test process_in_chunks with empty stream."""
        chunks = list(process_in_chunks(iter([]), chunk_size=5))
        assert chunks == []

    def test_write_chunked_output_empty(self):
        """Test writing empty stream to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty.json"
            write_chunked_output(iter([]), str(output_path))

            with open(output_path, "r") as f:
                content = json.load(f)
            assert content == []

    def test_merge_with_missing_file(self):
        """Test merging when one file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            chunk1 = Path(tmpdir) / "chunk1.json"
            merged = Path(tmpdir) / "merged.json"

            with open(chunk1, "w") as f:
                json.dump([{"id": 1}], f)

            # Missing chunk2 should be ignored
            result_path = merge_chunked_outputs([str(chunk1), "nonexistent.json"], str(merged))

            with open(result_path, "r") as f:
                content = json.load(f)
            assert len(content) == 1
            assert content[0]["id"] == 1
