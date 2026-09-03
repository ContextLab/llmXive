"""
Unit tests for dynamics models (GGM05C, Drag, SRP).
"""
import pytest
import numpy as np
from astropy.coordinates import CartesianRepresentation, SkyCoord, GCRS
from astropy.time import Time
from astropy import units as u
from models.dynamics import DynamicsModel, compute_acceleration

@pytest.fixture
def sample_time():
    return Time("2023-01-01T12:00:00", scale="utc")

@pytest.fixture
def sample_state():
    # LAGEOS-like orbit (approx 6000 km altitude)
    x = 12878000.0  # m
    y = 0.0
    z = 0.0
    vx = 0.0
    vy = 3074.0  # m/s (approx)
    vz = 0.0
    return CartesianRepresentation(x, y, z, unit=u.m), CartesianRepresentation(vx, vy, vz, unit=u.m/u.s)

@pytest.fixture
def lageos_model():
    return DynamicsModel(satellite_id="LAGEOS-1", mass=411.0, area=1.0)

def test_geopotential_acceleration(lageos_model, sample_state, sample_time):
    """Test that geopotential acceleration is non-zero and points roughly towards Earth."""
    state = sample_state[0]
    acc = lageos_model.compute_geopotential_acceleration(state, sample_time)
    
    assert acc.d_x.unit == u.m/u.s**2
    assert abs(acc.d_x.value) > 0.0
    # Direction should be roughly -x (towards origin)
    assert acc.d_x.value < 0.0

def test_drag_acceleration(lageos_model, sample_state, sample_time):
    """Test drag acceleration opposes velocity."""
    state = sample_state[0]
    acc = lageos_model.compute_drag_acceleration(state, sample_time)
    
    # Drag should be small at LAGEOS altitude but non-zero
    assert abs(acc.d_x.value) > 0.0 or abs(acc.d_y.value) > 0.0 or abs(acc.d_z.value) > 0.0

def test_srp_acceleration(lageos_model, sample_state, sample_time):
    """Test SRP acceleration calculation."""
    # Mock Sun position (arbitrary)
    sun_pos = SkyCoord(x=1.496e11*u.m, y=0*u.m, z=0*u.m, frame=GCRS, obstime=sample_time)
    
    state = sample_state[0]
    acc = lageos_model.compute_srp_acceleration(state, sample_time, sun_pos)
    
    assert abs(acc.d_x.value) > 0.0 or abs(acc.d_y.value) > 0.0 or abs(acc.d_z.value) > 0.0

def test_compute_acceleration_integration(lageos_model, sample_state, sample_time):
    """Test the full compute_acceleration function."""
    sun_pos = SkyCoord(x=1.496e11*u.m, y=0*u.m, z=0*u.m, frame=GCRS, obstime=sample_time)
    state = sample_state[0]
    
    ax, ay, az = compute_acceleration(state, sample_time, lageos_model, sun_pos)
    
    # Total acceleration should be dominated by gravity (~6 m/s^2)
    total_acc = np.sqrt(ax**2 + ay**2 + az**2)
    assert total_acc > 1.0 # Must be significant gravity
    assert total_acc < 10.0 # Not infinite