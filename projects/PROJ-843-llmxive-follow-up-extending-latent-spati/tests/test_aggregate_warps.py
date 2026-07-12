"""
Tests for the aggregate_warps module.

These tests verify that the aggregation logic correctly:
1. Scans for warped frames
2. Loads and validates individual frames
3. Aggregates frames into a single array
4. Handles edge cases (empty directory, inconsistent shapes, NaN values)
"""
import os
import tempfile
import numpy as np
from pathlib import Path
import pytest

from geometry.aggregate_warps import (
    scan_warped_frames,
    load_warped_frame,
    validate_aggregated_data,
    aggregate_warped_frames
)
from config import get_results_dir


class TestScanWarpedFrames:
    """Tests for the scan_warped_frames function."""
    
    def test_scan_empty_directory(self, tmp_path):
        """Test scanning an empty results directory."""
        results = scan_warped_frames(tmp_path)
        assert results == []
    
    def test_scan_with_valid_files(self, tmp_path):
        """Test scanning a directory with valid warped frame files."""
        # Create directory structure
        stratum_dir = tmp_path / "Static-High"
        seq_dir = stratum_dir / "seq_001"
        seq_dir.mkdir(parents=True)
        
        # Create dummy warped frames
        for i in range(5):
            frame_data = np.random.rand(100, 100, 3).astype(np.float32)
            np.save(seq_dir / f"{i}_warped.npy", frame_data)
        
        results = scan_warped_frames(tmp_path)
        assert len(results) == 5
        
        # Check that paths are sorted correctly
        for i, (path, seq_id) in enumerate(results):
            assert seq_id == "seq_001"
            assert path.stem == f"{i}_warped"
    
    def test_scan_multiple_sequences(self, tmp_path):
        """Test scanning multiple sequences."""
        # Create two sequences
        for seq_id in ["seq_001", "seq_002"]:
            seq_dir = tmp_path / "Static-High" / seq_id
            seq_dir.mkdir(parents=True)
            
            frame_data = np.random.rand(100, 100, 3).astype(np.float32)
            np.save(seq_dir / "0_warped.npy", frame_data)
        
        results = scan_warped_frames(tmp_path)
        assert len(results) == 2
        
        # Verify sorting by sequence ID
        seq_ids = [seq_id for _, seq_id in results]
        assert seq_ids == ["seq_001", "seq_002"]


class TestLoadWarpedFrame:
    """Tests for the load_warped_frame function."""
    
    def test_load_valid_frame(self, tmp_path):
        """Test loading a valid warped frame."""
        frame_data = np.random.rand(100, 100, 3).astype(np.float32)
        file_path = tmp_path / "test_warped.npy"
        np.save(file_path, frame_data)
        
        loaded = load_warped_frame(file_path)
        np.testing.assert_array_equal(loaded, frame_data)
    
    def test_load_frame_with_nan_raises(self, tmp_path):
        """Test that loading a frame with NaN raises an error."""
        frame_data = np.random.rand(100, 100, 3).astype(np.float32)
        frame_data[0, 0, 0] = np.nan
        file_path = tmp_path / "test_warped.npy"
        np.save(file_path, frame_data)
        
        with pytest.raises(ValueError, match="contains NaN or Inf values"):
            load_warped_frame(file_path)
    
    def test_load_frame_with_inf_raises(self, tmp_path):
        """Test that loading a frame with Inf raises an error."""
        frame_data = np.random.rand(100, 100, 3).astype(np.float32)
        frame_data[0, 0, 0] = np.inf
        file_path = tmp_path / "test_warped.npy"
        np.save(file_path, frame_data)
        
        with pytest.raises(ValueError, match="contains NaN or Inf values"):
            load_warped_frame(file_path)
    
    def test_load_nonexistent_file_raises(self, tmp_path):
        """Test that loading a non-existent file raises an error."""
        file_path = tmp_path / "nonexistent.npy"
        
        with pytest.raises(RuntimeError, match="Failed to load"):
            load_warped_frame(file_path)


