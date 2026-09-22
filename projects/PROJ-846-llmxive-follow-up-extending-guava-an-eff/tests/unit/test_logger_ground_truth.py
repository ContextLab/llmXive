"""
Unit tests for the logger.py module, specifically log_perception_ground_truth.

Tests verify that object_missing_if_visible is correctly derived from
comparing YOLO output against ground truth annotations.
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from datetime import datetime

# Import the function to test
# We need to mock the project paths and dependencies
from utils.logger import log_perception_ground_truth, _compare_detection_to_ground_truth
from utils.exceptions import DatasetUnavailableError, GroundTruthSchemaMissingError


class TestCompareDetectionToGroundTruth:
    """Tests for the internal comparison logic."""

    def test_all_detected_correctly(self):
        """When detections match GT perfectly, flag should be False."""
        detected = [
            {"class": "cup", "bbox": [10, 10, 50, 50], "centroid": [30, 30], "color_hist": [0.1]},
            {"class": "bottle", "bbox": [60, 60, 90, 90], "centroid": [75, 75], "color_hist": [0.2]}
        ]
        confs = [0.9, 0.8]
        
        gt_data = {
            "trajectories": {
                "traj_001": {
                    "frames": [
                        {
                            "objects": [
                                {"class": "cup", "bbox": [10, 10, 50, 50]},
                                {"class": "bottle", "bbox": [60, 60, 90, 90]}
                            ]
                        }
                    ]
                }
            }
        }
        
        _, missing = _compare_detection_to_ground_truth(
            detected, confs, "traj_001", 0, gt_data
        )
        assert missing is False

    def test_missing_visible_object(self):
        """When a GT object is present but not detected, flag should be True."""
        detected = [
            {"class": "cup", "bbox": [10, 10, 50, 50], "centroid": [30, 30], "color_hist": [0.1]}
        ]
        confs = [0.9]
        
        gt_data = {
            "trajectories": {
                "traj_001": {
                    "frames": [
                        {
                            "objects": [
                                {"class": "cup", "bbox": [10, 10, 50, 50]},
                                {"class": "bottle", "bbox": [60, 60, 90, 90]} # Not detected
                            ]
                        }
                    ]
                }
            }
        }
        
        _, missing = _compare_detection_to_ground_truth(
            detected, confs, "traj_001", 0, gt_data
        )
        assert missing is True

    def test_occluded_object_ignored(self):
        """If the missed object is marked occluded, flag should be False."""
        detected = [
            {"class": "cup", "bbox": [10, 10, 50, 50], "centroid": [30, 30], "color_hist": [0.1]}
        ]
        confs = [0.9]
        
        gt_data = {
            "trajectories": {
                "traj_001": {
                    "frames": [
                        {
                            "objects": [
                                {"class": "cup", "bbox": [10, 10, 50, 50]},
                                {"class": "bottle", "bbox": [60, 60, 90, 90], "occluded": True} # Missed but occluded
                            ]
                        }
                    ]
                }
            }
        }
        
        _, missing = _compare_detection_to_ground_truth(
            detected, confs, "traj_001", 0, gt_data
        )
        assert missing is False

    def test_no_ground_truth_for_frame(self):
        """If no GT exists for the frame, flag should be False."""
        detected = [
            {"class": "cup", "bbox": [10, 10, 50, 50], "centroid": [30, 30], "color_hist": [0.1]}
        ]
        confs = [0.9]
        
        gt_data = {
            "trajectories": {
                "traj_001": {
                    "frames": [{}] # Empty frame
                }
            }
        }
        
        _, missing = _compare_detection_to_ground_truth(
            detected, confs, "traj_001", 0, gt_data
        )
        assert missing is False


class TestLogPerceptionGroundTruth:
    """Tests for the main logging function."""

    @patch('utils.logger.Path')
    @patch('utils.logger.open', new_callable=mock_open)
    @patch('utils.logger.get_path', return_value="data/artifacts/perception_log.json")
    def test_writes_correct_schema(self, mock_get_path, mock_open_file, mock_path):
        """Verify the output JSON schema matches requirements."""
        # Setup mock for ground truth
        mock_gt_data = {
            "trajectories": {
                "traj_001": {
                    "frames": [
                        {"objects": [{"class": "cup", "bbox": [10, 10, 50, 50]}]}
                    ]
                }
            }
        }
        
        with patch('builtins.open', side_effect=[
            mock_open(read_data=json.dumps(mock_gt_data))(), # Read GT
            mock_open()() # Write Log
        ]):
            detected = [
                {"class": "cup", "bbox": [10, 10, 50, 50], "centroid": [30, 30], "color_hist": [0.1]}
            ]
            confs = [0.9]
            
            result = log_perception_ground_truth(
                "traj_001", 0, detected, confs, append_mode=False
            )
            
            # Check schema keys
            assert "timestamp" in result
            assert "trajectory_id" in result
            assert "frame_id" in result
            assert "detected_objects" in result
            assert "confidence_scores" in result
            assert "object_missing_if_visible" in result
            
            # Check types
            assert isinstance(result["timestamp"], float)
            assert isinstance(result["object_missing_if_visible"], bool)
            assert isinstance(result["detected_objects"], list)
            assert isinstance(result["confidence_scores"], list)

    @patch('utils.logger.Path')
    @patch('utils.logger.get_path', return_value="data/artifacts/perception_log.json")
    def test_raises_on_missing_gt_file(self, mock_get_path, mock_path):
        """Ensure DatasetUnavailableError is raised if GT file is missing."""
        mock_path.exists.return_value = False
        
        detected = [{"class": "cup", "bbox": [10, 10, 50, 50], "centroid": [30, 30], "color_hist": [0.1]}]
        confs = [0.9]
        
        with pytest.raises(DatasetUnavailableError):
            log_perception_ground_truth("traj_001", 0, detected, confs, append_mode=False)

    @patch('utils.logger.Path')
    @patch('utils.logger.get_path', return_value="data/artifacts/perception_log.json")
    def test_raises_on_invalid_gt_schema(self, mock_get_path, mock_path):
        """Ensure GroundTruthSchemaMissingError is raised if GT schema is wrong."""
        mock_path.exists.return_value = True
        mock_path.open.return_value.__enter__.return_value.read.return_value = json.dumps({"invalid": "data"})
        
        detected = [{"class": "cup", "bbox": [10, 10, 50, 50], "centroid": [30, 30], "color_hist": [0.1]}]
        confs = [0.9]
        
        with pytest.raises(GroundTruthSchemaMissingError):
            log_perception_ground_truth("traj_001", 0, detected, confs, append_mode=False)