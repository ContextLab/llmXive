"""
Unit tests for the StreamingStressCurveLoader in data_loader.py.
Verifies chunked processing and memory-efficient streaming.
"""
import pytest
import csv
import json
from pathlib import Path
import tempfile
import os

from data_loader import (
    StreamingStressCurveLoader,
    load_stress_curves_streaming,
    DEFAULT_CHUNK_SIZE
)

@pytest.fixture
def sample_stress_curve_csv(tmp_path):
    """Create a sample stress curve CSV file for testing."""
    csv_path = tmp_path / "stress_curves.csv"
    
    # Create sample data
    headers = [
        "clip_id", "speaker_id", "snr_db", "rt60", 
        "sss_score", "wer_score", "collapse_intensity"
    ]
    
    rows = []
    for i in range(2500):  # 2500 rows to test multiple chunks
        rows.append({
            "clip_id": f"clip_{i}",
            "speaker_id": f"speaker_{i % 10}",
            "snr_db": str(i % 31),
            "rt60": str(0.1 + (i % 7) * 0.3),
            "sss_score": str(1.0 - (i % 100) / 200),
            "wer_score": str((i % 100) / 100),
            "collapse_intensity": str(i % 54)
        })
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    
    return csv_path

def test_streaming_loader_initialization(sample_stress_curve_csv):
    """Test that StreamingStressCurveLoader initializes correctly."""
    loader = StreamingStressCurveLoader(sample_stress_curve_csv, chunk_size=500)
    assert loader.file_path == sample_stress_curve_csv
    assert loader.chunk_size == 500

def test_streaming_loader_missing_file(tmp_path):
    """Test that StreamingStressCurveLoader raises error for missing file."""
    missing_path = tmp_path / "nonexistent.csv"
    with pytest.raises(FileNotFoundError):
        StreamingStressCurveLoader(missing_path)

def test_chunk_size_behavior(sample_stress_curve_csv):
    """Test that chunks are produced with correct size."""
    chunk_size = 500
    loader = StreamingStressCurveLoader(sample_stress_curve_csv, chunk_size=chunk_size)
    
    chunks = list(loader.stream_chunks())
    
    # Should have 5 chunks for 2500 rows with chunk_size=500
    assert len(chunks) == 5
    
    # First 4 chunks should have exactly chunk_size rows
    for i in range(4):
        assert len(chunks[i]) == chunk_size
    
    # Last chunk should have remaining rows
    assert len(chunks[4]) == 500

def test_chunk_content_integrity(sample_stress_curve_csv):
    """Test that chunk content is correct and complete."""
    loader = StreamingStressCurveLoader(sample_stress_curve_csv, chunk_size=1000)
    chunks = list(loader.stream_chunks())
    
    # Verify all rows are present
    total_rows = sum(len(chunk) for chunk in chunks)
    assert total_rows == 2500
    
    # Verify first row of first chunk
    assert chunks[0][0]["clip_id"] == "clip_0"
    assert chunks[0][0]["speaker_id"] == "speaker_0"
    
    # Verify last row of last chunk
    last_chunk = chunks[-1]
    assert last_chunk[-1]["clip_id"] == "clip_2499"

def test_load_stress_curves_streaming_function(sample_stress_curve_csv):
    """Test the convenience streaming function."""
    chunks = list(load_stress_curves_streaming(sample_stress_curve_csv, chunk_size=750))
    
    # 2500 rows / 750 chunk_size = 3 full chunks + 1 partial
    assert len(chunks) == 4
    assert len(chunks[0]) == 750
    assert len(chunks[1]) == 750
    assert len(chunks[2]) == 750
    assert len(chunks[3]) == 250

def test_aggregation_without_loading_all(sample_stress_curve_csv):
    """Test that aggregation can be done without loading all data."""
    def count_rows_aggregator(state, chunk):
        return state + len(chunk)
    
    loader = StreamingStressCurveLoader(sample_stress_curve_csv, chunk_size=500)
    total_count = loader.stream_with_aggregation(count_rows_aggregator, initial_state=0)
    
    assert total_count == 2500

def test_aggregation_compute_mean_sss(sample_stress_curve_csv):
    """Test computing mean SSS score incrementally."""
    def mean_sss_aggregator(state, chunk):
        if state is None:
            state = {"sum": 0.0, "count": 0}
        
        for row in chunk:
            state["sum"] += float(row["sss_score"])
            state["count"] += 1
        
        return state
    
    loader = StreamingStressCurveLoader(sample_stress_curve_csv, chunk_size=500)
    result = loader.stream_with_aggregation(mean_sss_aggregator, initial_state=None)
    
    expected_mean = sum(1.0 - (i % 100) / 200 for i in range(2500)) / 2500
    assert abs(result["sum"] / result["count"] - expected_mean) < 1e-6

def test_small_chunk_size(sample_stress_curve_csv):
    """Test with very small chunk size."""
    loader = StreamingStressCurveLoader(sample_stress_curve_csv, chunk_size=10)
    chunks = list(loader.stream_chunks())
    
    assert len(chunks) == 250
    for chunk in chunks[:-1]:
        assert len(chunk) == 10
    assert len(chunks[-1]) == 10

def test_large_chunk_size(sample_stress_curve_csv):
    """Test with chunk size larger than file."""
    loader = StreamingStressCurveLoader(sample_stress_curve_csv, chunk_size=5000)
    chunks = list(loader.stream_chunks())
    
    assert len(chunks) == 1
    assert len(chunks[0]) == 2500

def test_default_chunk_size_constant():
    """Verify default chunk size is reasonable for memory constraints."""
    assert DEFAULT_CHUNK_SIZE == 1000
    assert DEFAULT_CHUNK_SIZE > 0
    assert DEFAULT_CHUNK_SIZE <= 10000