"""
Unit tests for code/data_loader.py

Tests the DataChunk logic, memory mapping, and the 30-feature extraction structure.
"""
import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data_loader import DataChunk, EEGDataLoader, TOTAL_FEATURE_COUNT

class TestDataChunk:
    """Tests for the DataChunk class."""

    def test_memmap_creation(self):
        """Test that DataChunk successfully creates a memory-mapped array."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            # Create dummy data
            shape = (64, 10000)
            dtype = np.float32
            data = np.random.rand(*shape).astype(dtype)
            f.write(data.tobytes())
            temp_path = f.name

        try:
            chunk = DataChunk(
                path=Path(temp_path),
                shape=shape,
                dtype=dtype
            )
            assert chunk.memmap is not None
            assert chunk.get_data().shape == shape
            assert chunk.get_data().dtype == dtype
            # Verify data integrity
            assert np.allclose(chunk.get_data(), data)
        finally:
            os.unlink(temp_path)

    def test_memmap_slice(self):
        """Test slicing a DataChunk."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            shape = (64, 10000)
            dtype = np.float32
            data = np.random.rand(*shape).astype(dtype)
            f.write(data.tobytes())
            temp_path = f.name

        try:
            chunk = DataChunk(
                path=Path(temp_path),
                shape=shape,
                dtype=dtype
            )
            
            # Slice first channel
            sliced = chunk.slice(channel_idx=0)
            assert sliced.get_data().shape == (1, 10000)
            
            # Slice time range
            sliced_time = chunk.slice(sample_range=(0, 100))
            assert sliced_time.get_data().shape == (64, 100)
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test that DataChunk raises error for missing file."""
        with pytest.raises(FileNotFoundError):
            DataChunk(
                path=Path("/nonexistent/file.bin"),
                shape=(64, 1000),
                dtype=np.float32
            )

    def test_shape_mismatch(self):
        """Test that DataChunk raises error if file size doesn't match shape."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            # Write small data
            data = np.array([1.0, 2.0], dtype=np.float32)
            f.write(data.tobytes())
            temp_path = f.name

        try:
            # Request a shape that is too large
            with pytest.raises(ValueError):
                DataChunk(
                    path=Path(temp_path),
                    shape=(100, 100), # Way too big
                    dtype=np.float32
                )
        finally:
            os.unlink(temp_path)


class TestEEGDataLoader:
    """Tests for the EEGDataLoader class."""

    def test_init(self):
        """Test initialization of EEGDataLoader."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = EEGDataLoader(Path(tmpdir))
            assert loader.data_path == Path(tmpdir)

    def test_load_chunk(self):
        """Test loading a chunk via EEGDataLoader."""
        with tempfile.TemporaryDirectory() as tmpdir:
          # Create a dummy file
          file_path = Path(tmpdir) / "test.bin"
          shape = (32, 5000)
          dtype = np.float32
          data = np.random.rand(*shape).astype(dtype)
          file_path.write_bytes(data.tobytes())
          
          loader = EEGDataLoader(Path(tmpdir))
          chunk = loader.load_chunk("test.bin", shape, dtype)
          
          assert chunk.get_data().shape == shape
          assert chunk.get_data().dtype == dtype

    def test_extract_features_structure(self):
        """Test that extract_features returns exactly 30 features."""
        with tempfile.TemporaryDirectory() as tmpdir:
          file_path = Path(tmpdir) / "test.bin"
          shape = (64, 10000)
          dtype = np.float32
          data = np.random.rand(*shape).astype(dtype)
          file_path.write_bytes(data.tobytes())
          
          loader = EEGDataLoader(Path(tmpdir))
          chunk = loader.load_chunk("test.bin", shape, dtype)
          
          result = loader.extract_features(chunk)
          
          # Check feature count
          assert 'feature_vector' in result
          assert len(result['feature_vector']) == TOTAL_FEATURE_COUNT
          
          # Check feature names
          assert 'feature_names' in result
          assert len(result['feature_names']) == TOTAL_FEATURE_COUNT
          
          # Check no NaNs
          assert not np.isnan(result['feature_vector']).any()

    def test_feature_names_order(self):
        """Test that feature names follow the correct order (FR-002)."""
        with tempfile.TemporaryDirectory() as tmpdir:
          file_path = Path(tmpdir) / "test.bin"
          shape = (64, 10000)
          dtype = np.float32
          data = np.random.rand(*shape).astype(dtype)
          file_path.write_bytes(data.tobytes())
          
          loader = EEGDataLoader(Path(tmpdir))
          chunk = loader.load_chunk("test.bin", shape, dtype)
          
          result = loader.extract_features(chunk)
          names = result['feature_names']
          
          # Expected order:
          # 4 mean durations (A, B, C, D)
          # 4 occurrence rates (A, B, C, D)
          # 16 transition probs
          # 6 spectral powers
          
          # Check first 4 are mean durations
          for i in range(4):
              assert names[i].startswith("mean_duration_map_")
          
          # Check next 4 are occurrence rates
          for i in range(4, 8):
              assert names[i].startswith("occurrence_rate_map_")
          
          # Check last 6 are spectral power
          for i in range(24, 30):
              assert names[i].startswith("power_")

    def test_integrity_check(self):
        """Test data integrity verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
          file_path = Path(tmpdir) / "test.bin"
          data = np.random.rand(10, 100).astype(np.float32)
          file_path.write_bytes(data.tobytes())
          
          loader = EEGDataLoader(Path(tmpdir))
          
          # Should pass
          assert loader.verify_data_integrity("test.bin")
          
          # Should fail with wrong checksum
          with pytest.raises(ValueError):
              loader.verify_data_integrity("test.bin", expected_checksum="invalid_hash")