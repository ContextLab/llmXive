import json
import os
import tempfile
import numpy as np
from pathlib import Path
import pytest

# Add parent directory to path for imports if running as standalone
# In actual execution, this is handled by the project structure
import sys
from unittest.mock import patch

# Import the module under test
# Assuming tests are run from project root or code/
try:
    from analysis.sweep_checksums import (
        compute_file_sha256,
        find_sweep_matrices,
        checksum_sweep_matrices,
        main
    )
except ImportError:
    # Fallback for different execution contexts
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from analysis.sweep_checksums import (
        compute_file_sha256,
        find_sweep_matrices,
        checksum_sweep_matrices,
        main
    )


class TestComputeFileSha256:
    def test_compute_sha256_correctness(self, tmp_path):
        """Verify SHA-256 computation is correct for known input."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        checksum = compute_file_sha256(test_file)
        
        # Known SHA-256 for "Hello, World!"
        expected = "d9014c4624844aa5bac314773d6b689ad467fa4e1d1a50a1b8a99d5a95f72ff5"
        assert checksum == expected

    def test_compute_sha256_nonexistent_file(self, tmp_path):
        """Verify FileNotFoundError is raised for missing file."""
        missing_file = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            compute_file_sha256(missing_file)


class TestFindSweepMatrices:
    def test_find_matrices_in_sweep_dir(self, tmp_path):
        """Verify finding .npy files in the sweep directory structure."""
        sweep_dir = tmp_path / "data" / "raw" / "sweep"
        sweep_dir.mkdir(parents=True)
        
        # Create dummy matrix files
        (sweep_dir / "matrix_N100_theta2.5_seed42.npy").touch()
        (sweep_dir / "matrix_N200_theta1.0_seed99.npy").touch()
        (sweep_dir / "other_file.txt").touch() # Should be ignored
        
        found = find_sweep_matrices(tmp_path)
        
        assert len(found) == 2
        # Verify paths are returned
        assert all(f.suffix == ".npy" for f in found)

    def test_find_matrices_empty_dir(self, tmp_path):
        """Verify empty list when no matrices exist."""
        sweep_dir = tmp_path / "data" / "raw" / "sweep"
        sweep_dir.mkdir(parents=True)
        
        found = find_sweep_matrices(tmp_path)
        assert len(found) == 0

    def test_find_matrices_missing_dir(self, tmp_path):
        """Verify empty list when sweep directory is missing."""
        found = find_sweep_matrices(tmp_path)
        assert len(found) == 0


class TestChecksumSweepMatrices:
    def test_checksum_sweep_creates_manifest(self, tmp_path):
        """Verify checksum_sweep_matrices creates a valid JSON manifest."""
        # Setup sweep directory with dummy matrices
        sweep_dir = tmp_path / "data" / "raw" / "sweep"
        sweep_dir.mkdir(parents=True)
        
        # Create a real numpy array to ensure valid .npy
        matrix_path = sweep_dir / "matrix_N100_theta2.5_seed42.npy"
        np.save(str(matrix_path), np.random.rand(10, 10))
        
        output_path = tmp_path / "state" / "checksums_sweep.json"
        
        # Run the function
        manifest = checksum_sweep_matrices(tmp_path, output_path)
        
        # Verify manifest structure
        assert "algorithm" in manifest
        assert manifest["algorithm"] == "SHA-256"
        assert "total_files" in manifest
        assert manifest["total_files"] == 1
        assert "checksums" in manifest
        assert len(manifest["checksums"]) == 1
        assert "status" in manifest
        assert manifest["status"] == "complete"
        
        # Verify file exists on disk
        assert output_path.exists()
        
        # Verify JSON content matches manifest
        with open(output_path, "r") as f:
            disk_manifest = json.load(f)
        
        assert disk_manifest["total_files"] == 1
        assert "matrix_N100_theta2.5_seed42.npy" in disk_manifest["checksums"].values() or \
               any("matrix_N100_theta2.5_seed42.npy" in k for k in disk_manifest["checksums"].keys())

    def test_checksum_sweep_no_files_raises(self, tmp_path):
        """Verify FileNotFoundError is raised when no matrices are found."""
        output_path = tmp_path / "state" / "checksums_sweep.json"
        
        with pytest.raises(FileNotFoundError, match="No raw matrix instances found"):
            checksum_sweep_matrices(tmp_path, output_path)


class TestMain:
    def test_main_success(self, tmp_path):
        """Verify main() returns 0 on success."""
        # Setup
        sweep_dir = tmp_path / "data" / "raw" / "sweep"
        sweep_dir.mkdir(parents=True)
        matrix_path = sweep_dir / "matrix_N100_theta2.5_seed42.npy"
        np.save(str(matrix_path), np.ones((5, 5)))
        
        # Mock cwd to be tmp_path
        with patch('pathlib.Path.cwd', return_value=tmp_path):
            result = main()
        
        assert result == 0
        assert (tmp_path / "state" / "checksums_sweep.json").exists()

    def test_main_missing_data(self, tmp_path):
        """Verify main() returns 1 when data is missing."""
        with patch('pathlib.Path.cwd', return_value=tmp_path):
            result = main()
        
        assert result == 1