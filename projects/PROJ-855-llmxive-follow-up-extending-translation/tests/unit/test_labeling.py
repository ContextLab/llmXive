"""
Unit tests for physics metric logic (tipping angle, slippage, stability labeling).
Validates the implementation in code/utils/physics_metrics.py.
"""
import math
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Add code directory to path to import utils
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from utils.physics_metrics import (
    load_config,
    get_thresholds,
    calculate_tipping_angle,
    calculate_slippage_distance,
    is_stable,
    get_stability_label,
)
import yaml


class TestPhysicsMetrics:
    """Test suite for physics metric calculations and labeling logic."""

    def test_calculate_tipping_angle_zero(self):
        """Tipping angle should be 0 when object is upright (z=1)."""
        # Object upright: quaternion (0, 0, 0, 1) -> z component = 1
        quaternion = (0.0, 0.0, 0.0, 1.0)
        angle = calculate_tipping_angle(quaternion)
        assert math.isclose(angle, 0.0, abs_tol=1e-6)

    def test_calculate_tipping_angle_45_degrees(self):
        """Tipping angle should be ~45 degrees for 45-degree tilt."""
        # Quaternion for 45-degree rotation around X axis
        # q = (sin(θ/2), 0, 0, cos(θ/2)) = (sin(22.5°), 0, 0, cos(22.5°))
        theta = math.radians(45)
        q_x = math.sin(theta / 2)
        q_w = math.cos(theta / 2)
        quaternion = (q_x, 0.0, 0.0, q_w)
        
        angle = calculate_tipping_angle(quaternion)
        assert math.isclose(angle, 45.0, abs_tol=1e-1)

    def test_calculate_tipping_angle_90_degrees(self):
        """Tipping angle should be ~90 degrees for 90-degree tilt."""
        # Quaternion for 90-degree rotation around X axis
        theta = math.radians(90)
        q_x = math.sin(theta / 2)
        q_w = math.cos(theta / 2)
        quaternion = (q_x, 0.0, 0.0, q_w)
        
        angle = calculate_tipping_angle(quaternion)
        assert math.isclose(angle, 90.0, abs_tol=1e-1)

    def test_calculate_slippage_distance_zero(self):
        """Slippage distance should be 0 when start and end positions are identical."""
        start_pos = (1.0, 2.0, 3.0)
        end_pos = (1.0, 2.0, 3.0)
        distance = calculate_slippage_distance(start_pos, end_pos)
        assert math.isclose(distance, 0.0, abs_tol=1e-6)

    def test_calculate_slippage_distance_nonzero(self):
        """Slippage distance should be Euclidean distance between points."""
        start_pos = (0.0, 0.0, 0.0)
        end_pos = (3.0, 4.0, 0.0)
        # Distance = sqrt(3^2 + 4^2) = 5
        distance = calculate_slippage_distance(start_pos, end_pos)
        assert math.isclose(distance, 5.0, abs_tol=1e-6)

    def test_is_stable_below_thresholds(self):
        """Object should be stable when both metrics are below thresholds."""
        # Tipping angle = 10°, slippage = 0.01m
        # Default thresholds: tipping=15°, slippage=0.02m
        quaternion = (0.0, 0.0, 0.0, 1.0)  # Upright
        start_pos = (0.0, 0.0, 0.0)
        end_pos = (0.01, 0.0, 0.0)  # 1cm shift
        
        is_stable_result = is_stable(quaternion, start_pos, end_pos)
        assert is_stable_result is True

    def test_is_stable_above_tipping_threshold(self):
        """Object should be unstable when tipping angle exceeds threshold."""
        # Tipping angle = 20° (above 15° threshold)
        theta = math.radians(20)
        q_x = math.sin(theta / 2)
        q_w = math.cos(theta / 2)
        quaternion = (q_x, 0.0, 0.0, q_w)
        start_pos = (0.0, 0.0, 0.0)
        end_pos = (0.0, 0.0, 0.0)
        
        is_stable_result = is_stable(quaternion, start_pos, end_pos)
        assert is_stable_result is False

    def test_is_stable_above_slippage_threshold(self):
        """Object should be unstable when slippage exceeds threshold."""
        # Tipping angle = 0°, slippage = 0.05m (above 0.02m threshold)
        quaternion = (0.0, 0.0, 0.0, 1.0)
        start_pos = (0.0, 0.0, 0.0)
        end_pos = (0.05, 0.0, 0.0)  # 5cm shift
        
        is_stable_result = is_stable(quaternion, start_pos, end_pos)
        assert is_stable_result is False

    def test_get_stability_label_stable(self):
        """Stable object should return label 1."""
        quaternion = (0.0, 0.0, 0.0, 1.0)
        start_pos = (0.0, 0.0, 0.0)
        end_pos = (0.0, 0.0, 0.0)
        
        label = get_stability_label(quaternion, start_pos, end_pos)
        assert label == 1

    def test_get_stability_label_unstable(self):
        """Unstable object should return label 0."""
        # 20° tilt (above 15° threshold)
        theta = math.radians(20)
        q_x = math.sin(theta / 2)
        q_w = math.cos(theta / 2)
        quaternion = (q_x, 0.0, 0.0, q_w)
        start_pos = (0.0, 0.0, 0.0)
        end_pos = (0.0, 0.0, 0.0)
        
        label = get_stability_label(quaternion, start_pos, end_pos)
        assert label == 0

    def test_get_thresholds_default(self):
        """Default thresholds should be loaded from config.yaml."""
        # Mock the config.yaml content
        mock_config = {
            "physics_metrics": {
                "tipping_angle_threshold": 15.0,
                "slippage_distance_threshold": 0.02
            }
        }
        
        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config))):
            with patch("utils.physics_metrics.Path.exists", return_value=True):
                thresholds = get_thresholds()
                assert thresholds["tipping_angle"] == 15.0
                assert thresholds["slippage_distance"] == 0.02

    def test_get_thresholds_custom(self):
        """Custom thresholds should be loaded from config.yaml."""
        mock_config = {
            "physics_metrics": {
                "tipping_angle_threshold": 20.0,
                "slippage_distance_threshold": 0.05
            }
        }
        
        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config))):
            with patch("utils.physics_metrics.Path.exists", return_value=True):
                thresholds = get_thresholds()
                assert thresholds["tipping_angle"] == 20.0
                assert thresholds["slippage_distance"] == 0.05

    def test_load_config_file_not_found(self):
        """Should return default config when config.yaml is not found."""
        with patch("utils.physics_metrics.Path.exists", return_value=False):
            config = load_config()
            assert "physics_metrics" in config
            assert config["physics_metrics"]["tipping_angle_threshold"] == 15.0
            assert config["physics_metrics"]["slippage_distance_threshold"] == 0.02

    def test_edge_case_just_below_threshold(self):
        """Object with metrics just below threshold should be stable."""
        # Tipping angle = 14.99° (just below 15°)
        theta = math.radians(14.99)
        q_x = math.sin(theta / 2)
        q_w = math.cos(theta / 2)
        quaternion = (q_x, 0.0, 0.0, q_w)
        start_pos = (0.0, 0.0, 0.0)
        end_pos = (0.0, 0.0, 0.0)
        
        is_stable_result = is_stable(quaternion, start_pos, end_pos)
        assert is_stable_result is True

    def test_edge_case_just_above_threshold(self):
        """Object with metrics just above threshold should be unstable."""
        # Tipping angle = 15.01° (just above 15°)
        theta = math.radians(15.01)
        q_x = math.sin(theta / 2)
        q_w = math.cos(theta / 2)
        quaternion = (q_x, 0.0, 0.0, q_w)
        start_pos = (0.0, 0.0, 0.0)
        end_pos = (0.0, 0.0, 0.0)
        
        is_stable_result = is_stable(quaternion, start_pos, end_pos)
        assert is_stable_result is False

    def test_combined_failure(self):
        """Object should be unstable if EITHER metric exceeds threshold."""
        # Tipping angle = 10° (OK), slippage = 0.03m (FAIL)
        quaternion = (0.0, 0.0, 0.0, 1.0)
        start_pos = (0.0, 0.0, 0.0)
        end_pos = (0.03, 0.0, 0.0)
        
        is_stable_result = is_stable(quaternion, start_pos, end_pos)
        assert is_stable_result is False

        # Tipping angle = 20° (FAIL), slippage = 0.01m (OK)
        theta = math.radians(20)
        q_x = math.sin(theta / 2)
        q_w = math.cos(theta / 2)
        quaternion = (q_x, 0.0, 0.0, q_w)
        start_pos = (0.0, 0.0, 0.0)
        end_pos = (0.01, 0.0, 0.0)
        
        is_stable_result = is_stable(quaternion, start_pos, end_pos)
        assert is_stable_result is False