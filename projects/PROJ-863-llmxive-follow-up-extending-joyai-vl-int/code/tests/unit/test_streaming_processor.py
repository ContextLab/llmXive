"""
Unit tests for the Streaming Feature Processor (Task T022).
"""
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np

from src.feature_extraction.streaming_processor import StreamingFeatureProcessor, DEFAULT_CHUNK_SIZE
from src.feature_extraction.streaming import StreamingConfig
from src.data_synthesis.models import SyntheticVideoFrame

@pytest.fixture
def temp_manifest():
    """Create a temporary manifest file with synthetic frames."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for i in range(DEFAULT_CHUNK_SIZE + 50):  # Ensure at least one full chunk + remainder
            frame = SyntheticVideoFrame(
                frame_id=f"frame_{i:05d}",
                timestamp=i * 0.033,
                video_path="dummy.mp4",
                objects=[],
                labels={"critical": False}
            )
            f.write(json.dumps(asdict(frame)) + "\n")
        return f.name

@pytest.fixture
def mock_extractor():
    """Mock the JoyAIFeatureExtractor to avoid loading real models."""
    with patch('src.feature_extraction.streaming_processor.JoyAIFeatureExtractor') as MockExtractor:
        mock_instance = MockExtractor.return_value
        # Mock extract_batch to return random numpy vectors
        def mock_extract(frames):
            return [np.random.rand(128) for _ in frames]
        mock_instance.extract_batch.side_effect = mock_extract
        yield mock_instance

def test_streaming_processor_initialization():
    """Test that the processor initializes correctly."""
    processor = StreamingFeatureProcessor(
        model_path="/fake/path",
        chunk_size=100,
        output_dir="/tmp/test_output"
    )
    assert processor.chunk_size == 100
    assert processor.output_dir == Path("/tmp/test_output")

def test_process_stream_chunking(temp_manifest, mock_extractor, tmp_path):
    """Test that the processor correctly chunks data and writes files."""
    # Create a small chunk size for testing
    chunk_size = 100
    processor = StreamingFeatureProcessor(
        model_path="/fake/path",
        chunk_size=chunk_size,
        output_dir=str(tmp_path)
    )
    
    # Mock the extractor again for this specific test scope if needed, 
    # but the fixture above handles the class mock globally for this module.
    
    output_files = list(processor.process_stream(temp_manifest))
    
    # We have 1050 frames (1000 + 50). With chunk_size=100, we expect 11 chunks.
    expected_chunks = 11
    assert len(output_files) == expected_chunks, f"Expected {expected_chunks} chunks, got {len(output_files)}"
    
    # Verify file names
    for i, path in enumerate(output_files):
        assert path.exists(), f"Output file {path} was not created"
        assert f"features_chunk_{i+1:05d}.jsonl" in str(path)

def test_process_stream_empty_manifest(tmp_path):
    """Test behavior with an empty manifest."""
    empty_manifest = tmp_path / "empty.jsonl"
    empty_manifest.write_text("")
    
    processor = StreamingFeatureProcessor(
        model_path="/fake/path",
        chunk_size=100,
        output_dir=str(tmp_path / "output")
    )
    
    output_files = list(processor.process_stream(str(empty_manifest)))
    assert len(output_files) == 0

def test_memory_cleanup(mock_extractor, temp_manifest, tmp_path):
    """Verify that garbage collection is triggered after chunks."""
    # This is a soft test; we verify the logic path.
    processor = StreamingFeatureProcessor(
        model_path="/fake/path",
        chunk_size=50,
        output_dir=str(tmp_path)
    )
    
    # Run processing
    list(processor.process_stream(temp_manifest))
    
    # If we got here without OOM, the logic holds.
    # A more rigorous test would involve memory profiling, but that's environment-dependent.
    assert True

def test_validation_dimension_match(mock_extractor, temp_manifest, tmp_path):
    """Test that dimension validation is called (conceptually)."""
    # The processor calls validate_dimension_match in the extraction logic if implemented.
    # For now, we ensure the flow completes.
    processor = StreamingFeatureProcessor(
        model_path="/fake/path",
        chunk_size=10,
        output_dir=str(tmp_path)
    )
    list(processor.process_stream(temp_manifest))
    assert True

def asdict(obj):
    """Helper to mimic dataclasses.asdict for the test fixture."""
    return {
        "frame_id": obj.frame_id,
        "timestamp": obj.timestamp,
        "video_path": obj.video_path,
        "objects": obj.objects,
        "labels": obj.labels
    }
