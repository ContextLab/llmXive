"""
Unit tests for src/validation/reconstruction_error.py
"""

import os
import sys
import tempfile
import json
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.validation.reconstruction_error import (
    load_npz_safe,
    cosine_distance,
    calculate_reconstruction_errors,
    save_results
)


class TestLoadNpzSafe:
    def test_load_valid_npz(self, tmp_path):
        # Create a valid npz file
        data = {"A": np.array([1, 2, 3]), "B": np.array([4, 5, 6])}
        np.savez(tmp_path / "test.npz", **data)

        result = load_npz_safe(tmp_path / "test.npz")
        assert result is not None
        assert "A" in result
        assert np.array_equal(result["A"], data["A"])

    def test_load_missing_file(self, tmp_path):
        result = load_npz_safe(tmp_path / "nonexistent.npz")
        assert result is None

    def test_load_corrupted_file(self, tmp_path):
        # Write garbage
        with open(tmp_path / "bad.npz", "wb") as f:
            f.write(b"not a npz file")

        result = load_npz_safe(tmp_path / "bad.npz")
        assert result is None


class TestCosineDistance:
    def test_identical_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        dist = cosine_distance(v1, v2)
        assert np.isclose(dist, 0.0)

    def test_opposite_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([-1.0, 0.0, 0.0])
        dist = cosine_distance(v1, v2)
        assert np.isclose(dist, 2.0)

    def test_orthogonal_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        dist = cosine_distance(v1, v2)
        assert np.isclose(dist, 1.0)

    def test_zero_vector(self):
        v1 = np.array([0.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        dist = cosine_distance(v1, v2)
        assert np.isclose(dist, 2.0)  # Should return max distance

    def test_nan_vector(self):
        v1 = np.array([1.0, np.nan, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        dist = cosine_distance(v1, v2)
        assert np.isclose(dist, 2.0)  # Should return max distance


class TestCalculateReconstructionErrors:
    def test_perfect_match(self):
        syn = {"A": np.array([1.0, 2.0, 3.0])}
        gt = {"A": np.array([1.0, 2.0, 3.0])}
        mean_err, max_err, details = calculate_reconstruction_errors(syn, gt)
        assert np.isclose(mean_err, 0.0)
        assert np.isclose(max_err, 0.0)
        assert len(details) == 1

    def test_partial_match(self):
        # 90 degree angle -> distance 1.0
        syn = {"A": np.array([1.0, 0.0])}
        gt = {"A": np.array([0.0, 1.0])}
        mean_err, max_err, details = calculate_reconstruction_errors(syn, gt)
        assert np.isclose(mean_err, 1.0)
        assert np.isclose(max_err, 1.0)

    def test_multiple_matrices(self):
        syn = {
            "A": np.array([1.0, 0.0]),
            "B": np.array([1.0, 0.0])
        }
        gt = {
            "A": np.array([0.0, 1.0]),
            "B": np.array([1.0, 0.0])
        }
        mean_err, max_err, details = calculate_reconstruction_errors(syn, gt)
        # A: 1.0, B: 0.0 -> mean 0.5, max 1.0
        assert np.isclose(mean_err, 0.5)
        assert np.isclose(max_err, 1.0)

    def test_shape_mismatch(self):
        syn = {"A": np.array([1.0, 2.0])}
        gt = {"A": np.array([1.0, 2.0, 3.0])}
        with pytest.raises(ValueError):
            calculate_reconstruction_errors(syn, gt)

    def test_no_common_keys(self):
        syn = {"A": np.array([1.0])}
        gt = {"B": np.array([1.0])}
        with pytest.raises(ValueError):
            calculate_reconstruction_errors(syn, gt)


class TestSaveResults:
    def test_save_creates_file(self, tmp_path):
        output_path = tmp_path / "results" / "reconstruction_error.json"
        details = [{"matrix": "A", "cosine_distance": 0.5}]
        save_results(0.5, 0.5, details, 0.1, output_path)

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
            assert data["results"]["mean_cosine_distance"] == 0.5
            assert data["status"] == "WARNING"

    def test_save_flagged_status(self, tmp_path):
        output_path = tmp_path / "results" / "reconstruction_error.json"
        details = [{"matrix": "A", "cosine_distance": 0.9}]
        save_results(0.9, 0.9, details, 0.1, output_path)

        with open(output_path) as f:
            data = json.load(f)
            assert data["status"] == "WARNING"

    def test_save_ok_status(self, tmp_path):
        output_path = tmp_path / "results" / "reconstruction_error.json"
        details = [{"matrix": "A", "cosine_distance": 0.05}]
        save_results(0.05, 0.05, details, 0.1, output_path)

        with open(output_path) as f:
            data = json.load(f)
            assert data["status"] == "OK"