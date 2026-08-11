import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.validation.reconstruction_error import (
    load_npz_file,
    compute_cosine_distance,
    calculate_reconstruction_error,
    save_results,
    main
)

class TestLoadNpzFile:
    def test_load_existing_file(self, tmp_path):
        """Test loading an existing .npz file."""
        test_file = tmp_path / "test.npz"
        data = {"a": np.array([1, 2, 3]), "b": np.array([4, 5, 6])}
        np.savez(str(test_file), **data)
        
        result = load_npz_file(test_file)
        assert "a" in result
        assert "b" in result
        np.testing.assert_array_equal(result["a"], data["a"])
        np.testing.assert_array_equal(result["b"], data["b"])

    def test_load_nonexistent_file(self, tmp_path):
        """Test that loading a non-existent file raises FileNotFoundError."""
        test_file = tmp_path / "nonexistent.npz"
        
        with pytest.raises(FileNotFoundError):
            load_npz_file(test_file)

    def test_load_empty_file(self, tmp_path):
        """Test that loading an empty .npz file raises ValueError."""
        test_file = tmp_path / "empty.npz"
        test_file.touch()
        
        with pytest.raises(ValueError):
            load_npz_file(test_file)

class TestComputeCosineDistance:
    def test_identical_vectors(self):
        """Test cosine distance for identical vectors (should be 0)."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([1.0, 2.0, 3.0])
        
        distance = compute_cosine_distance(vec1, vec2)
        assert np.isclose(distance, 0.0, atol=1e-6)

    def test_opposite_vectors(self):
        """Test cosine distance for opposite vectors (should be 2)."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([-1.0, 0.0, 0.0])
        
        distance = compute_cosine_distance(vec1, vec2)
        assert np.isclose(distance, 2.0, atol=1e-6)

    def test_orthogonal_vectors(self):
        """Test cosine distance for orthogonal vectors (should be 1)."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        
        distance = compute_cosine_distance(vec1, vec2)
        assert np.isclose(distance, 1.0, atol=1e-6)

    def test_different_shapes(self):
        """Test that different shapes raise ValueError."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([1.0, 2.0])
        
        with pytest.raises(ValueError):
            compute_cosine_distance(vec1, vec2)

    def test_zero_vector(self):
        """Test that zero vectors raise ValueError."""
        vec1 = np.array([0.0, 0.0, 0.0])
        vec2 = np.array([1.0, 2.0, 3.0])
        
        with pytest.raises(ValueError):
            compute_cosine_distance(vec1, vec2)

    def test_multidimensional_vectors(self):
        """Test with multi-dimensional arrays."""
        vec1 = np.array([[1.0, 2.0], [3.0, 4.0]])
        vec2 = np.array([[1.0, 2.0], [3.0, 4.0]])
        
        distance = compute_cosine_distance(vec1, vec2)
        assert np.isclose(distance, 0.0, atol=1e-6)

