"""
Unit tests for raw data capture and hygiene module.

Tests Constitution Principle III compliance: raw data preservation and checksumming.
"""
import os
import json
import tempfile
from pathlib import Path
import numpy as np
import pytest

from analysis.raw_data_capture import (
    save_dense_matrix_to_npy,
    save_sparse_matrix_to_npz,
    capture_and_checksum_raw_instance,
    run_hygiene_capture
)
from utils.checksum import compute_file_checksum


class TestSaveDenseMatrix:
    def test_save_dense_matrix_creates_file(self, tmp_path):
        """Test that save_dense_matrix_to_npy creates the expected file."""
        matrix = np.random.rand(10, 10)
        output_path = tmp_path / "test_matrix.npy"
        metadata = {"N": 10, "seed": 42}
        
        checksum = save_dense_matrix_to_npy(matrix, output_path, metadata)
        
        assert output_path.exists()
        assert output_path.with_suffix('.json').exists()
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 hex length
        
    def test_save_dense_matrix_metadata(self, tmp_path):
        """Test that metadata is correctly saved alongside the matrix."""
        matrix = np.random.rand(5, 5)
        output_path = tmp_path / "test.npy"
        metadata = {"N": 5, "seed": 123, "custom_field": "value"}
        
        save_dense_matrix_to_npy(matrix, output_path, metadata)
        
        meta_path = output_path.with_suffix('.json')
        with open(meta_path, 'r') as f:
            saved_meta = json.load(f)
        
        assert saved_meta["N"] == 5
        assert saved_meta["seed"] == 123
        assert saved_meta["custom_field"] == "value"
        
    def test_save_dense_matrix_integrity(self, tmp_path):
        """Test that saved matrix can be loaded and matches original."""
        matrix = np.random.rand(7, 7)
        output_path = tmp_path / "test.npy"
        metadata = {"N": 7}
        
        save_dense_matrix_to_npy(matrix, output_path, metadata)
        
        loaded = np.load(output_path)
        np.testing.assert_array_equal(matrix, loaded)


class TestSaveSparseMatrix:
    def test_save_sparse_matrix_creates_file(self, tmp_path):
        """Test that save_sparse_matrix_to_npz creates the expected file."""
        from scipy import sparse
        matrix = sparse.random(10, 10, density=0.1, format='csr')
        output_path = tmp_path / "test_sparse.npz"
        metadata = {"N": 10}
        
        checksum = save_sparse_matrix_to_npz(matrix, output_path, metadata)
        
        assert output_path.exists()
        assert output_path.with_suffix('.json').exists()
        assert isinstance(checksum, str)
        
    def test_save_sparse_matrix_integrity(self, tmp_path):
        """Test that saved sparse matrix can be loaded and matches original."""
        from scipy import sparse
        matrix = sparse.random(5, 5, density=0.2, format='csr')
        output_path = tmp_path / "test.npz"
        metadata = {"N": 5}
        
        save_sparse_matrix_to_npz(matrix, output_path, metadata)
        
        loaded = sparse.load_npz(output_path)
        # Compare in CSR format
        np.testing.assert_array_equal(matrix.toarray(), loaded.toarray())


class TestCaptureAndChecksumRawInstance:
    def test_capture_creates_wigner_only(self, tmp_path):
        """Test capture without perturbation creates only wigner file."""
        matrix = np.random.rand(10, 10)
        
        results = capture_and_checksum_raw_instance(
            matrix=matrix,
            perturbation=None,
            seed=42,
            N=10,
            theta=2.5,
            output_dir=tmp_path
        )
        
        assert "wigner_path" in results
        assert "wigner_checksum" in results
        assert "perturbation_path" not in results
        assert os.path.exists(results["wigner_path"])
        
    def test_capture_creates_all_files(self, tmp_path):
        """Test capture with perturbation creates wigner, perturbation, and combined files."""
        matrix = np.random.rand(10, 10)
        perturbation = np.random.rand(10, 10) * 0.1
        
        results = capture_and_checksum_raw_instance(
            matrix=matrix,
            perturbation=perturbation,
            perturbation_type="diagonal",
            seed=42,
            N=10,
            theta=2.5,
            output_dir=tmp_path
        )
        
        assert "wigner_path" in results
        assert "perturbation_path" in results
        assert "combined_path" in results
        assert "wigner_checksum" in results
        assert "perturbation_checksum" in results
        assert "combined_checksum" in results
        
        # Verify files exist
        assert os.path.exists(results["wigner_path"])
        assert os.path.exists(results["perturbation_path"])
        assert os.path.exists(results["combined_path"])
        
    def test_capture_checksums_valid(self, tmp_path):
        """Test that returned checksums match actual file checksums."""
        matrix = np.random.rand(10, 10)
        perturbation = np.random.rand(10, 10) * 0.1
        
        results = capture_and_checksum_raw_instance(
            matrix=matrix,
            perturbation=perturbation,
            seed=42,
            N=10,
            theta=2.5,
            output_dir=tmp_path
        )
        
        # Verify wigner checksum
        actual_wigner_checksum = compute_file_checksum(Path(results["wigner_path"]))
        assert results["wigner_checksum"] == actual_wigner_checksum
        
        # Verify perturbation checksum
        actual_pert_checksum = compute_file_checksum(Path(results["perturbation_path"]))
        assert results["perturbation_checksum"] == actual_pert_checksum
        
        # Verify combined checksum
        actual_combined_checksum = compute_file_checksum(Path(results["combined_path"]))
        assert results["combined_checksum"] == actual_combined_checksum


class TestRunHygieneCapture:
    def test_hygiene_capture_multiple_states(self, tmp_path):
        """Test capturing multiple intermediate states."""
        matrices = {
            "initial": np.random.rand(5, 5),
            "iter_1": np.random.rand(5, 5),
            "iter_2": np.random.rand(5, 5)
        }
        metadata = {"run_id": "test_001", "method": "power_iteration"}
        
        results = run_hygiene_capture(matrices, metadata, tmp_path)
        
        assert "initial" in results
        assert "iter_1" in results
        assert "iter_2" in results
        assert "manifest_path" in results
        
        # Verify all files exist
        for state_name in matrices:
            assert os.path.exists(results[state_name]["path"])
            
    def test_hygiene_capture_manifest(self, tmp_path):
        """Test that manifest file is created with correct structure."""
        matrices = {"state1": np.random.rand(3, 3)}
        metadata = {"test": "value"}
        
        results = run_hygiene_capture(matrices, metadata, tmp_path)
        
        manifest_path = Path(results["manifest_path"])
        assert manifest_path.exists()
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert "run_id" in manifest
        assert "timestamp" in manifest
        assert "metadata" in manifest
        assert "files" in manifest
        assert "state1" in manifest["files"]
        
    def test_hygiene_capture_manifest_checksum(self, tmp_path):
        """Test that manifest checksum is valid."""
        matrices = {"state": np.random.rand(3, 3)}
        metadata = {"test": "value"}
        
        results = run_hygiene_capture(matrices, metadata, tmp_path)
        
        actual_checksum = compute_file_checksum(Path(results["manifest_path"]))
        assert results["manifest_checksum"] == actual_checksum
