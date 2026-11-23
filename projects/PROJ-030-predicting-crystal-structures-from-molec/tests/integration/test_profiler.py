"""
Integration tests for the data loading pipeline profiler.

Tests verify that:
- The profiler runs without errors
- Output file is created with valid JSON
- Metrics contain expected fields
- Throughput is positive and reasonable
"""

import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion.profiler import profile_streaming_pipeline, measure_chunk_performance


class TestProfilerIntegration:
    """Integration tests for the profiler module."""
    
    def test_profile_creates_output_file(self):
        """Test that profiling creates the output JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metrics.json"
            
            # Profile with a small limit to keep test fast
            result = profile_streaming_pipeline(
                output_path=str(output_path),
                max_chunks=2  # Only process 2 chunks for speed
            )
            
            # Verify file exists
            assert output_path.exists(), "Output file was not created"
            
            # Verify JSON is valid
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert isinstance(data, dict), "Output is not a dictionary"
    
    def test_profile_results_contain_required_fields(self):
        """Test that profile results contain all required metric fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metrics.json"
            
            result = profile_streaming_pipeline(
                output_path=str(output_path),
                max_chunks=1
            )
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            # Check required top-level fields
            required_fields = [
                "profile_timestamp",
                "total_chunks_processed",
                "total_rows_processed",
                "total_time_seconds",
                "overall_throughput_rows_per_second",
                "peak_memory_bytes",
                "chunk_details"
            ]
            
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
    
    def test_throughput_is_positive(self):
        """Test that measured throughput is positive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metrics.json"
            
            result = profile_streaming_pipeline(
                output_path=str(output_path),
                max_chunks=2
            )
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            throughput = data["overall_throughput_rows_per_second"]
            assert throughput > 0, f"Throughput should be positive, got {throughput}"
    
    def test_chunk_details_have_per_chunk_metrics(self):
        """Test that chunk details contain per-chunk metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metrics.json"
            
            result = profile_streaming_pipeline(
                output_path=str(output_path),
                max_chunks=3
            )
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            chunk_details = data["chunk_details"]
            assert len(chunk_details) > 0, "No chunk details recorded"
            
            # Check first chunk has required fields
            first_chunk = chunk_details[0]
            required_chunk_fields = [
                "chunk_id",
                "row_count",
                "processing_time_seconds",
                "rows_per_second",
                "current_memory_bytes",
                "peak_memory_bytes"
            ]
            
            for field in required_chunk_fields:
                assert field in first_chunk, f"Chunk missing field: {field}"
    
    def test_measure_chunk_performance_returns_valid_metrics(self):
        """Test the low-level chunk measurement function."""
        # Create a mock chunk
        mock_chunk = [{"id": i, "value": f"test_{i}"} for i in range(10)]
        
        metrics = measure_chunk_performance(mock_chunk, chunk_id=0)
        
        assert metrics["chunk_id"] == 0
        assert metrics["row_count"] == 10
        assert metrics["processing_time_seconds"] >= 0
        assert metrics["rows_per_second"] > 0
        assert metrics["current_memory_bytes"] >= 0
        assert metrics["peak_memory_bytes"] >= 0
    
    def test_max_chunks_limit_works(self):
        """Test that max_chunks parameter limits the number of chunks processed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metrics.json"
            
            result = profile_streaming_pipeline(
                output_path=str(output_path),
                max_chunks=1
            )
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["total_chunks_processed"] == 1
            assert data["max_chunks_limited"] is True
    
    def test_sample_rows_parameter_works(self):
        """Test that sample_rows parameter limits rows per chunk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metrics.json"
            
            result = profile_streaming_pipeline(
                output_path=str(output_path),
                max_chunks=1,
                sample_rows_per_chunk=5
            )
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            # First chunk should have at most 5 rows
            first_chunk = data["chunk_details"][0]
            assert first_chunk["row_count"] <= 5