class TestValidateAggregatedData:
    """Tests for the validate_aggregated_data function."""
    
    def test_valid_aggregation(self):
        """Test validation of a valid aggregated array."""
        data = np.random.rand(10, 100, 100, 3).astype(np.float32)
        expected_shape = (10, 100, 100, 3)
        
        assert validate_aggregated_data(data, expected_shape) is True
    
    def test_wrong_shape_raises(self):
        """Test that validation fails for wrong shape."""
        data = np.random.rand(10, 100, 100, 3).astype(np.float32)
        wrong_shape = (5, 100, 100, 3)
        
        with pytest.raises(ValueError, match="does not match expected shape"):
            validate_aggregated_data(data, wrong_shape)
    
    def test_nan_values_raises(self):
        """Test that validation fails for NaN values."""
        data = np.random.rand(10, 100, 100, 3).astype(np.float32)
        data[0, 0, 0, 0] = np.nan
        shape = (10, 100, 100, 3)
        
        with pytest.raises(ValueError, match="contains NaN or Inf values"):
            validate_aggregated_data(data, shape)
    
    def test_inf_values_raises(self):
        """Test that validation fails for Inf values."""
        data = np.random.rand(10, 100, 100, 3).astype(np.float32)
        data[0, 0, 0, 0] = np.inf
        shape = (10, 100, 100, 3)
        
        with pytest.raises(ValueError, match="contains NaN or Inf values"):
            validate_aggregated_data(data, shape)


class TestAggregateWarpedFrames:
    """Tests for the main aggregation function."""
    
    def test_aggregate_single_frame(self, tmp_path):
        """Test aggregating a single warped frame."""
        # Create a single warped frame
        stratum_dir = tmp_path / "Static-High"
        seq_dir = stratum_dir / "seq_001"
        seq_dir.mkdir(parents=True)
        
        frame_data = np.random.rand(50, 50, 3).astype(np.float32)
        np.save(seq_dir / "0_warped.npy", frame_data)
        
        output_path = tmp_path / "output.npy"
        result_path = aggregate_warped_frames(tmp_path, output_path)
        
        assert result_path == output_path
        assert output_path.exists()
        
        # Verify the saved data
        loaded = np.load(output_path)
        assert loaded.shape == (1, 50, 50, 3)
        np.testing.assert_array_equal(loaded[0], frame_data)
    
    def test_aggregate_multiple_frames(self, tmp_path):
        """Test aggregating multiple warped frames."""
        # Create multiple frames
        for i in range(3):
            stratum_dir = tmp_path / "Static-High"
            seq_dir = stratum_dir / f"seq_{i:03d}"
            seq_dir.mkdir(parents=True)
            
            frame_data = np.random.rand(50, 50, 3).astype(np.float32)
            np.save(seq_dir / "0_warped.npy", frame_data)
        
        output_path = tmp_path / "output.npy"
        result_path = aggregate_warped_frames(tmp_path, output_path)
        
        assert result_path.exists()
        
        # Verify the saved data
        loaded = np.load(output_path)
        assert loaded.shape == (3, 50, 50, 3)
    
    def test_aggregate_no_frames_raises(self, tmp_path):
        """Test that aggregation fails when no frames are found."""
        output_path = tmp_path / "output.npy"
        
        with pytest.raises(FileNotFoundError, match="No warped frames found"):
            aggregate_warped_frames(tmp_path, output_path)
    
    def test_aggregate_creates_metadata(self, tmp_path):
        """Test that aggregation creates a metadata file."""
        # Create a single frame
        stratum_dir = tmp_path / "Static-High"
        seq_dir = stratum_dir / "seq_001"
        seq_dir.mkdir(parents=True)
        
        frame_data = np.random.rand(50, 50, 3).astype(np.float32)
        np.save(seq_dir / "0_warped.npy", frame_data)
        
        output_path = tmp_path / "output.npy"
        aggregate_warped_frames(tmp_path, output_path)
        
        metadata_path = output_path.with_suffix('.json')
        assert metadata_path.exists()
        
        import json
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        assert "num_frames" in metadata
        assert metadata["num_frames"] == 1
        assert "frame_shape" in metadata
        assert metadata["dtype"] is not None