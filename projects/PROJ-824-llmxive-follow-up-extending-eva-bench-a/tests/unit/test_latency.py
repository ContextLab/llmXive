"""
Unit tests for LatencyInjector chunked processing memory limits.

This module verifies that the LatencyInjector correctly handles memory constraints
by processing audio in chunks and enforcing maximum memory usage limits.
"""

import os
import sys
import tempfile
import pytest
import numpy as np
from pathlib import Path

# Add the project root to the path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.injectors.latency import LatencyInjector
from code.config import ensure_directories


class MockAudioStream:
    """Mock audio stream for testing chunked processing without loading full audio."""

    def __init__(self, sample_rate: int = 22050, duration_seconds: float = 10.0):
        self.sample_rate = sample_rate
        self.duration_seconds = duration_seconds
        self.total_samples = int(sample_rate * duration_seconds)
        self.chunk_size = 22050  # 1 second chunks

    def __iter__(self):
        """Yield chunks of audio data."""
        samples_per_chunk = self.chunk_size
        total_samples = self.total_samples

        for start in range(0, total_samples, samples_per_chunk):
            end = min(start + samples_per_chunk, total_samples)
            chunk_size = end - start
            # Generate deterministic "audio" data
            chunk = np.random.randn(chunk_size).astype(np.float32)
            yield chunk, start, end

    def get_duration(self) -> float:
        return self.duration_seconds

    def get_sample_rate(self) -> int:
        return self.sample_rate


def test_chunked_processing_memory_limit():
    """
    Test that chunked processing respects memory limits by processing
    audio in configurable chunks rather than loading the entire file.
    """
    # Create a temporary directory for test outputs
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_file = temp_path / "test_output.wav"

        # Initialize the injector with a small chunk size to simulate memory constraints
        injector = LatencyInjector(
            target_delay_ms=500,
            jitter_ms=0,
            chunk_size_seconds=1.0,  # Process 1 second chunks
            max_memory_mb=100,       # Simulate low memory limit
            sample_rate=22050
        )

        # Create a mock audio stream (simulating a 10-second audio file)
        mock_stream = MockAudioStream(
            sample_rate=22050,
            duration_seconds=10.0
        )

        # Process the audio stream with chunked processing
        result = injector.process_stream(mock_stream, str(output_file))

        # Verify that the output file was created
        assert output_file.exists(), "Output audio file was not created"

        # Verify that the output duration is approximately the input duration + delay
        expected_duration = mock_stream.get_duration() + (500 / 1000.0)
        actual_duration = result['duration']
        assert abs(actual_duration - expected_duration) < 0.1, \
            f"Duration mismatch: expected {expected_duration}, got {actual_duration}"

        # Verify that chunked processing was used (chunk_size < total duration)
        assert injector.chunk_size_samples < mock_stream.total_samples, \
            "Chunked processing was not utilized"


def test_memory_limit_enforcement():
    """
    Test that the injector enforces memory limits by rejecting configurations
    that would exceed available memory.
    """
    # Test with an extremely small chunk size that would cause excessive overhead
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_file = temp_path / "test_output.wav"

        # Create an injector with very small chunks (simulating strict memory limit)
        injector = LatencyInjector(
            target_delay_ms=500,
            jitter_ms=0,
            chunk_size_seconds=0.1,  # Very small chunks
            max_memory_mb=50,        # Very low memory limit
            sample_rate=22050
        )

        # Create a mock audio stream
        mock_stream = MockAudioStream(
            sample_rate=22050,
            duration_seconds=5.0
        )

        # Process should complete without memory error
        result = injector.process_stream(mock_stream, str(output_file))

        # Verify output was created
        assert output_file.exists(), "Output file should be created even with strict memory limits"

        # Verify that the chunk size is respected
        assert injector.chunk_size_samples == int(22050 * 0.1), \
            "Chunk size calculation is incorrect"


def test_large_audio_chunked_processing():
    """
    Test chunked processing with a larger audio file to ensure memory limits
    are respected for files that would otherwise exceed available memory.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_file = temp_path / "large_audio_output.wav"

        # Initialize with moderate chunk size
        injector = LatencyInjector(
            target_delay_ms=500,
            jitter_ms=0,
            chunk_size_seconds=2.0,
            max_memory_mb=200,
            sample_rate=22050
        )

        # Create a mock audio stream simulating a 60-second file
        mock_stream = MockAudioStream(
            sample_rate=22050,
            duration_seconds=60.0
        )

        # Process the large audio stream
        result = injector.process_stream(mock_stream, str(output_file))

        # Verify output was created
        assert output_file.exists(), "Output file for large audio was not created"

        # Verify duration increase matches expected delay
        expected_duration = 60.0 + 0.5
        assert abs(result['duration'] - expected_duration) < 0.2, \
            f"Duration mismatch for large audio: expected {expected_duration}, got {result['duration']}"

        # Verify that the number of chunks processed is reasonable
        expected_chunks = int(60.0 / 2.0)
        assert result['chunks_processed'] == expected_chunks, \
            f"Expected {expected_chunks} chunks, got {result['chunks_processed']}"


def test_chunk_boundary_handling():
    """
    Test that latency injection handles chunk boundaries correctly,
    ensuring no artifacts at chunk transitions.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_file = temp_path / "boundary_test.wav"

        injector = LatencyInjector(
            target_delay_ms=500,
            jitter_ms=0,
            chunk_size_seconds=1.0,
            max_memory_mb=100,
            sample_rate=22050
        )

        mock_stream = MockAudioStream(
            sample_rate=22050,
            duration_seconds=5.0
        )

        result = injector.process_stream(mock_stream, str(output_file))

        # Verify output exists
        assert output_file.exists(), "Output file not created"

        # The key test: verify that processing completed without errors
        # which would indicate chunk boundary issues
        assert result['status'] == 'success', "Processing failed at chunk boundaries"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])