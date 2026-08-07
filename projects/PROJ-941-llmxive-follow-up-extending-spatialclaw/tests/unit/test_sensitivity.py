"""
tests/unit/test_sensitivity.py

Unit tests for code/stats/sensitivity.py
"""
import pytest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import numpy as np

# Import the module under test
# Note: We need to ensure the path is set up correctly for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from stats.sensitivity import classify_failure, run_sensitivity_analysis

class TestClassifyFailure:
    def test_flat_object_failure(self):
        """Test that a failure on a flat object is classified as projection_loss."""
        task_id = "test_001"
        result_2d = {"success": False}
        gt_3d = {
            "ground_truth_3d_params": {
                "depth_variance": 0.0001, # Near zero
                "gt_3d_is_occluded": True
            }
        }
        
        classification = classify_failure(task_id, result_2d, gt_3d)
        assert classification == "projection_loss"

    def test_non_flat_object_failure(self):
        """Test that a failure on a non-flat object is classified as action_restriction."""
        task_id = "test_002"
        result_2d = {"success": False}
        gt_3d = {
            "ground_truth_3d_params": {
                "depth_variance": 2.5, # Significant variance
                "gt_3d_is_occluded": True,
                "task_type": "occlusion"
            }
        }
        
        classification = classify_failure(task_id, result_2d, gt_3d)
        assert classification == "action_restriction"

    def test_success_classification(self):
        """Test that a success is classified as success."""
        task_id = "test_003"
        result_2d = {"success": True}
        gt_3d = {
            "ground_truth_3d_params": {
                "depth_variance": 1.0
            }
        }
        
        classification = classify_failure(task_id, result_2d, gt_3d)
        assert classification == "success"

class TestRunSensitivityAnalysis:
    @patch('stats.sensitivity.load_dataset')
    @patch('stats.sensitivity.load_comparison_results')
    def test_sensitivity_calculation(self, mock_load_comp, mock_load_ds):
        """Test that sensitivity analysis calculates FP/FN rates correctly."""
        # Mock data
        mock_dataset = {
            "tasks": [
                {
                    "task_id": "t1",
                    "task_type": "occlusion",
                    "ground_truth_3d_params": {"gt_3d_is_occluded": True, "depth_variance": 2.0},
                    "seed": 1
                },
                {
                    "task_id": "t2",
                    "task_type": "occlusion",
                    "ground_truth_3d_params": {"gt_3d_is_occluded": False, "depth_variance": 1.0},
                    "seed": 2
                }
            ]
        }
        mock_load_ds.return_value = mock_dataset

        # Mock 2D results: t1 says not occluded (FN), t2 says occluded (FP)
        # We assume the 2D result has a 'predicted_depth_diff' for the logic to work
        mock_two_d = [
            {"task_id": "t1", "success": False, "predicted_depth_diff": 0.5}, # < threshold (say 1.0) -> not occluded
            {"task_id": "t2", "success": False, "predicted_depth_diff": 1.5}  # > threshold -> occluded
        ]
        mock_baseline = []
        mock_load_comp.return_value = (mock_two_d, mock_baseline)

        # Run analysis with threshold 1.0
        results = run_sensitivity_analysis(thresholds=[1.0])
        
        assert len(results) == 1
        res = results[0]
        assert res['threshold_value'] == 1.0
        # t1: GT True, 2D False (0.5 < 1.0) -> FN
        # t2: GT False, 2D True (1.5 > 1.0) -> FP
        # FP Rate = 1/2 = 0.5, FN Rate = 1/2 = 0.5
        assert abs(res['false_positive_rate'] - 0.5) < 1e-6
        assert abs(res['false_negative_rate'] - 0.5) < 1e-6
