"""
Unit tests for the hashing utilities.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from utils.hashing import (
    compute_file_hash,
    compute_dataframe_hash,
    hash_directory,
    save_hash_manifest,
    generate_hashes_for_artifacts
)


class TestComputeFileHash:
    def test_sha256_known_value(self, tmp_path):
        """Test hashing a file with known content."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        # Known SHA256 for "Hello, World!"
        expected = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
        result = compute_file_hash(test_file)
        assert result == expected

    def test_nonexistent_file(self, tmp_path):
        """Test that hashing a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            compute_file_hash(tmp_path / "does_not_exist.txt")

    def test_large_file_chunking(self, tmp_path):
        """Test that large files are hashed correctly using chunking."""
        test_file = tmp_path / "large.bin"
        # Create a 1MB file
        content = b"0" * (1024 * 1024)
        test_file.write_bytes(content)

        result = compute_file_hash(test_file)
        assert len(result) == 64  # SHA256 hex length

class TestComputeDataFrameHash:
    def test_consistent_hash_same_data(self):
        """Test that the same DataFrame produces the same hash."""
        df = pd.DataFrame({
            "a": [1, 2, 3],
            "b": [4.0, 5.0, 6.0],
            "c": ["x", "y", "z"]
        })

        hash1 = compute_dataframe_hash(df)
        hash2 = compute_dataframe_hash(df)
        assert hash1 == hash2

    def test_different_data_different_hash(self):
        """Test that different DataFrames produce different hashes."""
        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df2 = pd.DataFrame({"a": [1, 2, 4]})

        hash1 = compute_dataframe_hash(df1)
        hash2 = compute_dataframe_hash(df2)
        assert hash1 != hash2

    def test_order_invariance_columns(self):
        """Test that column order does not affect hash."""
        df1 = pd.DataFrame({"a": [1], "b": [2]})
        df2 = pd.DataFrame({"b": [2], "a": [1]})

        hash1 = compute_dataframe_hash(df1)
        hash2 = compute_dataframe_hash(df2)
        assert hash1 == hash2

class TestHashDirectory:
    def test_empty_directory(self, tmp_path):
        """Test hashing an empty directory."""
        result = hash_directory(tmp_path)
        assert result == {}

    def test_single_file(self, tmp_path):
        """Test hashing a directory with a single file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = hash_directory(tmp_path)
        assert "test.txt" in result
        assert len(result) == 1

    def test_extension_filter(self, tmp_path):
        """Test filtering by file extension."""
        (tmp_path / "test.csv").write_text("a,b")
        (tmp_path / "test.json").write_text("{}")
        (tmp_path / "readme.md").write_text("# Readme")

        result_csv = hash_directory(tmp_path, extensions=[".csv"])
        result_all = hash_directory(tmp_path)

        assert len(result_csv) == 1
        assert "test.csv" in result_csv
        assert "test.json" not in result_csv
        assert len(result_all) == 3

class TestSaveHashManifest:
    def test_manifest_structure(self, tmp_path):
        """Test that the manifest file has the correct structure."""
        hashes = {"file1.txt": "abc123", "file2.txt": "def456"}
        output_path = tmp_path / "manifest.json"

        save_hash_manifest(hashes, output_path, tmp_path)

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)

        assert data["algorithm"] == "sha256"
        assert "source_directory" in data
        assert "files" in data
        assert data["files"] == hashes

class TestGenerateHashesForArtifacts:
    def test_full_integration(self, tmp_path):
        """Test the full artifact hashing pipeline."""
        # Create mock data and results directories
        data_dir = tmp_path / "data"
        results_dir = tmp_path / "results"
        data_dir.mkdir()
        results_dir.mkdir()

        # Create mock files
        (data_dir / "features.csv").write_text("col1,col2\n1,2")
        (results_dir / "model.pkl").write_bytes(b"mock_model_data")
        (results_dir / "metrics.json").write_text('{"rmse": 0.1}')

        manifest_path = tmp_path / "manifest.json"

        result = generate_hashes_for_artifacts(
            data_dir, results_dir, manifest_path
        )

        assert "data" in result
        assert "results" in result
        assert len(result["data"]) == 1
        assert len(result["results"]) == 2
        assert manifest_path.exists()
