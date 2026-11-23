"""
Unit tests for reconstruction_error.py (T022d)
"""

import os
import sys
import tempfile
import json
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.validation.reconstruction_error import (
    cosine_distance,
    load_npz_safe,
    calculate_reconstruction_errors,
    save_results,
    main
)

class TestCosineDistance:
    """Tests for cosine_distance function."""

    def test_identical_vectors(self):
        """Distance between identical vectors should be 0."""
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([1.0, 2.0, 3.0])
        assert cosine_distance(v1, v2) == 0.0

    def test_opposite_vectors(self):
        """Distance between opposite vectors should be 2.0."""
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([-1.0, 0.0, 0.0])
        assert abs(cosine_distance(v1, v2) - 2.0) < 1e-6

    def test_orthogonal_vectors(self):
        """Distance between orthogonal vectors should be 1.0."""
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        assert abs(cosine_distance(v1, v2) - 1.0) < 1e-6

    def test_zero_vector(self):
        """Distance involving zero vector should be 1.0."""
        v1 = np.array([0.0, 0.0, 0.0])
        v2 = np.array([1.0, 2.0, 3.0])
        assert cosine_distance(v1, v2) == 1.0

    def test_multidimensional(self):
        """Test with higher dimensional vectors."""
        v1 = np.random.rand(100)
        v2 = v1.copy()
        assert cosine_distance(v1, v2) == 0.0

class TestLoadNpzSafe:
    """Tests for load_npz_safe function."""

    def test_load_valid_file(self):
        """Should load a valid npz file."""
        with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as f:
            temp_path = Path(f.name)
            np.savez(temp_path, a=np.array([1, 2, 3]), b=np.array([4, 5]))
        
        try:
            data = load_npz_safe(temp_path)
            assert 'a' in data
            assert 'b' in data
            np.testing.assert_array_equal(data['a'], [1, 2, 3])
        finally:
            temp_path.unlink()

    def test_missing_file(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_npz_safe(Path("/nonexistent/file.npz"))

class TestCalculateReconstructionErrors:
    """Tests for calculate_reconstruction_errors function."""

    def test_perfect_match(self):
        """Error should be 0 for identical weights."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create identical synthesized and ground truth
            syn_data = {'A': np.ones((10, 10)), 'B': np.ones((10, 10))}
            gt_data = {'A': np.ones((10, 10)), 'B': np.ones((10, 10))}
            
            syn_path = tmp_path / "syn.npz"
            gt_path = tmp_path / "gt.npz"
            
            np.savez(syn_path, **syn_data)
            np.savez(gt_path, **gt_data)
            
            mean_err, max_err, indiv_errs = calculate_reconstruction_errors(syn_path, gt_path)
            
            assert mean_err == 0.0
            assert max_err == 0.0
            assert len(indiv_errs) == 2

    def test_different_weights(self):
        """Should calculate non-zero error for different weights."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            np.random.seed(42)
            syn_data = {'A': np.random.rand(5, 5), 'B': np.random.rand(5, 5)}
            gt_data = {'A': np.random.rand(5, 5), 'B': np.random.rand(5, 5)}
            
            syn_path = tmp_path / "syn.npz"
            gt_path = tmp_path / "gt.npz"
            
            np.savez(syn_path, **syn_data)
            np.savez(gt_path, **gt_data)
            
            mean_err, max_err, indiv_errs = calculate_reconstruction_errors(syn_path, gt_path)
            
            assert mean_err > 0
            assert max_err > 0
            assert len(indiv_errs) == 2

    def test_shape_mismatch(self):
        """Should raise ValueError for shape mismatch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            syn_data = {'A': np.ones((10, 10))}
            gt_data = {'A': np.ones((5, 5))}
            
            syn_path = tmp_path / "syn.npz"
            gt_path = tmp_path / "gt.npz"
            
            np.savez(syn_path, **syn_data)
            np.savez(gt_path, **gt_data)
            
            with pytest.raises(ValueError, match="Shape mismatch"):
                calculate_reconstruction_errors(syn_path, gt_path)

    def test_key_mismatch(self):
        """Should raise ValueError for key mismatch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            syn_data = {'A': np.ones((10, 10))}
            gt_data = {'B': np.ones((10, 10))}
            
            syn_path = tmp_path / "syn.npz"
            gt_path = tmp_path / "gt.npz"
            
            np.savez(syn_path, **syn_data)
            np.savez(gt_path, **gt_data)
            
            with pytest.raises(ValueError, match="Key mismatch"):
                calculate_reconstruction_errors(syn_path, gt_path)

class TestSaveResults:
    """Tests for save_results function."""

    def test_save_valid_json(self):
        """Should save valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            output_path = tmp_path / "results.json"
            
            errors = [0.1, 0.2, 0.3]
            save_results(
                output_path,
                mean_error=0.2,
                max_error=0.3,
                individual_errors=errors,
                validity_flag=True,
                metadata={"test": "value"}
            )
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data['mean_error'] == 0.2
            assert data['max_error'] == 0.3
            assert data['validity_flag'] == True
            assert data['metadata']['test'] == 'value'

class TestMain:
    """Tests for main function."""

    @patch('src.validation.reconstruction_error.get_project_paths')
    @patch('src.validation.reconstruction_error.load_npz_safe')
    @patch('pathlib.Path.exists')
    def test_main_missing_ground_truth(self, mock_exists, mock_load, mock_paths):
        """Should raise FileNotFoundError if ground truth missing."""
        mock_paths.return_value = {
            "data_processed": Path("/fake/processed"),
            "artifacts": Path("/fake/artifacts"),
            "data_results": Path("/fake/results")
        }
        mock_exists.return_value = False  # ground_truth_path doesn't exist
        
        with pytest.raises(FileNotFoundError, match="Ground truth file not found"):
            main()