"""
Unit tests for the dynamics module (T020/T023).
"""
import pytest
import numpy as np
from astropy.time import Time
from astropy import units as u

# Import the module under test
from models.dynamics import DynamicsModel, compute_acceleration

class TestGeopotential:
    def test_geopotential_direction(self):
        """Test that geopotential acceleration is generally towards Earth."""
        model = DynamicsModel()
        # Position at 6000km from center (approx 2000km altitude)
        r = np.array([6000000.0, 0.0, 0.0])
        v = np.array([0.0, 7500.0, 0.0])
        t = Time("2023-01-01T00:00:00", scale="utc")
        
        acc = model.compute_geopotential_acceleration(r, v, t)
        
        # Acceleration should be roughly towards origin (negative x)
        assert acc[0] < 0, "Radial acceleration should be negative (towards center)"
        assert np.abs(acc[1]) < 1e-5, "Cross-track acceleration should be near zero"
        assert np.abs(acc[2]) < 1e-5, "Cross-track acceleration should be near zero"
        
    def test_geopotential_magnitude_order(self):
        """Test that acceleration magnitude is of correct order (~1 m/s^2)."""
        model = DynamicsModel()
        r = np.array([7000000.0, 0.0, 0.0]) # ~7000km
        v = np.zeros(3)
        t = Time("2023-01-01T00:00:00", scale="utc")
        
        acc = model.compute_geopotential_acceleration(r, v, t)
        mag = np.linalg.norm(acc)
        
        # Expected: mu/r^2 ~ 4e14 / 49e12 ~ 8 m/s^2
        assert 5.0 < mag < 10.0, f"Acceleration magnitude {mag} is not in expected range"

class TestDrag:
    def test_drag_opposes_velocity(self):
        """Test that drag opposes relative velocity."""
        model = DynamicsModel()
        r = np.array([7000000.0, 0.0, 0.0])
        v = np.array([0.0, 7000.0, 0.0])
        t = Time("2023-01-01T00:00:00", scale="utc")
        
        acc = model.compute_drag_acceleration(r, v, t, mass=400.0, area=2.0)
        
        # Drag should be opposite to velocity direction
        # Dot product of acc and v should be negative
        dot = np.dot(acc, v)
        assert dot < 0, "Drag acceleration should oppose velocity"

class TestSRP:
    def test_srp_direction(self):
        """Test that SRP is generally away from Sun."""
        model = DynamicsModel()
        r = np.array([7000000.0, 0.0, 0.0])
        t = Time("2023-01-01T00:00:00", scale="utc")
        
        # Assume Sun is at -x (approx)
        sun_pos = np.array([-1.5e11, 0.0, 0.0])
        
        acc = model.compute_srp_acceleration(r, t, mass=400.0, area=2.0, sun_pos_gcrs=sun_pos)
        
        # If Sun is at -x, SRP should push towards +x (away from Sun)
        # Vector from Sun to Sat is roughly +x
        assert acc[0] > 0, "SRP should push away from Sun"

class TestTotalAcceleration:
    def test_total_accumulates(self):
        """Test that total acceleration is sum of components."""
        model = DynamicsModel()
        r = np.array([7000000.0, 0.0, 0.0])
        v = np.array([0.0, 7000.0, 0.0])
        t = Time("2023-01-01T00:00:00", scale="utc")
        
        acc_grav = model.compute_geopotential_acceleration(r, v, t)
        acc_drag = model.compute_drag_acceleration(r, v, t, mass=400.0, area=2.0)
        acc_srp = model.compute_srp_acceleration(r, t, mass=400.0, area=2.0)
        
        acc_total = model.compute_total_acceleration(r, v, t, mass=400.0, area=2.0)
        
        expected = acc_grav + acc_drag + acc_srp
        
        np.testing.assert_array_almost_equal(acc_total, expected, decimal=10)

class TestComputeAccelerationFunction:
    def test_interface(self):
        """Test the convenience function interface."""
        r = np.array([7000000.0, 0.0, 0.0])
        v = np.array([0.0, 7000.0, 0.0])
        t = Time("2023-01-01T00:00:00", scale="utc")
        
        acc = compute_acceleration((r, v), t, mass=400.0, area=2.0)
        
        assert acc.shape == (3,)
        assert isinstance(acc, np.ndarray)