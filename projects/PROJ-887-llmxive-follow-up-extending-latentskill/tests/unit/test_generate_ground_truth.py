import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Add src to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.validation.generate_ground_truth import (
    generate_composite_weights,
    save_ground_truth,
    load_skill_index
)

class TestGenerateGroundTruth:
    def test_generate_composite_weights_formula(self):
        """Verify the interpolation formula: W_syn = alpha * W_A + (1-alpha) * W_B"""
        # Create mock vectors
        vec_a = np.array([1.0, 2.0, 3.0])
        vec_b = np.array([4.0, 5.0, 6.0])
        
        vector_dict = {
            "task_a": vec_a,
            "task_b": vec_b
        }
        
        alpha = 0.5
        name, result = generate_composite_weights(vector_dict, ("task_a", "task_b"), alpha)
        
        expected = (alpha * vec_a) + ((1.0 - alpha) * vec_b)
        
        assert name == "composite_task_a__task_b_alpha0.5"
        np.testing.assert_array_almost_equal(result, expected)

    def test_generate_composite_weights_alpha_0(self):
        """Test with alpha=0, should return W_B"""
        vec_a = np.array([1.0, 1.0])
        vec_b = np.array([2.0, 2.0])
        vector_dict = {"task_a": vec_a, "task_b": vec_b}
        
        name, result = generate_composite_weights(vector_dict, ("task_a", "task_b"), alpha=0.0)
        np.testing.assert_array_almost_equal(result, vec_b)

    def test_generate_composite_weights_alpha_1(self):
        """Test with alpha=1, should return W_A"""
        vec_a = np.array([1.0, 1.0])
        vec_b = np.array([2.0, 2.0])
        vector_dict = {"task_a": vec_a, "task_b": vec_b}
        
        name, result = generate_composite_weights(vector_dict, ("task_a", "task_b"), alpha=1.0)
        np.testing.assert_array_almost_equal(result, vec_a)

    def test_generate_composite_weights_dimension_mismatch(self):
        """Test that dimension mismatch raises ValueError"""
        vec_a = np.array([1.0, 2.0, 3.0])
        vec_b = np.array([1.0, 2.0]) # Different size
        vector_dict = {"task_a": vec_a, "task_b": vec_b}
        
        with pytest.raises(ValueError, match="Dimension mismatch"):
            generate_composite_weights(vector_dict, ("task_a", "task_b"), alpha=0.5)

    def test_generate_composite_weights_missing_task(self):
        """Test that missing task raises ValueError"""
        vec_a = np.array([1.0, 2.0])
        vector_dict = {"task_a": vec_a}
        
        with pytest.raises(ValueError, match="not found in skill index"):
            generate_composite_weights(vector_dict, ("task_a", "non_existent"), alpha=0.5)

    def test_save_ground_truth(self):
        """Test saving ground truth to a temporary file"""
        results = {
            "comp_1": np.array([0.5, 0.5, 0.5]),
            "comp_2": np.array([0.1, 0.2, 0.3])
        }
        metadata = {"test": True}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_ground_truth.npz")
            save_ground_truth(results, output_path, metadata)
            
            assert os.path.exists(output_path)
            
            # Verify contents
            data = np.load(output_path, allow_pickle=True)
            assert "comp_1" in data.files
            assert "comp_2" in data.files
            assert "metadata" in data.files
            
            np.testing.assert_array_almost_equal(data["comp_1"], results["comp_1"])
            np.testing.assert_array_almost_equal(data["comp_2"], results["comp_2"])
            assert data["metadata"].item() == metadata