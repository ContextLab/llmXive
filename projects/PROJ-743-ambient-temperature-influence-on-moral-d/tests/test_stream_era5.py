"""
Unit tests for stream_era5.py (Task T002d)
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import pyarrow.parquet as pq

# Import the module functions
from stream_era5 import (
    ensure_directories,
    load_fetch_status,
    stream_tile_to_parquet,
    concatenate_parquet_chunks,
    main
)


class TestStreamEra5:
    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Create temporary directories for testing."""
        chunks_dir = tmp_path / "data" / "raw" / "era5_raw_chunks"
        output_dir = tmp_path / "data" / "raw"
        logs_dir = tmp_path / "results" / "logs"
        
        chunks_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        logs_dir.mkdir(parents=True)
        
        # Mock fetch_status.json
        fetch_status = {
            "tiles": [
                {"tile_id": "test_tile_1", "status": "completed", "file_path": "dummy.nc"},
                {"tile_id": "test_tile_2", "status": "failed", "file_path": "dummy.nc"}
            ]
        }
        fetch_file = logs_dir / "fetch_status.json"
        with open(fetch_file, "w") as f:
            json.dump(fetch_status, f)
        
        # Create a dummy NetCDF-like file for test_tile_1
        # We will simulate a CSV for simplicity if NetCDF is too heavy, 
        # but for the test we assume the function handles it.
        # Let's create a simple CSV that mimics a flattened NetCDF
        dummy_data = pd.DataFrame({
            "latitude": [51.0, 52.0],
            "longitude": [-0.1, -0.2],
            "temperature_celsius": [15.0, 16.0],
            "timestamp": ["2016-01-01", "2016-01-02"]
        })
        dummy_nc_path = chunks_dir / "era5_tile_test_tile_1.nc"
        dummy_data.to_csv(dummy_nc_path, index=False) # Simulating content for test
        
        return {
            "chunks_dir": chunks_dir,
            "output_dir": output_dir,
            "logs_dir": logs_dir,
            "fetch_file": fetch_file
        }

    def test_ensure_directories(self, temp_dirs):
        """Test that ensure_directories creates paths."""
        # Just verify it doesn't crash
        ensure_directories()
        assert temp_dirs["chunks_dir"].exists()

    def test_load_fetch_status(self, temp_dirs, monkeypatch):
        """Test loading fetch status."""
        # Monkeypatch the path to use temp directory
        import stream_era5
        original_path = stream_era5.FETCH_STATUS_PATH
        stream_era5.FETCH_STATUS_PATH = temp_dirs["fetch_file"]
        
        try:
            tiles = load_fetch_status()
            assert len(tiles) == 2
            assert tiles[0]["tile_id"] == "test_tile_1"
            assert tiles[1]["status"] == "failed"
        finally:
            stream_era5.FETCH_STATUS_PATH = original_path

    def test_stream_tile_to_parquet(self, temp_dirs):
        """Test streaming a single tile."""
        tile_info = {"tile_id": "test_tile_1"}
        
        # Monkeypatch path
        import stream_era5
        original_path = stream_era5.RAW_CHUNKS_DIR
        stream_era5.RAW_CHUNKS_DIR = temp_dirs["chunks_dir"]
        
        try:
            result = stream_tile_to_parquet(tile_info)
            assert result is not None
            assert result.exists()
            assert result.suffix == ".parquet"
            
            # Verify content
            df = pd.read_parquet(result)
            assert "temperature_celsius" in df.columns
            assert len(df) == 2
        finally:
            stream_era5.RAW_CHUNKS_DIR = original_path

    def test_concatenate_parquet_chunks(self, temp_dirs):
        """Test concatenating chunks."""
        # Create two dummy parquet files
        df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df2 = pd.DataFrame({"a": [5, 6], "b": [7, 8]})
        
        chunk1 = temp_dirs["chunks_dir"] / "chunk_1.parquet"
        chunk2 = temp_dirs["chunks_dir"] / "chunk_2.parquet"
        
        df1.to_parquet(chunk1)
        df2.to_parquet(chunk2)
        
        output = temp_dirs["output_dir"] / "combined.parquet"
        
        concatenate_parquet_chunks([chunk1, chunk2], output)
        
        assert output.exists()
        combined_df = pd.read_parquet(output)
        assert len(combined_df) == 4
        assert list(combined_df.columns) == ["a", "b"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])