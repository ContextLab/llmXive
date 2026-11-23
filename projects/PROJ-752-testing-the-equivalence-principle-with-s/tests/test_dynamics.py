"""
Unit tests for dynamical model components (geopotential, drag, SRP, relativity).
Tests the components implemented in T023 (models/dynamics.py).
"""
import pytest
import numpy as np
from astropy.coordinates import CartesianRepresentation, SkyCoord, GCRS, ITRS
from astropy.time import Time
from astropy import units as u
from astropy.constants import G, M_earth
import sys
import os

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from models.dynamics import (
    DynamicsModel, 
    compute_geopotential_acceleration, 
    compute_jacchia_drag_acceleration, 
    compute_srp_acceleration, 
    compute_acceleration,
    delta
)
from utils.logging import get_logger

logger = get_logger(__name__)

@pytest.fixture
def sample_time():
    """Fixture for a standard test time."""
    return Time("2023-01-01T12:00:00", scale="utc")

@pytest.fixture
def sample_state():
    """
    Fixture for a LAGEOS-like state vector.
    Approx 6000 km altitude, circular orbit.
    Returns (position, velocity) in CartesianRepresentation.
    """
    # LAGEOS semi-major axis ~ 12270 km (Earth radius + ~5900km altitude)
    r_mag = 12270000.0  # meters
    x = r_mag
    y = 0.0
    z = 0.0
    
    # Circular orbit velocity v = sqrt(GM/r)
    # GM_earth = 3.986004418e14 m^3/s^2
    mu = G * M_earth
    v_mag = np.sqrt(mu / r_mag)
    
    vx = 0.0
    vy = v_mag
    vz = 0.0

    pos = CartesianRepresentation(x, y, z, unit=u.m)
    vel = CartesianRepresentation(vx, vy, vz, unit=u.m/u.s)
    return pos, vel

@pytest.fixture
def lageos_model():
    """Fixture for LAGEOS-1 DynamicsModel."""
    # Mass ~ 411 kg, Area ~ 1.0 m^2 (approx for sphere of 30cm radius)
    # Reflectivity ~ 0.9
    return DynamicsModel(
        satellite_id="LAGEOS-1", 
        mass=411.0, 
        area=1.0, 
        reflectivity=0.9
    )

@pytest.fixture
def sun_position(sample_time):
    """Mock Sun position in GCRS for SRP test."""
    # Approximate Sun position at J2000 or similar
    # Distance ~ 1 AU
    return SkyCoord(
        x=1.496e11*u.m, 
        y=0*u.m, 
        z=0*u.m, 
        frame=GCRS, 
        obstime=sample_time
    )

def test_geopotential_acceleration(lageos_model, sample_state, sample_time):
    """
    Test that geopotential acceleration is non-zero and points roughly towards Earth.
    Validates T023a (GGM model).
    """
    state = sample_state[0]
    # compute_geopotential_acceleration expects (x, y, z) arrays or similar
    # The API in models.dynamics returns a CartesianDifferential or tuple
    try:
        acc = lageos_model.compute_geopotential_acceleration(state, sample_time)
        
        # Check units
        assert acc.d_x.unit == u.m/u.s**2
        assert abs(acc.d_x.value) > 0.0 or abs(acc.d_y.value) > 0.0 or abs(acc.d_z.value) > 0.0
        
        # Direction should be roughly -r (towards origin)
        # Dot product of position and acceleration should be negative
        pos_vec = np.array([state.x.value, state.y.value, state.z.value])
        acc_vec = np.array([acc.d_x.value, acc.d_y.value, acc.d_z.value])
        dot_product = np.dot(pos_vec, acc_vec)
        assert dot_product < 0, "Gravity should be attractive (negative dot product)"
        
        logger.info(f"Geopotential test passed. Acc: {acc_vec}")
    except Exception as e:
        pytest.fail(f"Geopotential acceleration test failed: {e}")

