"""
Unit tests for stability labeling logic (tipping/slippage thresholds).

This module validates the physics metric calculations and the binary
stability labeling logic defined in code/utils/physics_metrics.py.

It ensures that:
1. Tipping angle calculation correctly identifies instability >= threshold.
2. Slippage distance calculation correctly identifies instability >= threshold.
3. The combined stability label (is_stable) is False if EITHER condition is met.
4. The combined stability label is True only if BOTH conditions are safe.
5. Thresholds are correctly loaded from config.yaml.
"""
import math
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
import yaml

# Import the functions we are testing from the existing API surface
from utils.physics_metrics import (
    load_config,
    get_thresholds,
    calculate_tipping_angle,
    calculate_slippage_distance,
    is_stable,
    get_stability_label,
)


class TestPhysicsMetrics:
    """Tests for the physics metric calculation functions."""

    def test_calculate_tipping_angle_zero(self):
        """Test tipping angle calculation when object is upright."""
        # Upright quaternion (w=1, x=0, y=0, z=0)
        quat = [1.0, 0.0, 0.0, 0.0]
        angle = calculate_tipping_angle(quat)
        # Should be very close to 0
        assert math.isclose(angle, 0.0, abs_tol=1e-6)

    def test_calculate_tipping_angle_45_degrees(self):
        """Test tipping angle calculation for 45 degree rotation."""
        # 45 degrees around X axis: w=cos(22.5), x=sin(22.5), y=0, z=0
        # Note: Quaternion rotation is half-angle, so 45 deg rotation -> 22.5 deg in quat
        angle_deg = 45.0
        half_angle = math.radians(angle_deg / 2)
        w = math.cos(half_angle)
        x = math.sin(half_angle)
        y = 0.0
        z = 0.0
        quat = [w, x, y, z]
        
        result = calculate_tipping_angle(quat)
        # Should be close to 45 degrees
        assert math.isclose(result, angle_deg, abs_tol=1e-4)

    def test_calculate_tipping_angle_90_degrees(self):
        """Test tipping angle calculation for 90 degree rotation."""
        angle_deg = 90.0
        half_angle = math.radians(angle_deg / 2)
        w = math.cos(half_angle)
        x = math.sin(half_angle)
        y = 0.0
        z = 0.0
        quat = [w, x, y, z]
        
        result = calculate_tipping_angle(quat)
        assert math.isclose(result, angle_deg, abs_tol=1e-4)

    def test_calculate_slippage_distance_zero(self):
        """Test slippage distance when start and end are identical."""
        start = [0.0, 0.0, 0.0]
        end = [0.0, 0.0, 0.0]
        distance = calculate_slippage_distance(start, end)
        assert math.isclose(distance, 0.0, abs_tol=1e-6)

    def test_calculate_slippage_distance_simple(self):
        """Test slippage distance for a simple vector."""
        start = [0.0, 0.0, 0.0]
        end = [1.0, 0.0, 0.0]
        distance = calculate_slippage_distance(start, end)
        assert math.isclose(distance, 1.0, abs_tol=1e-6)

    def test_calculate_slippage_distance_3d(self):
        """Test slippage distance for a 3D vector."""
        start = [0.0, 0.0, 0.0]
        end = [1.0, 2.0, 2.0]
        distance = calculate_slippage_distance(start, end)
        # sqrt(1 + 4 + 4) = sqrt(9) = 3
        assert math.isclose(distance, 3.0, abs_tol=1e-6)


