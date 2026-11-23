import pytest
import math
import sys
import os

# Ensure code/ is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.physics_metrics import (
    calculate_tipping_angle,
    calculate_slippage_distance,
    is_stable,
    get_stability_label,
    load_config,
    get_thresholds
)


class TestStabilityLabelingLogic:
    """Unit tests for stability labeling logic (tipping/slippage thresholds)."""

    def test_tipping_angle_calculation(self):
        """Verify tipping angle calculation matches geometric definition."""
        # tan(theta) = displacement / height
        # theta = arctan(displacement / height)
        disp = 0.1
        height = 0.5
        angle_deg = calculate_tipping_angle(disp, height)
        expected_rad = math.atan(disp / height)
        expected_deg = math.degrees(expected_rad)
        assert abs(angle_deg - expected_deg) < 1e-5

    def test_slippage_distance_calculation(self):
        """Verify slippage distance is Euclidean norm of displacement."""
        dx = 0.03
        dy = 0.04
        dist = calculate_slippage_distance(dx, dy)
        expected = math.sqrt(dx**2 + dy**2)
        assert abs(dist - expected) < 1e-5

    def test_stability_threshold_loading(self):
        """Verify thresholds are correctly loaded from config."""
        # Assuming default config has tipping_threshold=10.0 and slippage_threshold=0.1
        # This test validates the logic path, not specific values (which are config-driven)
        thresholds = get_thresholds()
        assert "tipping_threshold" in thresholds
        assert "slippage_threshold" in thresholds
        assert isinstance(thresholds["tipping_threshold"], (int, float))
        assert isinstance(thresholds["slippage_threshold"], (int, float))

    def test_is_stable_logic(self):
        """Verify is_stable returns True only when both metrics are within thresholds."""
        # Using standard thresholds from config as defaults
        tipping_thresh = 10.0
        slippage_thresh = 0.1

        # Both within
        assert is_stable(5.0, 0.05, tipping_thresh, slippage_thresh) is True

        # Tipping exceeds
        assert is_stable(15.0, 0.05, tipping_thresh, slippage_thresh) is False

        # Slippage exceeds
        assert is_stable(5.0, 0.15, tipping_thresh, slippage_thresh) is False

        # Both exceed
        assert is_stable(15.0, 0.15, tipping_thresh, slippage_thresh) is False

    def test_get_stability_label_binary(self):
        """Verify get_stability_label returns binary 0/1."""
        # Stable -> 1
        assert get_stability_label(5.0, 0.05, 10.0, 0.1) == 1
        # Unstable -> 0
        assert get_stability_label(15.0, 0.05, 10.0, 0.1) == 0
        assert get_stability_label(5.0, 0.15, 10.0, 0.1) == 0

    def test_labeling_edge_cases(self):
        """Test labeling at exact threshold boundaries."""
        # Exactly at threshold should be stable (<=)
        assert get_stability_label(10.0, 0.1, 10.0, 0.1) == 1
        # Just over threshold should be unstable
        assert get_stability_label(10.0001, 0.1, 10.0, 0.1) == 0
        assert get_stability_label(10.0, 0.1001, 10.0, 0.1) == 0

    def test_config_integration(self):
        """Test that labeling logic integrates correctly with loaded config."""
        # Load real config and thresholds
        config = load_config()
        thresholds = get_thresholds()
        
        # Verify config exists and has expected structure
        assert config is not None
        assert "physics_metrics" in config
        
        # Test that we can use loaded thresholds
        tipping_thresh = thresholds["tipping_threshold"]
        slippage_thresh = thresholds["slippage_threshold"]
        
        # Should be able to call is_stable with loaded thresholds
        result = is_stable(5.0, 0.05, tipping_thresh, slippage_thresh)
        assert isinstance(result, bool)
        
        # Should be able to get a label with loaded thresholds
        label = get_stability_label(5.0, 0.05, tipping_thresh, slippage_thresh)
        assert label in [0, 1]