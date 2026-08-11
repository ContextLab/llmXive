"""
Unit tests for the Dynamics Model (GGM05C, Drag, SRP).
"""

import pytest
import numpy as np
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import CartesianRepresentation, ITRS

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from models.dynamics import DynamicsModel, compute_acceleration, GGM05C_COEFFS

@pytest.fixture
def lageos_state():
    """
    Approximate state vector for LAGEOS-1 at a specific epoch.
    Altitude ~ 5900 km, Velocity ~ 3.8 km/s.
    """
    r = 12270000.0 # ~ 12270 km from center (Earth radius + 5900km)
    v = 3800.0
    # Simple circular orbit in equatorial plane for testing
    state = np.array([r, 0.0, 0.0, 0.0, v, 0.0])
    return state

@pytest.fixture
def test_time():
    return Time("2023-01-01T12:00:00", scale='utc')

@pytest.fixture
def lageos_params():
    return {
        'area': 0.5,
        'mass': 409.0,
        'Cd': 2.2,
        'Cr': 1.1
    }

def test_geopotential_acceleration_j2(lageos_state, test_time, lageos_params):
    """
    Test that J2 acceleration is non-zero and has correct sign.
    J2 causes a perturbation in the Z direction and radial component.
    """
    model = DynamicsModel(lageos_params)
    r_vec = lageos_state[:3]
    a = model.compute_geopotential_acceleration(r_vec, test_time)

    # J2 acceleration should be significant (order of 10^-3 to 10^-4 m/s^2)
    assert np.linalg.norm(a) > 1e-5, "J2 acceleration is too small."

    # Check Z component (should be negative for positive Z, but here Z=0)
    # For a circular orbit in equatorial plane, J2 radial component is negative (attraction)
    # and there is no Z component if Z=0.
    # However, the formula a_z = factor * z * (5*z^2/r^2 - 3). If z=0, a_z=0.
    # a_x = factor * x * (5*0 - 1) = -factor * x. (Negative, attractive).
    assert a[0] < 0, "Radial acceleration should be negative (attractive)."

def test_drag_acceleration_direction(lageos_state, test_time, lageos_params):
    """
    Test that drag acceleration is opposite to velocity.
    """
    model = DynamicsModel(lageos_params)
    r_vec = lageos_state[:3]
    v_vec = lageos_state[3:]

    a_drag = model.compute_drag_acceleration(r_vec, v_vec, test_time)

    # Drag should be opposite to velocity
    # Dot product should be negative
    dot = np.dot(a_drag, v_vec)
    assert dot < 0, "Drag acceleration should oppose velocity."

def test_srp_acceleration_direction(lageos_state, test_time, lageos_params):
    """
    Test that SRP acceleration is in the direction away from the Sun.
    (Exact direction depends on Sun position, but magnitude should be reasonable).
    """
    model = DynamicsModel(lageos_params)
    r_vec = lageos_state[:3]

    a_srp = model.compute_srp_acceleration(r_vec, test_time)

    # Magnitude check: SRP is small, ~10^-7 to 10^-6 m/s^2
    mag = np.linalg.norm(a_srp)
    assert mag > 0, "SRP acceleration should be non-zero."
    assert mag < 1e-3, "SRP acceleration is unreasonably large."

def test_compute_acceleration_integration(lageos_state, test_time, lageos_params):
    """
    Test the full compute_acceleration function.
    """
    a = compute_acceleration(lageos_state, test_time, lageos_params)

    # Total acceleration should be dominated by gravity (10^-1 to 10^-2 m/s^2)
    # Gravity ~ GM/r^2 = 4e14 / (1.2e7)^2 ~ 2.7e-1 m/s^2
    # J2 is a perturbation.
    # Drag and SRP are small.
    assert np.linalg.norm(a) > 0.1, "Total acceleration is too small."
    assert np.linalg.norm(a) < 1.0, "Total acceleration is too large."

def test_dynamics_model_initialization():
    """
    Test that DynamicsModel initializes correctly.
    """
    params = {'area': 1.0, 'mass': 100.0}
    model = DynamicsModel(params)
    assert model.sat_params['area'] == 1.0
    assert model.sat_params['mass'] == 100.0