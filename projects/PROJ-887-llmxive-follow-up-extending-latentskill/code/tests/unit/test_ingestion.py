"""
Unit tests for src/ingestion/flatten_lora.py (T013).
Verifies vector dimensionality matches A*B product and L2 normalization.
"""

import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ingestion.flatten_lora import flatten_and_normalize, load_npz_file, process_all_weights


class TestFlattenLoRA:
    """Tests for the flatten_and_normalize function."""

    def test_flatten_and_normalize_dimensions(self):
        """Verify output dimension matches flattened A and B shapes."""
        # Create mock LoRA weights
        rank = 16
        hidden_size = 2048
        A = np.random.randn(rank, hidden_size)
        B = np.random.randn(hidden_size, rank)

        weights = {
            'A': A,
            'B': B,
            'id': 'test_task',
            'task_desc': 'Test Description'
        }

        vec, meta = flatten_and_normalize(weights)

        expected_dim = A.size + B.size
        assert vec.shape[0] == expected_dim, f"Expected dim {expected_dim}, got {vec.shape[0]}"
        assert meta['original_A_shape'] == list(A.shape)
        assert meta['original_B_shape'] == list(B.shape)
        assert meta['flattened_dim'] == expected_dim

    def test_l2_normalization(self):
        """Verify the output vector has L2 norm of 1 (or 0 if input was 0)."""
        rank = 4
        hidden_size = 8
        A = np.ones((rank, hidden_size))
        B = np.ones((hidden_size, rank))

        weights = {
            'A': A,
            'B': B,
            'id': 'norm_test',
            'task_desc': 'Norm Test'
        }

        vec, _ = flatten_and_normalize(weights)

        norm = np.linalg.norm(vec)
        assert np.isclose(norm, 1.0, atol=1e-5), f"L2 norm should be 1.0, got {norm}"

    def test_zero_vector_handling(self):
        """Verify handling of zero-weight matrices."""
        rank = 4
        hidden_size = 8
        A = np.zeros((rank, hidden_size))
        B = np.zeros((hidden_size, rank))

        weights = {
            'A': A,
            'B': B,
            'id': 'zero_test',
            'task_desc': 'Zero Test'
        }

        vec, meta = flatten_and_normalize(weights)
        norm = np.linalg.norm(vec)
        assert norm == 0.0, "Zero input should result in zero norm"
        assert meta['l2_norm'] == 0.0

    def test_missing_keys(self):
        """Verify ValueError is raised if A or B is missing."""
        weights = {'A': np.random.randn(4, 4)} # Missing B
        with pytest.raises(ValueError, match="Missing required key"):
            flatten_and_normalize(weights)

    def test_non_array_input(self):
        """Verify ValueError is raised if A or B is not a numpy array."""
        weights = {
            'A': [[1, 2], [3, 4]], # List instead of array
            'B': np.random.randn(2, 2)
        }
        with pytest.raises(ValueError, match="must be numpy arrays"):
            flatten_and_normalize(weights)

class TestProcessAllWeights:
    """Tests for the process_all_weights function."""

    def test_process_multiple_files(self):
        """Verify processing of multiple .npz files in a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            output_path = input_dir / "output.npz"

            # Create two mock weight files
            A1 = np.random.randn(4, 8)
            B1 = np.random.randn(8, 4)
            np.savez(input_dir / "file1.npz", A=A1, B=B1, id="task1", task_desc="desc1")

            A2 = np.random.randn(4, 8)
            B2 = np.random.randn(8, 4)
            np.savez(input_dir / "file2.npz", A=A2, B=B2, id="task2", task_desc="desc2")

            stats = process_all_weights(input_dir, output_path)

            assert stats['num_vectors'] == 2
            assert stats['vector_dim'] == (4*8 + 8*4) # 64
            assert output_path.exists()

            # Verify content
            data = np.load(output_path, allow_pickle=True)
            assert data['vectors'].shape == (2, 64)
            assert len(data['metadata']) == 2

    def test_empty_directory(self):
        """Verify ValueError is raised if no .npz files are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            output_path = input_dir / "output.npz"

            with pytest.raises(ValueError, match="No .npz files found"):
                process_all_weights(input_dir, output_path)

    def test_invalid_file_handling(self):
        """Verify invalid files are skipped and valid ones are processed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            output_path = input_dir / "output.npz"

            # Create one valid file
            A = np.random.randn(4, 8)
            B = np.random.randn(8, 4)
            np.savez(input_dir / "valid.npz", A=A, B=B, id="valid", task_desc="desc")

            # Create an invalid file (empty)
            Path(input_dir / "invalid.npz").touch()

            stats = process_all_weights(input_dir, output_path)

            assert stats['num_vectors'] == 1
            assert output_path.exists()