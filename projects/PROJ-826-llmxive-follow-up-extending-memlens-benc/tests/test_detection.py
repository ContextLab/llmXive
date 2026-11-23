import os
import json
import sys
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.detection import (
    check_ground_truth_exists,
    calculate_iou,
    calculate_recall,
    calculate_recall_statistics
)

class TestCheckGroundTruth:
    def test_has_annotations(self):
        sample = {
            "annotations": [
                {"bbox": [10, 10, 50, 50], "label": "cat"}
            ]
        }
        assert check_ground_truth_exists(sample) is True

    def test_has_gt_boxes(self):
        sample = {
            "gt_boxes": [[10, 10, 50, 50]]
        }
        assert check_ground_truth_exists(sample) is True

    def test_no_annotations(self):
        sample = {
            "annotations": []
        }
        assert check_ground_truth_exists(sample) is False

    def test_empty_sample(self):
        sample = {}
        assert check_ground_truth_exists(sample) is False

class TestCalculateIoU:
    def test_perfect_overlap(self):
        box1 = [0, 0, 10, 10]
        box2 = [0, 0, 10, 10]
        assert calculate_iou(box1, box2) == 1.0

    def test_no_overlap(self):
        box1 = [0, 0, 10, 10]
        box2 = [20, 20, 30, 30]
        assert calculate_iou(box1, box2) == 0.0

    def test_partial_overlap(self):
        box1 = [0, 0, 10, 10]
        box2 = [5, 5, 15, 15]
        # Intersection: 5x5 = 25
        # Union: 100 + 100 - 25 = 175
        # IoU: 25/175 = 0.1428...
        expected = 25 / 175
        assert abs(calculate_iou(box1, box2) - expected) < 1e-5

class TestCalculateRecall:
    def test_simple_recall(self):
        # GT: [A], [B]
        # Det: [A_match]
        gt_boxes = [[0, 0, 10, 10], [20, 20, 30, 30]]
        detections = [
            {"bbox": [0, 0, 10, 10], "confidence": 0.9} # Matches first GT
        ]
        # Recall = TP / (TP + FN) = 1 / (1 + 1) = 0.5
        recall = calculate_recall(detections, gt_boxes, iou_threshold=0.5)
        assert recall == 0.5

    def test_full_recall(self):
        gt_boxes = [[0, 0, 10, 10], [20, 20, 30, 30]]
        detections = [
            {"bbox": [0, 0, 10, 10], "confidence": 0.9},
            {"bbox": [20, 20, 30, 30], "confidence": 0.8}
        ]
        recall = calculate_recall(detections, gt_boxes, iou_threshold=0.5)
        assert recall == 1.0

    def test_zero_recall(self):
        gt_boxes = [[0, 0, 10, 10]]
        detections = [
            {"bbox": [100, 100, 110, 110], "confidence": 0.9}
        ]
        recall = calculate_recall(detections, gt_boxes, iou_threshold=0.5)
        assert recall == 0.0

    def test_no_gt(self):
        gt_boxes = []
        detections = [
            {"bbox": [0, 0, 10, 10], "confidence": 0.9}
        ]
        # Should return 0.0 as per implementation safety
        recall = calculate_recall(detections, gt_boxes, iou_threshold=0.5)
        assert recall == 0.0

class TestCalculateRecallStatistics:
    def test_mixed_results(self):
        results = [
            {"ground_truth_exists": True, "recall": 0.5},
            {"ground_truth_exists": True, "recall": 1.0},
            {"ground_truth_exists": False, "recall": "N/A"},
            {"ground_truth_exists": True, "recall": 0.0}
        ]
        stats = calculate_recall_statistics(results)
        
        assert stats["total_samples"] == 4
        assert stats["samples_with_gt"] == 3
        assert stats["mean_recall"] == (0.5 + 1.0 + 0.0) / 3
        assert stats["status"] == "SUCCESS"

    def test_no_gt_data(self):
        results = [
            {"ground_truth_exists": False, "recall": "N/A"}
        ]
        stats = calculate_recall_statistics(results)
        
        assert stats["samples_with_gt"] == 0
        assert stats["status"] == "NO_GT_DATA"
