"""
Unit tests for IoU calculation (T030).
"""

import os
import sys
import json
import tempfile
from pathlib import Path
import unittest
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from eval.iou_calculator import calculate_iou, calculate_iou_report, generate_expert_review_report


class TestIoUCalculator(unittest.TestCase):
    """Tests for IoU calculation functions."""

    def test_iou_identical_masks(self):
        """Test IoU with identical masks should be 1.0."""
        mask1 = np.ones((10, 10), dtype=np.uint8)
        mask2 = np.ones((10, 10), dtype=np.uint8)

        iou = calculate_iou(mask1, mask2)
        self.assertEqual(iou, 1.0)

    def test_iou_disjoint_masks(self):
        """Test IoU with disjoint masks should be 0.0."""
        mask1 = np.zeros((10, 10), dtype=np.uint8)
        mask1[:5, :] = 1
        mask2 = np.zeros((10, 10), dtype=np.uint8)
        mask2[5:, :] = 1

        iou = calculate_iou(mask1, mask2)
        self.assertEqual(iou, 0.0)

    def test_iou_partial_overlap(self):
        """Test IoU with partial overlap."""
        mask1 = np.zeros((10, 10), dtype=np.uint8)
        mask1[:6, :6] = 1
        mask2 = np.zeros((10, 10), dtype=np.uint8)
        mask2[4:, 4:] = 1

        # Intersection: 2x2 = 4
        # Union: 6x6 + 6x6 - 4 = 36 + 36 - 4 = 68
        # IoU = 4 / 68 = 0.0588...
        iou = calculate_iou(mask1, mask2)
        self.assertGreater(iou, 0.0)
        self.assertLess(iou, 0.1)

    def test_iou_empty_union(self):
        """Test IoU when union is empty should return 0.0."""
        mask1 = np.zeros((10, 10), dtype=np.uint8)
        mask2 = np.zeros((10, 10), dtype=np.uint8)

        iou = calculate_iou(mask1, mask2)
        self.assertEqual(iou, 0.0)

    def test_calculate_iou_report_no_annotations(self):
        """Test report generation when no annotations available."""
        image_ids = ["img1", "img2"]
        report = calculate_iou_report(image_ids, None, {}, threshold=0.4)

        self.assertEqual(report["status"], "no_annotations")
        self.assertIn("message", report)

    def test_calculate_iou_report_with_data(self):
        """Test report generation with valid data."""
        image_ids = ["img1"]
        annotations = {
            "img1": np.ones((10, 10), dtype=np.uint8)
        }
        heatmaps = {
            "img1": np.ones((10, 10), dtype=np.float32)
        }

        report = calculate_iou_report(image_ids, annotations, heatmaps, threshold=0.4)

        self.assertEqual(report["status"], "completed")
        self.assertIn("summary", report)
        self.assertIn("mean_iou", report["summary"])
        self.assertGreaterEqual(report["summary"]["mean_iou"], 0.0)
        self.assertLessEqual(report["summary"]["mean_iou"], 1.0)

    def test_expert_review_report(self):
        """Test expert review report generation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            report = generate_expert_review_report(
                ["img1", "img2"],
                annotations_available=False,
                heatmaps_available=True,
                output_path=output_path
            )

            self.assertEqual(report["status"], "expert_review_required")
            self.assertFalse(report["annotations_available"])
            self.assertTrue(report["heatmaps_available"])

            # Verify file was written
            self.assertTrue(output_path.exists())

            with open(output_path, 'r') as f:
                saved_report = json.load(f)

            self.assertEqual(saved_report["status"], "expert_review_required")
        finally:
            output_path.unlink()


if __name__ == "__main__":
    unittest.main()