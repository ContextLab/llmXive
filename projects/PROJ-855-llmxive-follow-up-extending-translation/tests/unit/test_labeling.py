import pytest
from utils.physics_metrics import calculate_tipping_angle, calculate_slippage_distance, is_stable, get_stability_label

class TestLabelingLogic:
    def test_calculate_tipping_angle_positive(self):
        """Test tipping angle calculation with positive displacement."""
        # Example: displacement_x = 0.1, height = 0.5
        # angle = atan(0.1 / 0.5) * (180 / pi)
        angle = calculate_tipping_angle(0.1, 0.5)
        expected = 11.309932474020213
        assert abs(angle - expected) < 0.001

    def test_calculate_tipping_angle_negative(self):
        """Test tipping angle calculation with negative displacement."""
        angle = calculate_tipping_angle(-0.1, 0.5)
        # Should be negative
        assert angle < 0

    def test_calculate_slippage_distance(self):
        """Test slippage distance calculation."""
        # Simple linear displacement
        distance = calculate_slippage_distance(0.05, 0.02)
        # sqrt(0.05^2 + 0.02^2)
        import math
        expected = math.sqrt(0.05**2 + 0.02**2)
        assert abs(distance - expected) < 0.0001

    def test_is_stable_within_thresholds(self):
        """Test stability check when within thresholds."""
        # tipping_angle=10, slippage=0.1
        assert is_stable(5.0, 0.05, 10.0, 0.1) is True

    def test_is_stable_exceeds_tipping(self):
        """Test stability check when tipping angle exceeds threshold."""
        assert is_stable(15.0, 0.05, 10.0, 0.1) is False

    def test_is_stable_exceeds_slippage(self):
        """Test stability check when slippage exceeds threshold."""
        assert is_stable(5.0, 0.15, 10.0, 0.1) is False

    def test_get_stability_label_stable(self):
        """Test labeling for stable object."""
        label = get_stability_label(5.0, 0.05, 10.0, 0.1)
        assert label == 1

    def test_get_stability_label_unstable_tipping(self):
        """Test labeling for unstable object due to tipping."""
        label = get_stability_label(15.0, 0.05, 10.0, 0.1)
        assert label == 0

    def test_get_stability_label_unstable_slippage(self):
        """Test labeling for unstable object due to slippage."""
        label = get_stability_label(5.0, 0.15, 10.0, 0.1)
        assert label == 0
