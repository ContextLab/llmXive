"""
Unit tests for src/ingestion/flatten_lora.py
"""
import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.flatten_lora import (
    load_weight_file,
    flatten_matrices,
    l2_normalize,
    process_single_file,
    validate_dimensions,
    flatten_lora_weights
)


class TestLoadWeightFile:
    """Tests for load_weight_file function."""

    def test_load_valid_npz(self, tmp_path):
        """Test loading a valid NPZ file with A and B matrices."""
        # Create test data
        a_matrix = np.random.randn(4, 8).astype(np.float32)
        b_matrix = np.random.randn(8, 4).astype(np.float32)

        # Save to temp file
        npz_file = tmp_path / "test_weights.npz"
        np.savez(npz_file, A=a_matrix, B=b_matrix)

        # Load and verify
        loaded = load_weight_file(npz_file)

        assert 'A' in loaded
        assert 'B' in loaded
        assert np.allclose(loaded['A'], a_matrix)
        assert np.allclose(loaded['B'], b_matrix)
        assert loaded['A'].shape == a_matrix.shape
        assert loaded['B'].shape == b_matrix.shape

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        missing_file = tmp_path / "nonexistent.npz"
        with pytest.raises(FileNotFoundError):
            load_weight_file(missing_file)


class TestFlattenMatrices:
    """Tests for flatten_matrices function."""

    def test_flatten_correct_dimensions(self):
        """Test that flattening produces correct vector size."""
        a_matrix = np.random.randn(4, 8)
        b_matrix = np.random.randn(8, 4)

        weight_dict = {'A': a_matrix, 'B': b_matrix}

        vector, metadata = flatten_matrices(weight_dict)

        expected_size = a_matrix.size + b_matrix.size
        assert vector.shape[0] == expected_size
        assert metadata['a_size'] == a_matrix.size
        assert metadata['b_size'] == b_matrix.size
        assert metadata['total_size'] == expected_size

    def test_flatten_missing_matrices(self):
        """Test that ValueError is raised when A or B is missing."""
        with pytest.raises(ValueError):
            flatten_matrices({'A': np.random.randn(4, 8)})

        with pytest.raises(ValueError):
            flatten_matrices({'B': np.random.randn(8, 4)})

    def test_flatten_non_2d(self):
        """Test that ValueError is raised for non-2D matrices."""
        with pytest.raises(ValueError):
            flatten_matrices({
                'A': np.random.randn(4, 8, 2),
                'B': np.random.randn(8, 4)
            })


class TestL2Normalize:
    """Tests for l2_normalize function."""

    def test_normalize_unit_length(self):
        """Test that normalized vector has unit length."""
        vector = np.random.randn(100)
        normalized = l2_normalize(vector)

        norm = np.linalg.norm(normalized)
        assert np.isclose(norm, 1.0)

    def test_normalize_zero_vector(self):
        """Test handling of zero vector."""
        zero_vector = np.zeros(100)
        normalized = l2_normalize(zero_vector)

        # Should return zero vector unchanged
        assert np.allclose(normalized, zero_vector)

    def test_normalize_preserves_direction(self):
        """Test that normalization preserves direction."""
        vector = np.array([3.0, 4.0])
        normalized = l2_normalize(vector)

        # Original direction: [3/5, 4/5]
        expected = np.array([0.6, 0.8])
        assert np.allclose(normalized, expected)


class TestProcessSingleFile:
    """Tests for process_single_file function."""

    def test_full_pipeline(self, tmp_path):
        """Test complete processing pipeline."""
        # Create test data
        a_matrix = np.random.randn(4, 8).astype(np.float32)
        b_matrix = np.random.randn(8, 4).astype(np.float32)

        npz_file = tmp_path / "test.npz"
        np.savez(npz_file, A=a_matrix, B=b_matrix)

        vector, metadata = process_single_file(npz_file)

        # Check normalization
        assert np.isclose(np.linalg.norm(vector), 1.0)
        assert metadata['normalized'] is True
        assert metadata['a_shape'] == list(a_matrix.shape)
        assert metadata['b_shape'] == list(b_matrix.shape)


class TestValidateDimensions:
    """Tests for validate_dimensions function."""

    def test_consistent_dimensions(self):
        """Test that consistent dimensions pass validation."""
        vectors = [
            np.random.randn(100),
            np.random.randn(100),
            np.random.randn(100)
        ]
        names = ['v1', 'v2', 'v3']

        assert validate_dimensions(vectors, names) is True

    def test_inconsistent_dimensions(self):
        """Test that inconsistent dimensions raise ValueError."""
        vectors = [
            np.random.randn(100),
            np.random.randn(200),
            np.random.randn(100)
        ]
        names = ['v1', 'v2', 'v3']

        with pytest.raises(ValueError):
            validate_dimensions(vectors, names)

    def test_single_vector(self):
        """Test that single vector passes validation."""
        vectors = [np.random.randn(100)]
        names = ['v1']

        assert validate_dimensions(vectors, names) is True


class TestFlattenLoraWeights:
    """Tests for main flatten_lora_weights function."""

    def test_process_multiple_files(self, tmp_path):
        """Test processing multiple weight files."""
        # Create input directory
        input_dir = tmp_path / "raw"
        input_dir.mkdir()

        output_dir = tmp_path / "processed"
        output_dir.mkdir()

        # Create test files
        for i in range(3):
            a_matrix = np.random.randn(4, 8).astype(np.float32)
            b_matrix = np.random.randn(8, 4).astype(np.float32)
            np.savez(input_dir / f"weight_{i}.npz", A=a_matrix, B=b_matrix)

        # Run flattening
        result = flatten_lora_weights(input_dir, output_dir)

        # Verify outputs
        assert 'vectors' in result
        assert 'metadata' in result
        assert 'index_file' in result

        # Check index file exists
        assert result['index_file'].exists()

        # Load and verify shape
        loaded_matrix = np.load(result['index_file'])
        assert loaded_matrix.shape[0] == 3  # 3 files
        assert loaded_matrix.shape[1] == 96  # 4*8 + 8*4 = 32 + 64 = 96

        # Check metadata file exists
        assert result['metadata_file'].exists()

        # Verify all vectors are normalized
        for vec in loaded_matrix:
            assert np.isclose(np.linalg.norm(vec), 1.0)

    def test_empty_directory(self, tmp_path):
        """Test that empty directory raises FileNotFoundError."""
        input_dir = tmp_path / "empty_raw"
        input_dir.mkdir()

        output_dir = tmp_path / "processed"
        output_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            flatten_lora_weights(input_dir, output_dir)

    def test_dimension_mismatch(self, tmp_path):
        """Test that dimension mismatch raises ValueError."""
        input_dir = tmp_path / "raw"
        input_dir.mkdir()

        output_dir = tmp_path / "processed"
        output_dir.mkdir()

        # Create files with different dimensions
        a1, b1 = np.random.randn(4, 8), np.random.randn(8, 4)
        a2, b2 = np.random.randn(2, 4), np.random.randn(4, 2)

        np.savez(input_dir / "weight_1.npz", A=a1, B=b1)
        np.savez(input_dir / "weight_2.npz", A=a2, B=b2)

        with pytest.raises(ValueError):
            flatten_lora_weights(input_dir, output_dir)