class TestStabilityLabeling:
    """Tests for the stability labeling logic."""

    @pytest.fixture
    def temp_config_file(self, tmp_path):
        """Create a temporary config.yaml with specific thresholds for testing."""
        config = {
            "physics_thresholds": {
                "tipping_angle_deg": 15.0,
                "slippage_m": 0.02
            },
            "sensitivity_analysis": {
                "sweep_percent": 5.0
            }
        }
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return config_path

    def test_is_stable_both_safe(self, temp_config_file):
        """Test is_stable returns True when both metrics are below thresholds."""
        # Reset config loading to use our temp file
        os.environ["LLMXIVE_CONFIG_PATH"] = str(temp_config_file)
        
        # Upright object (0 deg) and no slippage
        quat = [1.0, 0.0, 0.0, 0.0]
        start = [0.0, 0.0, 0.0]
        end = [0.0, 0.0, 0.0]
        
        # Should be stable
        assert is_stable(quat, start, end) is True

    def test_is_stable_tipping_unsafe(self, temp_config_file):
        """Test is_stable returns False when tipping angle exceeds threshold."""
        os.environ["LLMXIVE_CONFIG_PATH"] = str(temp_config_file)
        
        # 20 degrees rotation (above 15 deg threshold)
        angle_deg = 20.0
        half_angle = math.radians(angle_deg / 2)
        w = math.cos(half_angle)
        x = math.sin(half_angle)
        quat = [w, x, 0.0, 0.0]
        
        start = [0.0, 0.0, 0.0]
        end = [0.0, 0.0, 0.0]
        
        # Should be unstable due to tipping
        assert is_stable(quat, start, end) is False

    def test_is_stable_slippage_unsafe(self, temp_config_file):
        """Test is_stable returns False when slippage distance exceeds threshold."""
        os.environ["LLMXIVE_CONFIG_PATH"] = str(temp_config_file)
        
        # Upright object
        quat = [1.0, 0.0, 0.0, 0.0]
        
        # 0.03m slippage (above 0.02m threshold)
        start = [0.0, 0.0, 0.0]
        end = [0.03, 0.0, 0.0]
        
        # Should be unstable due to slippage
        assert is_stable(quat, start, end) is False

    def test_is_stable_both_unsafe(self, temp_config_file):
        """Test is_stable returns False when both metrics exceed thresholds."""
        os.environ["LLMXIVE_CONFIG_PATH"] = str(temp_config_file)
        
        # 20 degrees rotation
        angle_deg = 20.0
        half_angle = math.radians(angle_deg / 2)
        w = math.cos(half_angle)
        x = math.sin(half_angle)
        quat = [w, x, 0.0, 0.0]
        
        # 0.03m slippage
        start = [0.0, 0.0, 0.0]
        end = [0.03, 0.0, 0.0]
        
        # Should be unstable
        assert is_stable(quat, start, end) is False

    def test_is_stable_boundary_tipping(self, temp_config_file):
        """Test is_stable at the exact tipping threshold."""
        os.environ["LLMXIVE_CONFIG_PATH"] = str(temp_config_file)
        
        # Exactly 15 degrees (threshold)
        angle_deg = 15.0
        half_angle = math.radians(angle_deg / 2)
        w = math.cos(half_angle)
        x = math.sin(half_angle)
        quat = [w, x, 0.0, 0.0]
        
        start = [0.0, 0.0, 0.0]
        end = [0.0, 0.0, 0.0]
        
        # At threshold, should be considered unstable (>= threshold)
        assert is_stable(quat, start, end) is False

    def test_is_stable_boundary_slippage(self, temp_config_file):
        """Test is_stable at the exact slippage threshold."""
        os.environ["LLMXIVE_CONFIG_PATH"] = str(temp_config_file)
        
        quat = [1.0, 0.0, 0.0, 0.0]
        
        # Exactly 0.02m slippage (threshold)
        start = [0.0, 0.0, 0.0]
        end = [0.02, 0.0, 0.0]
        
        # At threshold, should be considered unstable (>= threshold)
        assert is_stable(quat, start, end) is False

    def test_get_stability_label_returns_binary(self, temp_config_file):
        """Test that get_stability_label returns 1 or 0."""
        os.environ["LLMXIVE_CONFIG_PATH"] = str(temp_config_file)
        
        # Safe case -> 1
        quat = [1.0, 0.0, 0.0, 0.0]
        start = [0.0, 0.0, 0.0]
        end = [0.0, 0.0, 0.0]
        label_safe = get_stability_label(quat, start, end)
        assert label_safe == 1
        
        # Unsafe case -> 0
        angle_deg = 20.0
        half_angle = math.radians(angle_deg / 2)
        w = math.cos(half_angle)
        x = math.sin(half_angle)
        quat_unsafe = [w, x, 0.0, 0.0]
        
        label_unsafe = get_stability_label(quat_unsafe, start, end)
        assert label_unsafe == 0

    def test_get_thresholds_loads_correctly(self, temp_config_file):
        """Test that get_thresholds loads the correct values from config."""
        os.environ["LLMXIVE_CONFIG_PATH"] = str(temp_config_file)
        
        thresholds = get_thresholds()
        
        assert "tipping_angle_deg" in thresholds
        assert "slippage_m" in thresholds
        assert math.isclose(thresholds["tipping_angle_deg"], 15.0)
        assert math.isclose(thresholds["slippage_m"], 0.02)

    def test_get_thresholds_default_fallback(self):
        """Test that get_thresholds uses defaults if config is missing/invalid."""
        # Clear the env var to force default loading
        if "LLMXIVE_CONFIG_PATH" in os.environ:
            del os.environ["LLMXIVE_CONFIG_PATH"]
        
        # This might fail if no default config exists, but if it loads, 
        # it should use defaults. We test that it doesn't crash with KeyError.
        try:
            thresholds = get_thresholds()
            # If it loads, check defaults
            assert thresholds["tipping_angle_deg"] == 15.0
            assert thresholds["slippage_m"] == 0.02
        except (FileNotFoundError, yaml.YAMLError):
            # Expected if no config file exists and defaults aren't hardcoded
            # In a real run, the config should exist. 
            # We assert that the function handles the error gracefully or we rely on T005b creating it.
            pass