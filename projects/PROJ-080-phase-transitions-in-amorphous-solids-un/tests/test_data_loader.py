"""
Tests for data_loader.py - HuggingFace Streaming Implementation
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module
from data_loader import (
    RealDataFetchError,
    ChecksumValidationError,
    FatalError,
    get_schema_path,
    load_schema,
    compute_sha256,
    write_artifact_hashes,
    read_artifact_hashes,
    verify_checksum_local,
    download_and_verify_shard,
    load_verified_dataset_streaming,
    generate_synthetic_data_if_missing,
    load_synthetic_data,
    stream_trajectories,
    get_trajectory_metadata,
    compute_and_store_hashes,
    validate_checksums,
    main
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_h5_file(temp_dir):
    """Create a mock HDF5 file for testing."""
    import h5py
    file_path = temp_dir / "test.h5"
    with h5py.File(file_path, 'w') as f:
        f.create_dataset('particles', data=[[1, 2, 3], [4, 5, 6]])
        f.create_dataset('box_dimensions', data=[10, 10, 10])
    return file_path

def test_get_schema_path():
    """Test schema path generation."""
    path = get_schema_path("trajectory")
    assert path == Path("specs/contracts/trajectory.yaml")

def test_compute_sha256(temp_dir):
    """Test SHA-256 computation."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("test content")
    
    hash1 = compute_sha256(file_path)
    hash2 = compute_sha256(file_path)
    
    assert len(hash1) == 64  # SHA-256 hex length
    assert hash1 == hash2

def test_write_and_read_artifact_hashes(temp_dir, monkeypatch):
    """Test writing and reading artifact hashes."""
    monkeypatch.setattr("data_loader.STATE_FILE", str(temp_dir / "state.yaml"))
    
    test_hashes = {"file1": "abc123", "file2": "def456"}
    write_artifact_hashes(test_hashes)
    
    read_hashes = read_artifact_hashes()
    assert read_hashes == test_hashes

def test_verify_checksum_local(temp_dir):
    """Test local checksum verification."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("test content")
    
    actual_hash = compute_sha256(file_path)
    
    assert verify_checksum_local(file_path, actual_hash) == True
    assert verify_checksum_local(file_path, "wrong_hash") == False
    assert verify_checksum_local(temp_dir / "nonexistent.txt", actual_hash) == False

@patch("data_loader.load_dataset")
def test_load_verified_dataset_streaming_success(mock_load_dataset):
    """Test successful dataset loading."""
    mock_dataset = MagicMock()
    mock_dataset.__iter__ = MagicMock(return_value=iter([{"data": 1}, {"data": 2}]))
    mock_load_dataset.return_value = mock_dataset
    
    result = list(load_verified_dataset_streaming("test/dataset"))
    assert len(result) == 2
    assert result[0]["data"] == 1

@patch("data_loader.load_dataset")
def test_load_verified_dataset_streaming_failure(mock_load_dataset):
    """Test dataset loading failure."""
    from datasets.exceptions import DatasetNotFoundError
    mock_load_dataset.side_effect = DatasetNotFoundError("Not found")
    
    with pytest.raises(RealDataFetchError):
        list(load_verified_dataset_streaming("test/dataset"))

@patch("data_loader.stream_hdf5")
def test_load_synthetic_data(mock_stream_hdf5, temp_dir, monkeypatch):
    """Test synthetic data loading."""
    monkeypatch.setattr("data_loader.SYNTHETIC_DATA_DIR", str(temp_dir))
    
    # Create mock synthetic file
    mock_file = temp_dir / "synthetic_trajectory_test.h5"
    mock_file.touch()
    
    mock_stream_hdf5.return_value = iter([{"data": 1}, {"data": 2}])
    
    result = list(load_synthetic_data())
    assert len(result) == 2

@patch("data_loader.load_verified_dataset_streaming")
def test_stream_trajectories_real_success(mock_real_stream):
    """Test streaming with real data success."""
    mock_real_stream.return_value = iter([{"data": "real"}])
    
    result = list(stream_trajectories("test/dataset"))
    assert len(result) == 1
    assert result[0]["data"] == "real"
    mock_real_stream.assert_called_once()

@patch("data_loader.load_verified_dataset_streaming")
@patch("data_loader.load_synthetic_data")
def test_stream_trajectories_fallback_to_synthetic(mock_synthetic, mock_real):
    """Test fallback to synthetic data when real fails."""
    mock_real.side_effect = RealDataFetchError("Fetch failed")
    mock_synthetic.return_value = iter([{"data": "synthetic"}])
    
    result = list(stream_trajectories("test/dataset"))
    assert len(result) == 1
    assert result[0]["data"] == "synthetic"
    mock_real.assert_called_once()
    mock_synthetic.assert_called_once()

def test_get_trajectory_metadata():
    """Test metadata retrieval."""
    metadata = get_trajectory_metadata()
    
    assert "real_dataset_id" in metadata
    assert "synthetic_data_dir" in metadata
    assert "state_file" in metadata
    assert "real_data_available" in metadata
    assert "synthetic_files" in metadata

def test_main():
    """Test main function."""
    result = main()
    assert result == 0

@patch("data_loader.compute_sha256")
def test_compute_and_store_hashes(mock_compute, temp_dir, monkeypatch):
    """Test checksum computation and storage."""
    monkeypatch.setattr("data_loader.STATE_FILE", str(temp_dir / "state.yaml"))
    
    mock_compute.return_value = "test_hash"
    
    result = compute_and_store_hashes()
    assert "test_hash" in str(result)

@patch("data_loader.read_artifact_hashes")
@patch("data_loader.compute_sha256")
def test_validate_checksums_success(mock_compute, mock_read):
    """Test successful checksum validation."""
    mock_read.return_value = {"file": "abc123"}
    mock_compute.return_value = "abc123"
    
    with patch("data_loader.Path.glob", return_value=[]):
        result = validate_checksums()
        assert result == True

@patch("data_loader.read_artifact_hashes")
@patch("data_loader.compute_sha256")
def test_validate_checksums_failure(mock_compute, mock_read):
    """Test failed checksum validation."""
    mock_read.return_value = {"file": "abc123"}
    mock_compute.return_value = "wrong_hash"
    
    with patch("data_loader.Path.glob", return_value=[]):
        result = validate_checksums()
        assert result == False