def test_drag_acceleration(lageos_model, sample_state, sample_time):
    """
    Test drag acceleration opposes velocity.
    Validates T023b (Jacchia drag).
    """
    state = sample_state[0]
    vel = sample_state[1]
    
    try:
        acc = lageos_model.compute_drag_acceleration(state, sample_time)
        
        # Drag should be small but non-zero at LAGEOS altitude (very thin atmosphere)
        # However, strictly speaking, at 5900km altitude, density is effectively zero.
        # The model might return 0. We assert it doesn't crash and returns a vector.
        assert acc is not None
        
        # Check units
        assert acc.d_x.unit == u.m/u.s**2
        
        # If non-zero, it must oppose velocity
        if np.any(acc.to(u.m/u.s**2).value != 0):
            vel_vec = np.array([vel.x.value, vel.y.value, vel.z.value])
            acc_vec = np.array([acc.d_x.value, acc.d_y.value, acc.d_z.value])
            dot_product = np.dot(vel_vec, acc_vec)
            # Drag opposes motion, so dot product should be negative
            assert dot_product < 0, "Drag should oppose velocity"
        
        logger.info(f"Drag test passed. Acc: {acc}")
    except Exception as e:
        pytest.fail(f"Drag acceleration test failed: {e}")

def test_srp_acceleration(lageos_model, sample_state, sample_time, sun_position):
    """
    Test SRP acceleration calculation.
    Validates T023c (SRP model).
    """
    state = sample_state[0]
    
    try:
        acc = lageos_model.compute_srp_acceleration(state, sample_time, sun_position)
        
        # SRP should be non-zero
        assert acc is not None
        assert acc.d_x.unit == u.m/u.s**2
        
        # Check magnitude is reasonable (order of 1e-7 to 1e-6 m/s^2 for LAGEOS)
        mag = np.sqrt(acc.d_x.value**2 + acc.d_y.value**2 + acc.d_z.value**2)
        assert mag > 0.0, "SRP acceleration must be non-zero"
        assert mag < 1e-3, "SRP acceleration magnitude seems unphysically large"
        
        logger.info(f"SRP test passed. Acc: {acc}, Mag: {mag}")
    except Exception as e:
        pytest.fail(f"SRP acceleration test failed: {e}")

def test_compute_acceleration_integration(lageos_model, sample_state, sample_time, sun_position):
    """
    Test the full compute_acceleration function (integration of all forces).
    Validates T023d (Relativity) and overall integration.
    """
    state = sample_state[0]
    
    try:
        # compute_acceleration returns (ax, ay, az) in m/s^2
        ax, ay, az = compute_acceleration(state, sample_time, lageos_model, sun_position)
        
        # Total acceleration should be dominated by gravity (~6 m/s^2 at this altitude)
        total_acc = np.sqrt(ax**2 + ay**2 + az**2)
        
        # Gravity at 12270km: GM/r^2 = 3.986e14 / (1.227e7)^2 ≈ 2.64 m/s^2
        # Plus small perturbations.
        assert total_acc > 1.0, "Total acceleration must be significant (gravity)"
        assert total_acc < 10.0, "Total acceleration must not be infinite"
        
        # Verify components are finite
        assert np.isfinite(ax) and np.isfinite(ay) and np.isfinite(az)
        
        logger.info(f"Integration test passed. Total Acc: {total_acc:.4f} m/s^2")
    except Exception as e:
        pytest.fail(f"Compute acceleration integration test failed: {e}")

def test_delta_function():
    """
    Test the delta function (unit conversion helper) used in dynamics.
    """
    try:
        # Test basic conversion
        val = 1.0 * u.m
        result = delta(val)
        assert result == 1.0
        
        val_km = 1.0 * u.km
        result_km = delta(val_km)
        assert result_km == 1000.0
        
        logger.info("Delta function test passed.")
    except Exception as e:
        pytest.fail(f"Delta function test failed: {e}")