"""
Unit tests for src/validation/reconstruction_error.py (Task T022d)
"""

import os
import sys
import tempfile
import json
import numpy as np
import pytest
from pathlib import Path

# Add src to path if running from root
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from src.validation.reconstruction_error import (
    calculate_cosine_distance,
    load_npz_safe,
    compute_reconstruction_error
)


class TestCosineDistance:
    def test_identical_vectors(self):
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([1.0, 2.0, 3.0])
        dist = calculate_cosine_distance(v1, v2)
        assert np.isclose(dist, 0.0)

    def test_opposite_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([-1.0, 0.0, 0.0])
        dist = calculate_cosine_distance(v1, v2)
        assert np.isclose(dist, 2.0)

    def test_orthogonal_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        dist = calculate_cosine_distance(v1, v2)
        assert np.isclose(dist, 1.0)

    def test_shape_mismatch(self):
        v1 = np.array([1.0, 2.0])
        v2 = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            calculate_cosine_distance(v1, v2)

    def test_zero_norm(self):
        v1 = np.array([0.0, 0.0])
        v2 = np.array([1.0, 1.0])
        dist = calculate_cosine_distance(v1, v2)
        assert dist == 1.0


class TestLoadNpzSafe:
    def test_load_valid_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.npz"
            np.savez(path, A=np.array([1, 2]), B=np.array([3, 4]))
            data = load_npz_safe(path)
            assert "A" in data
            assert "B" in data
            assert np.array_equal(data["A"], [1, 2])

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_npz_safe(Path("/nonexistent/path/file.npz"))


class TestComputeReconstructionError:
    def test_full_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create mock synthesized data
            syn_path = tmp_path / "syn.npz"
            # Create A and B matrices
            A_syn = np.random.randn(10, 10).astype(np.float32)
            B_syn = np.random.randn(10, 10).astype(np.float32)
            np.savez(syn_path, A=A_syn, B=B_syn)

            # Create mock ground truth (slightly perturbed)
            gt_path = tmp_path / "gt.npz"
            A_gt = A_syn + np.random.randn(10, 10) * 0.1
            B_gt = B_syn + np.random.randn(10, 10) * 0.1
            np.savez(gt_path, A=A_gt, B=B_gt)

            # Run computation
            result = compute_reconstruction_error(syn_path, gt_path)

            assert "reconstruction_error" in result
            assert 0.0 <= result["reconstruction_error"] <= 2.0
            assert "metric" in result
            assert result["metric"] == "cosine_distance"