"""
Unit tests for src/validation/reconstruction_error.py
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from src.validation.reconstruction_error import (
    calculate_cosine_distance,
    flatten_weights,
    load_lora_weights,
    run_reconstruction_error_analysis
)


class TestLoadAndFlatten:
    def test_load_lora_weights(self, tmp_path):
        """Test loading a mock .npz file."""
        test_file = tmp_path / "test.npz"
        mock_data = {"layer_A": np.array([[1.0, 2.0], [3.0, 4.0]]), "layer_B": np.array([[0.5], [0.5]])}
        np.savez(test_file, **mock_data)

        loaded = load_lora_weights(test_file)

        assert "layer_A" in loaded
        assert "layer_B" in loaded
        assert np.array_equal(loaded["layer_A"], mock_data["layer_A"])
        assert np.array_equal(loaded["layer_B"], mock_data["layer_B"])

    def test_load_lora_weights_not_found(self, tmp_path):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_lora_weights(tmp_path / "nonexistent.npz")

    def test_flatten_weights(self):
        """Test flattening logic."""
        weights = {
            "layer1_A": np.array([[1.0, 2.0]]),
            "layer1_B": np.array([[3.0]]),
            "layer2_A": np.array([[4.0, 5.0, 6.0]])
        }
        # Sorted keys: layer1_A, layer1_B, layer2_A
        # Values: [1, 2], [3], [4, 5, 6] -> [1, 2, 3, 4, 5, 6]
        expected = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        result = flatten_weights(weights)
        assert np.array_equal(result, expected)


class TestCosineDistance:
    def test_identical_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([1.0, 0.0, 0.0])
        assert calculate_cosine_distance(v1, v2) == 0.0

    def test_opposite_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([-1.0, 0.0, 0.0])
        assert np.isclose(calculate_cosine_distance(v1, v2), 2.0)

    def test_orthogonal_vectors(self):
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        assert np.isclose(calculate_cosine_distance(v1, v2), 1.0)

    def test_zero_vector(self):
        v1 = np.array([0.0, 0.0, 0.0])
        v2 = np.array([1.0, 2.0, 3.0])
        assert calculate_cosine_distance(v1, v2) == 1.0


class TestRunReconstructionAnalysis:
    @patch("src.validation.reconstruction_error.PROJECT_ROOT")
    @patch("src.validation.reconstruction_error.SYNTHESIZED_DIR")
    @patch("src.validation.reconstruction_error.TRUE_WEIGHTS_DIR")
    def test_run_analysis_creates_json(self, mock_true_dir, mock_syn_dir, mock_root, tmp_path):
        """Test that the main function creates the output JSON file."""
        # Setup mock paths
        mock_root.return_value = tmp_path
        mock_syn_dir.return_value = tmp_path / "artifacts" / "synthesized_adapters"
        mock_true_dir.return_value = tmp_path / "artifacts" / "true_weights"

        mock_syn_dir.return_value.mkdir(parents=True)
        mock_true_dir.return_value.mkdir(parents=True)
        output_dir = tmp_path / "data" / "results"
        output_dir.mkdir(parents=True)

        # Create mock files
        syn_file = mock_syn_dir.return_value / "task1_synthesized.npz"
        true_file = mock_true_dir.return_value / "task1_true.npz"

        np.savez(syn_file, layer_A=np.array([1.0, 1.0]), layer_B=np.array([1.0, 1.0]))
        np.savez(true_file, layer_A=np.array([1.0, 1.0]), layer_B=np.array([1.0, 1.0]))

        # Run
        run_reconstruction_error_analysis()

        # Verify output
        output_file = tmp_path / "data" / "results" / "reconstruction_error.json"
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert data["status"] == "completed"
        assert len(data["results"]) == 1
        assert data["results"][0]["task_id"] == "task1"
        assert np.isclose(data["results"][0]["reconstruction_error_cosine_distance"], 0.0)
