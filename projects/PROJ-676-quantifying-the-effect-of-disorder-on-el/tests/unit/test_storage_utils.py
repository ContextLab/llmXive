"""
Unit tests for storage_utils.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from code.storage_utils import (
    _compute_sha256,
    _load_provenance,
    _save_provenance,
    log_provenance_entry,
    save_hamiltonian_to_hdf5,
    save_eigenstates_to_hdf5,
)


def test_compute_sha256_numpy_array():
    """Test SHA-256 computation on a numpy array."""
    arr = np.array([1, 2, 3], dtype=np.float64)
    hash1 = _compute_sha256(arr)
    hash2 = _compute_sha256(arr)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length


def test_compute_sha256_bytes():
    """Test SHA-256 computation on bytes."""
    data = b"test data"
    hash_val = _compute_sha256(data)
    assert len(hash_val) == 64


def test_log_provenance_entry(tmp_path):
    """Test logging a provenance entry."""
    # Mock the provenance path
    with patch("code.storage_utils._get_provenance_path") as mock_path:
        mock_path.return_value = tmp_path / "provenance.json"

        log_provenance_entry(
            artifact_path="data/raw/test.h5",
            artifact_type="hamiltonian",
            checksum="abc123",
            metadata={"W": 1.0, "L": 100}
        )

        # Verify file was created
        assert (tmp_path / "provenance.json").exists()

        # Verify content
        with open(tmp_path / "provenance.json", "r") as f:
            data = json.load(f)

        assert len(data["entries"]) == 1
        assert data["entries"][0]["artifact_path"] == "data/raw/test.h5"
        assert data["entries"][0]["checksum"] == "abc123"
        assert data["entries"][0]["metadata"]["W"] == 1.0


def test_save_hamiltonian_to_hdf5(tmp_path):
    """Test saving a Hamiltonian to HDF5."""
    hamiltonian = np.random.rand(10, 10)
    disorder_params = {"W": 1.5, "L": 10}
    realization_index = 0

    with patch("code.storage_utils._get_provenance_path") as mock_path:
        mock_path.return_value = tmp_path / "provenance.json"
        with patch("code.storage_utils.get_config") as mock_config:
            mock_config.return_value.DATA_RAW_DIR = str(tmp_path / "data_raw")
            mock_config.return_value.DATA_METADATA_DIR = str(tmp_path)
            mock_config.return_value.RANDOM_SEED = 42
            mock_config.return_value.NUM_REALIZATIONS = 100

            relative_path = save_hamiltonian_to_hdf5(
                hamiltonian, disorder_params, realization_index
            )

    # Verify file exists
    assert os.path.exists(tmp_path / "data_raw" / os.path.basename(relative_path))

    # Verify provenance logged
    with open(tmp_path / "provenance.json", "r") as f:
        data = json.load(f)
    assert len(data["entries"]) == 1
    assert data["entries"][0]["artifact_type"] == "hamiltonian"


def test_save_eigenstates_to_hdf5(tmp_path):
    """Test saving eigenstates to HDF5."""
    eigenvalues = np.random.rand(10)
    eigenstates = np.random.rand(10, 10)
    disorder_params = {"W": 2.0, "L": 10}
    realization_index = 1

    with patch("code.storage_utils._get_provenance_path") as mock_path:
        mock_path.return_value = tmp_path / "provenance.json"
        with patch("code.storage_utils.get_config") as mock_config:
            mock_config.return_value.DATA_PROCESSED_DIR = str(tmp_path / "data_processed")
            mock_config.return_value.DATA_METADATA_DIR = str(tmp_path)
            mock_config.return_value.RANDOM_SEED = 42
            mock_config.return_value.NUM_REALIZATIONS = 100

            relative_path = save_eigenstates_to_hdf5(
                eigenvalues, eigenstates, disorder_params, realization_index
            )

    # Verify file exists
    assert os.path.exists(tmp_path / "data_processed" / os.path.basename(relative_path))

    # Verify provenance logged
    with open(tmp_path / "provenance.json", "r") as f:
        data = json.load(f)
    assert len(data["entries"]) == 1
    assert data["entries"][0]["artifact_type"] == "eigenstates"