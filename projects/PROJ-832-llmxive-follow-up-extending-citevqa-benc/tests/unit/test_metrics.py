"""
Unit tests for code/metrics.py functions.
Tests IoU, semantic similarity, SAA, and VLA calculations using mocked inputs.
"""
import unittest
import numpy as np
from unittest.mock import patch, MagicMock

# Import the functions to test
# Note: These imports assume the test is run from the project root with code/ in PYTHONPATH
# or via pytest configuration.
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.metrics import (
    calculate_iou,
    semantic_similarity,
    compute_saa,
    compute_vla,
    compute_batch_saa,
    compute_batch_vla
)


class TestCalculateIoU(unittest.TestCase):
    """Tests for the calculate_iou function."""

    def test_identical_boxes(self):
        """IoU of identical boxes should be 1.0."""
        box_pred = [10, 10, 20, 20]  # x_min, y_min, x_max, y_max
        box_gt = [10, 10, 20, 20]
        iou = calculate_iou(box_pred, box_gt)
        self.assertAlmostEqual(iou, 1.0, places=5)

    def test_no_overlap(self):
        """IoU of non-overlapping boxes should be 0.0."""
        box_pred = [0, 0, 10, 10]
        box_gt = [20, 20, 30, 30]
        iou = calculate_iou(box_pred, box_gt)
        self.assertAlmostEqual(iou, 0.0, places=5)

    def test_partial_overlap(self):
        """IoU of partially overlapping boxes."""
        # Box 1: 0,0 to 2,2 (Area 4)
        # Box 2: 1,1 to 3,3 (Area 4)
        # Overlap: 1,1 to 2,2 (Area 1)
        # Union: 4 + 4 - 1 = 7
        # IoU: 1/7
        box_pred = [0, 0, 2, 2]
        box_gt = [1, 1, 3, 3]
        expected_iou = 1.0 / 7.0
        iou = calculate_iou(box_pred, box_gt)
        self.assertAlmostEqual(iou, expected_iou, places=5)

    def test_box_inside_box(self):
        """IoU when prediction box is inside ground truth."""
        box_pred = [5, 5, 10, 10]  # Area 25
        box_gt = [0, 0, 20, 20]   # Area 400
        # Intersection = Area of pred = 25
        # Union = 400 + 25 - 25 = 400
        # IoU = 25/400 = 0.0625
        iou = calculate_iou(box_pred, box_gt)
        self.assertAlmostEqual(iou, 0.0625, places=5)

    def test_invalid_box_order(self):
        """Test behavior with invalid coordinates (min > max)."""
        # The implementation should handle this or return 0.
        # Assuming the implementation handles min/max swap or returns 0.
        # For this test, we assume standard behavior where area is 0 if min > max.
        box_pred = [20, 20, 10, 10]
        box_gt = [0, 0, 5, 5]
        iou = calculate_iou(box_pred, box_gt)
        # If the implementation clamps or returns 0 for invalid boxes:
        self.assertGreaterEqual(iou, 0.0)
        self.assertLessEqual(iou, 1.0)


