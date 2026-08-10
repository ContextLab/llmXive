"""
Unit tests for src/ingestion/flatten_lora.py

Tests:
  - load_weights_npz: Verify loading of .npz files with standard LoRA keys
  - flatten_and_normalize: Verify flattening and L2 normalization logic
  - process_weights_file: Verify end-to-end processing and file output
  - Dimension consistency checks
"""

import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from ingestion.flatten_lora import (
    load_weights_npz,
    flatten_and_normalize,
    process_weights_file
)


class TestLoadWeightsNpz:
    def test_load_standard_lora_keys(self, tmp_path):
        """Test loading .npz file with 'A' and 'B' keys"""
        A = np.random.rand(4096, 8).astype(np.float32)
        B = np.random.rand(8, 4096).astype(np.float32)

        filepath = tmp_path / "test_weights.npz"
        np.savez(filepath, A=A, B=B)

        result = load_weights_npz(filepath)

        assert 'A' in result
        assert 'B' in result
        np.testing.assert_array_equal(result['A'], A)
        np.testing.assert_array_equal(result['B'], B)

    def test_load_lora_A_B_keys(self, tmp_path):
        """Test loading .npz file with 'lora_A' and 'lora_B' keys"""
        A = np.random.rand(4096, 8).astype(np.float32)
        B = np.random.rand(8, 4096).astype(np.float32)

        filepath = tmp_path / "test_weights.npz"
        np.savez(filepath, lora_A=A, lora_B=B)

        result = load_weights_npz(filepath)

        assert 'A' in result
        assert 'B' in result
        np.testing.assert_array_equal(result['A'], A)
        np.testing.assert_array_equal(result['B'], B)

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file"""
        with pytest.raises(FileNotFoundError):
            load_weights_npz(tmp_path / "nonexistent.npz")

    def test_incompatible_dimensions(self, tmp_path):
        """Test handling of incompatible A/B dimensions"""
        A = np.random.rand(100, 8).astype(np.float32)
        B = np.random.rand(10, 200).astype(np.float32)  # Incompatible

        filepath = tmp_path / "test_weights.npz"
        np.savez(filepath, A=A, B=B)

        with pytest.raises(ValueError):
            load_weights_npz(filepath)
            flatten_and_normalize(A, B)


class TestFlattenAndNormalize:
    def test_flatten_and_normalize_basic(self):
        """Test basic flattening and normalization"""
        A = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)  # 2x2
        B = np.array([[5.0, 6.0], [7.0, 8.0]], dtype=np.float32)  # 2x2

        vector, in_f, out_f, rank = flatten_and_normalize(A, B)

        # Expected: A_flat = [1, 2, 3, 4], B_flat = [5, 6, 7, 8]
        # Combined = [1, 2, 3, 4, 5, 6, 7, 8]
        expected_combined = np.array([1, 2, 3, 4, 5, 6, 7, 8], dtype=np.float32)
        expected_norm = np.linalg.norm(expected_combined)
        expected_normalized = expected_combined / expected_norm

        assert vector.shape == (8,)
        np.testing.assert_array_almost_equal(vector, expected_normalized)
        assert in_f == 2
        assert out_f == 2
        assert rank == 2

    def test_l2_normalization(self):
        """Test that the output vector has unit L2 norm"""
        A = np.random.rand(100, 10).astype(np.float32)
        B = np.random.rand(10, 100).astype(np.float32)

        vector, _, _, _ = flatten_and_normalize(A, B)

        norm = np.linalg.norm(vector)
        assert np.isclose(norm, 1.0, atol=1e-6)

    def test_zero_norm_handling(self):
        """Test handling of zero-norm vectors"""
        A = np.zeros((10, 5), dtype=np.float32)
        B = np.zeros((5, 10), dtype=np.float32)

        vector, in_f, out_f, rank = flatten_and_normalize(A, B)

        assert np.allclose(vector, 0)
        assert in_f == 10
        assert out_f == 10
        assert rank == 5

    def test_dimension_consistency(self):
        """Test that dimensions are correctly inferred"""
        A = np.random.rand(4096, 8).astype(np.float32)
        B = np.random.rand(8, 4096).astype(np.float32)

        vector, in_f, out_f, rank = flatten_and_normalize(A, B)

        assert in_f == 4096
        assert out_f == 4096
        assert rank == 8
        assert vector.size == 4096 * 8 * 2  # A + B


class TestProcessWeightsFile:
    def test_process_weights_file_success(self, tmp_path):
        """Test successful processing of a weight file"""
        A = np.random.rand(100, 10).astype(np.float32)
        B = np.random.rand(10, 100).astype(np.float32)

        input_path = tmp_path / "input.npz"
        np.savez(input_path, A=A, B=B)

        output_path = tmp_path / "output.npz"

        result = process_weights_file(input_path, output_path, "test_task")

        assert result['status'] == 'success'
        assert result['task_id'] == 'test_task'
        assert output_path.exists()

        # Verify output content
        data = np.load(output_path)
        assert 'vector' in data
        assert 'task_id' in data
        assert 'in_features' in data
        assert 'out_features' in data
        assert 'rank' in data

        # Verify normalization
        vector = data['vector']
        norm = np.linalg.norm(vector)
        assert np.isclose(norm, 1.0, atol=1e-6)

    def test_process_weights_file_missing_input(self, tmp_path):
        """Test handling of missing input file"""
        output_path = tmp_path / "output.npz"
        input_path = tmp_path / "nonexistent.npz"

        result = process_weights_file(input_path, output_path, "test_task")

        assert result['status'] == 'failed'
        assert 'error' in result