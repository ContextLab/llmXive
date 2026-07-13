"""
Unit tests for physics_metrics module.
"""

import math
import os
import tempfile
import pytest
from pathlib import Path

# Import the module under test
# We need to add the code directory to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.physics_metrics import (
    calculate_tipping_angle,
    calculate_slippage_distance,
    is_stable,
    get_stability_label,
    load_config,
    get_thresholds
)


class TestCalculateTippingAngle:
    """Tests for the calculate_tipping_angle function."""

    def test_no_tipping(self):
        """Test with no tipping (object upright)."""
        # Identity quaternion (no rotation)
        q = (0.0, 0.0, 0.0, 1.0)
        angle = calculate_tipping_angle(q)
        # Should be very close to 0 degrees (allowing for floating point error)
        assert math.isclose(angle, 0.0, abs_tol=1e-6)

    def test_90_degree_tipping(self):
        """Test with 90 degree rotation around Y axis."""
        # Quaternion for 90 degrees around Y: (0, sin(45), 0, cos(45))
        # sin(45) = cos(45) = sqrt(2)/2
        q = (0.0, math.sqrt(2)/2, 0.0, math.sqrt(2)/2)
        angle = calculate_tipping_angle(q)
        assert math.isclose(angle, 90.0, abs_tol=1e-6)

    def test_180_degree_tipping(self):
        """Test with 180 degree rotation (upside down)."""
        # Quaternion for 180 degrees around X: (sin(90), 0, 0, 0) = (1, 0, 0, 0)
        q = (1.0, 0.0, 0.0, 0.0)
        angle = calculate_tipping_angle(q)
        assert math.isclose(angle, 180.0, abs_tol=1e-6)

    def test_small_tipping(self):
        """Test with a small tipping angle."""
        # 10 degrees around Z
        # sin(5), 0, cos(5)
        angle_deg = 10.0
        half_angle = math.radians(angle_deg / 2)
        q = (0.0, 0.0, math.sin(half_angle), math.cos(half_angle))
        calculated_angle = calculate_tipping_angle(q)
        assert math.isclose(calculated_angle, angle_deg, abs_tol=1e-3)


class TestCalculateSlippageDistance:
    """Tests for the calculate_slippage_distance function."""

    def test_no_slippage(self):
        """Test with no movement."""
        initial = (1.0, 2.0, 3.0)
        final = (1.0, 2.0, 3.0)
        distance = calculate_slippage_distance(initial, final)
        assert distance == 0.0

    def test_simple_slippage(self):
        """Test with simple 1D movement."""
        initial = (0.0, 0.0, 0.0)
        final = (3.0, 0.0, 0.0)
        distance = calculate_slippage_distance(initial, final)
        assert distance == 3.0

    def test_diagonal_slippage(self):
        """Test with diagonal movement."""
        initial = (0.0, 0.0, 0.0)
        final = (3.0, 4.0, 0.0)
        distance = calculate_slippage_distance(initial, final)
        assert math.isclose(distance, 5.0, abs_tol=1e-6)

    def test_3d_slippage(self):
        """Test with 3D movement."""
        initial = (0.0, 0.0, 0.0)
        final = (1.0, 2.0, 2.0)
        distance = calculate_slippage_distance(initial, final)
        # sqrt(1 + 4 + 4) = sqrt(9) = 3
        assert math.isclose(distance, 3.0, abs_tol=1e-6)


class TestIsStable:
    """Tests for the is_stable function."""

    def test_stable_below_thresholds(self):
        """Test stable object below all thresholds."""
        # Default thresholds: tipping=15, slippage=0.02
        assert is_stable(10.0, 0.01) is True
        assert is_stable(0.0, 0.0) is True
        assert is_stable(14.9, 0.019) is True

    def test_unstable_tipping(self):
        """Test unstable object due to tipping."""
        assert is_stable(15.0, 0.01) is False
        assert is_stable(20.0, 0.01) is False

    def test_unstable_slippage(self):
        """Test unstable object due to slippage."""
        assert is_stable(10.0, 0.02) is False
        assert is_stable(10.0, 0.05) is False

    def test_unstable_both(self):
        """Test unstable object due to both factors."""
        assert is_stable(20.0, 0.05) is False

    def test_custom_thresholds(self):
        """Test with custom thresholds."""
        custom_thresholds = {"tipping_angle_deg": 10.0, "slippage_m": 0.01}
        assert is_stable(5.0, 0.005, custom_thresholds) is True
        assert is_stable(10.0, 0.005, custom_thresholds) is False
        assert is_stable(5.0, 0.01, custom_thresholds) is False


class TestGetStabilityLabel:
    """Tests for the get_stability_label function."""

    def test_stable_label(self):
        """Test that stable objects get label 1."""
        assert get_stability_label(10.0, 0.01) == 1

    def test_unstable_label(self):
        """Test that unstable objects get label 0."""
        assert get_stability_label(20.0, 0.05) == 0

    def test_boundary_conditions(self):
        """Test boundary conditions."""
        # At exactly the threshold, should be unstable (>=)
        assert get_stability_label(15.0, 0.01) == 0
        assert get_stability_label(10.0, 0.02) == 0


class TestConfigLoading:
    """Tests for config loading functionality."""

    def test_load_config_from_temp_file(self):
        """Test loading config from a temporary file."""
        config_content = """
        thresholds:
          tipping_angle_deg: 20.0
          slippage_m: 0.05
        sensitivity_analysis:
          enabled: true
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config["thresholds"]["tipping_angle_deg"] == 20.0
            assert config["thresholds"]["slippage_m"] == 0.05
            assert config["sensitivity_analysis"]["enabled"] is True
        finally:
            os.unlink(temp_path)

    def test_get_thresholds(self):
        """Test extracting thresholds from config."""
        config = {
            "thresholds": {
                "tipping_angle_deg": 25.0,
                "slippage_m": 0.03
            }
        }
        thresholds = get_thresholds(config)
        assert thresholds["tipping_angle_deg"] == 25.0
        assert thresholds["slippage_m"] == 0.03

    def test_missing_threshold_raises_error(self):
        """Test that missing threshold keys raise an error."""
        config = {
            "thresholds": {
                "tipping_angle_deg": 25.0
                # Missing slippage_m
            }
        }
        with pytest.raises(KeyError):
            get_thresholds(config)

    def test_invalid_config_file(self):
        """Test that invalid config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")