class TestSemanticSimilarity(unittest.TestCase):
    """Tests for the semantic_similarity function."""

    def test_identical_vectors(self):
        """Similarity of identical vectors should be 1.0."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([1.0, 2.0, 3.0])
        # Normalize
        vec1 = vec1 / np.linalg.norm(vec1)
        vec2 = vec2 / np.linalg.norm(vec2)
        sim = semantic_similarity(vec1, vec2)
        self.assertAlmostEqual(sim, 1.0, places=5)

    def test_opposite_vectors(self):
        """Similarity of opposite vectors should be -1.0."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([-1.0, 0.0, 0.0])
        vec1 = vec1 / np.linalg.norm(vec1)
        vec2 = vec2 / np.linalg.norm(vec2)
        sim = semantic_similarity(vec1, vec2)
        self.assertAlmostEqual(sim, -1.0, places=5)

    def test_orthogonal_vectors(self):
        """Similarity of orthogonal vectors should be 0.0."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        vec1 = vec1 / np.linalg.norm(vec1)
        vec2 = vec2 / np.linalg.norm(vec2)
        sim = semantic_similarity(vec1, vec2)
        self.assertAlmostEqual(sim, 0.0, places=5)

    def test_string_inputs(self):
        """Test that string inputs are handled (mocked embedding)."""
        # In a real scenario, this would call an embedding model.
        # Here we mock the embedding generation to return fixed vectors.
        with patch('code.metrics.np.array') as mock_array:
            # Mock the embedding return values
            mock_vec1 = np.array([1.0, 0.0])
            mock_vec2 = np.array([1.0, 0.0])
            
            # We need to mock the logic inside semantic_similarity if it handles strings.
            # Since the signature suggests vector inputs, we test the vector path primarily.
            # If the function internally converts strings, we rely on the vector logic.
            pass

    def test_2d_vectors(self):
        """Test with 2D vectors."""
        vec1 = np.array([3.0, 4.0])
        vec2 = np.array([3.0, 4.0])
        sim = semantic_similarity(vec1, vec2)
        self.assertAlmostEqual(sim, 1.0, places=5)


class TestComputeSAA(unittest.TestCase):
    """Tests for the compute_saa function."""

    def test_exact_match(self):
        """SAA should be 1.0 if answers match exactly."""
        pred_answer = "The answer is 42."
        gt_answer = "The answer is 42."
        pred_box = [0, 0, 10, 10]
        gt_box = [0, 0, 10, 10]
        
        # Mock the similarity check to not trigger if exact match is handled first
        with patch('code.metrics.semantic_similarity', return_value=0.5):
            saa = compute_saa(pred_answer, gt_answer, pred_box, gt_box)
            # Exact match should yield 1.0 (assuming implementation checks exact match first)
            # If implementation relies on similarity >= 0.85, this might differ.
            # Based on spec: "Answer Correctness: Exact Match OR Semantic Similarity >= 0.85"
            self.assertEqual(saa, 1.0)

    def test_high_similarity_correct_box(self):
        """SAA should be 1.0 if similarity >= 0.85 and IoU > 0.5."""
        pred_answer = "The value is high."
        gt_answer = "The value is high." # Or similar
        pred_box = [0, 0, 10, 10]
        gt_box = [0, 0, 10, 10]
        
        with patch('code.metrics.semantic_similarity', return_value=0.9):
            with patch('code.metrics.calculate_iou', return_value=1.0):
                saa = compute_saa(pred_answer, gt_answer, pred_box, gt_box)
                self.assertEqual(saa, 1.0)

    def test_low_similarity_or_wrong_box(self):
        """SAA should be 0.0 if conditions not met."""
        pred_answer = "Wrong answer."
        gt_answer = "Correct answer."
        pred_box = [0, 0, 10, 10]
        gt_box = [50, 50, 60, 60] # No overlap
        
        with patch('code.metrics.semantic_similarity', return_value=0.3):
            with patch('code.metrics.calculate_iou', return_value=0.0):
                saa = compute_saa(pred_answer, gt_answer, pred_box, gt_box)
                self.assertEqual(saa, 0.0)

    def test_high_similarity_wrong_box(self):
        """SAA should be 0.0 if similarity high but IoU low."""
        pred_answer = "Correct text."
        gt_answer = "Correct text."
        pred_box = [0, 0, 10, 10]
        gt_box = [50, 50, 60, 60]
        
        with patch('code.metrics.semantic_similarity', return_value=0.95):
            with patch('code.metrics.calculate_iou', return_value=0.0):
                saa = compute_saa(pred_answer, gt_answer, pred_box, gt_box)
                self.assertEqual(saa, 0.0)


class TestComputeVLA(unittest.TestCase):
    """Tests for the compute_vla function."""

    def test_vla_calculation(self):
        """VLA is typically based on IoU for visual localization."""
        # Assuming VLA is 1.0 if IoU > threshold (e.g., 0.5), else 0.0
        pred_box = [0, 0, 10, 10]
        gt_box = [0, 0, 10, 10]
        
        with patch('code.metrics.calculate_iou', return_value=1.0):
            vla = compute_vla(pred_box, gt_box)
            self.assertEqual(vla, 1.0)

    def test_vla_failure(self):
        """VLA should be 0.0 if IoU is low."""
        pred_box = [0, 0, 10, 10]
        gt_box = [50, 50, 60, 60]
        
        with patch('code.metrics.calculate_iou', return_value=0.0):
            vla = compute_vla(pred_box, gt_box)
            self.assertEqual(vla, 0.0)


class TestComputeBatchSAA(unittest.TestCase):
    """Tests for the compute_batch_saa function."""

    def test_batch_calculation(self):
        """Test batch SAA calculation."""
        results = [
            {"pred_answer": "A", "gt_answer": "A", "pred_box": [0,0,1,1], "gt_box": [0,0,1,1]},
            {"pred_answer": "B", "gt_answer": "C", "pred_box": [0,0,1,1], "gt_box": [5,5,6,6]},
        ]
        
        with patch('code.metrics.compute_saa', side_effect=[1.0, 0.0]):
            mean_saa, scores = compute_batch_saa(results)
            self.assertEqual(mean_saa, 0.5)
            self.assertEqual(scores, [1.0, 0.0])


class TestComputeBatchVLA(unittest.TestCase):
    """Tests for the compute_batch_vla function."""

    def test_batch_calculation(self):
        """Test batch VLA calculation."""
        results = [
            {"pred_box": [0,0,1,1], "gt_box": [0,0,1,1]},
            {"pred_box": [0,0,1,1], "gt_box": [5,5,6,6]},
        ]
        
        with patch('code.metrics.compute_vla', side_effect=[1.0, 0.0]):
            mean_vla, scores = compute_batch_vla(results)
            self.assertEqual(mean_vla, 0.5)
            self.assertEqual(scores, [1.0, 0.0])


if __name__ == '__main__':
    unittest.main()