class TestCalculateReconstructionError:
    def test_perfect_reconstruction(self, tmp_path):
        """Test with identical synthesized and ground truth weights."""
        syn_file = tmp_path / "syn.npz"
        gt_file = tmp_path / "gt.npz"
        
        data = {"A": np.random.rand(4096, 1024), "B": np.random.rand(1024, 4096)}
        np.savez(str(syn_file), **data)
        np.savez(str(gt_file), **data)
        
        mean_err, max_err, valid = calculate_reconstruction_error(syn_file, gt_file)
        
        assert np.isclose(mean_err, 0.0, atol=1e-6)
        assert np.isclose(max_err, 0.0, atol=1e-6)
        assert valid is True

    def test_different_weights(self, tmp_path):
        """Test with different synthesized and ground truth weights."""
        syn_file = tmp_path / "syn.npz"
        gt_file = tmp_path / "gt.npz"
        
        data_syn = {"A": np.random.rand(4096, 1024), "B": np.random.rand(1024, 4096)}
        data_gt = {"A": np.random.rand(4096, 1024), "B": np.random.rand(1024, 4096)}
        
        np.savez(str(syn_file), **data_syn)
        np.savez(str(gt_file), **data_gt)
        
        mean_err, max_err, valid = calculate_reconstruction_error(syn_file, gt_file)
        
        assert mean_err >= 0.0
        assert max_err >= 0.0
        # We don't assert valid is True/False as it depends on the random data

    def test_key_mismatch(self, tmp_path):
        """Test that key mismatch raises ValueError."""
        syn_file = tmp_path / "syn.npz"
        gt_file = tmp_path / "gt.npz"
        
        data_syn = {"A": np.random.rand(4096, 1024)}
        data_gt = {"A": np.random.rand(4096, 1024), "B": np.random.rand(1024, 4096)}
        
        np.savez(str(syn_file), **data_syn)
        np.savez(str(gt_file), **data_gt)
        
        with pytest.raises(ValueError):
            calculate_reconstruction_error(syn_file, gt_file)

    def test_invalid_data(self, tmp_path):
        """Test with invalid data (e.g., zero vectors)."""
        syn_file = tmp_path / "syn.npz"
        gt_file = tmp_path / "gt.npz"
        
        # Create zero vector which should raise ValueError in compute_cosine_distance
        data_syn = {"A": np.zeros((4096, 1024))}
        data_gt = {"A": np.ones((4096, 1024))}
        
        np.savez(str(syn_file), **data_syn)
        np.savez(str(gt_file), **data_gt)
        
        with pytest.raises(ValueError):
            calculate_reconstruction_error(syn_file, gt_file)

class TestSaveResults:
    def test_save_results(self, tmp_path):
        """Test saving results to a JSON file."""
        output_file = tmp_path / "results.json"
        
        save_results(
            mean_error=0.02,
            max_error=0.04,
            validity_flag=True,
            output_path=output_file
        )
        
        assert output_file.exists()
        
        import json
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert data["mean_error"] == 0.02
        assert data["max_error"] == 0.04
        assert data["validity_flag"] is True
        assert data["threshold"] == 0.05

class TestMain:
    @patch('src.validation.reconstruction_error.Path.exists')
    @patch('src.validation.reconstruction_error.Path.glob')
    @patch('src.validation.reconstruction_error.load_npz_file')
    @patch('src.validation.reconstruction_error.compute_cosine_distance')
    @patch('src.validation.reconstruction_error.save_results')
    def test_main_execution(
        self,
        mock_save,
        mock_compute,
        mock_load,
        mock_glob,
        mock_exists,
        tmp_path
    ):
        """Test the main function execution flow."""
        # Setup mocks
        mock_exists.return_value = True
        mock_glob.return_value = [tmp_path / "syn1.npz"]
        mock_load.return_value = {"A": np.array([1.0, 2.0]), "B": np.array([3.0, 4.0])}
        mock_compute.return_value = 0.01
        mock_save.return_value = None

        # Change to temp directory for the test
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            main()
            mock_save.assert_called_once()
        finally:
            os.chdir(original_cwd)

    @patch('src.validation.reconstruction_error.Path.exists')
    def test_main_missing_ground_truth(self, mock_exists, tmp_path):
        """Test main when ground truth is missing."""
        mock_exists.return_value = False
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            with pytest.raises(SystemExit):
                main()
        finally:
            os.chdir(original_cwd)

    @patch('src.validation.reconstruction_error.Path.exists')
    @patch('src.validation.reconstruction_error.Path.glob')
    def test_main_no_synthesized_files(self, mock_glob, mock_exists, tmp_path):
        """Test main when no synthesized files are found."""
        mock_exists.return_value = True
        mock_glob.return_value = []
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            with pytest.raises(SystemExit):
                main()
        finally:
            os.chdir(original_cwd)