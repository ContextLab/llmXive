"""
Unit tests for code/physics.py mass loss calculation against the energy-limited formula (FR-004).

Tests the calculate_retention_fraction function which implements:
M_dot = (epsilon * pi * R_p^3 * F_XUV) / (G * M_p * K_tide)
Retention = 1 - (integral(M_dot dt) / M_atm_initial)
where M_atm_initial = 0.01 * M_p
"""
import numpy as np
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.physics import calculate_retention_fraction
from code.config import G, EFFICIENCY, K_TIDE, M_ATM_INITIAL_BASELINE

# Use SI units for consistency with physics module
# Constants
SOLAR_MASS = 1.989e30  # kg
SOLAR_RADIUS = 6.957e8  # m
EARTH_MASS = 5.972e24  # kg
EARTH_RADIUS = 6.371e6  # m
J_TO_ERG = 1e7  # conversion factor

def test_mass_loss_calculation_energy_limited():
    """
    Test mass loss calculation against the energy-limited formula.
    
    Manual calculation for verification:
    Given:
    - R_p = 1.0 R_earth = 6.371e6 m
    - M_p = 1.0 M_earth = 5.972e24 kg
    - F_XUV = 1000 W/m^2 = 1000 J/s/m^2 = 1e10 erg/s/cm^2
    - epsilon = 0.15
    - K_tide = 1.0
    - G = 6.674e-11 m^3/kg/s^2
    - age = 1 Gyr = 3.154e16 s
    
    M_dot = (epsilon * pi * R_p^3 * F_XUV) / (G * M_p * K_tide)
    M_dot = (0.15 * pi * (6.371e6)^3 * 1000) / (6.674e-11 * 5.972e24 * 1.0)
    M_dot = (0.15 * pi * 2.586e20 * 1000) / (3.986e14)
    M_dot = (1.22e23) / (3.986e14)
    M_dot = 3.06e8 kg/s
    
    Total mass loss over 1 Gyr:
    delta_M = M_dot * age = 3.06e8 * 3.154e16 = 9.65e24 kg
    
    M_atm_initial = 0.01 * M_p = 0.01 * 5.972e24 = 5.972e22 kg
    
    Retention = 1 - (delta_M / M_atm_initial)
    Retention = 1 - (9.65e24 / 5.972e22)
    Retention = 1 - 161.6
    Retention = -160.6 (clamped to 0)
    """
    
    # Test parameters
    mass = 1.0 * EARTH_MASS  # kg
    radius = 1.0 * EARTH_RADIUS  # m
    cumulative_flux = 1e10  # erg/s/cm^2 (converted to W/m^2 = 1000)
    age = 1e9  # years
    
    result = calculate_retention_fraction(
        mass=mass,
        radius=radius,
        cumulative_flux=cumulative_flux,
        age=age
    )
    
    # The retention should be 0 (completely stripped) for these extreme parameters
    assert result['retention_fraction'] == 0.0
    assert result['mass_loss_rate'] > 0
    assert result['total_mass_loss'] > 0
    
def test_retention_calculation_with_partial_loss():
    """
    Test a scenario where only partial atmospheric loss occurs.
    
    Using lower flux to get a retention fraction between 0 and 1.
    """
    mass = 1.0 * EARTH_MASS
    radius = 1.0 * EARTH_RADIUS
    cumulative_flux = 1e7  # Lower flux (erg/s/cm^2)
    age = 1e9  # 1 Gyr
    
    result = calculate_retention_fraction(
        mass=mass,
        radius=radius,
        cumulative_flux=cumulative_flux,
        age=age
    )
    
    # Verify the structure of the output
    assert 'retention_fraction' in result
    assert 'mass_loss_rate' in result
    assert 'total_mass_loss' in result
    
    # Retention should be between 0 and 1
    assert 0.0 <= result['retention_fraction'] <= 1.0
    
    # Mass loss rate should be positive
    assert result['mass_loss_rate'] > 0
    
def test_mass_loss_rate_formula():
    """
    Verify the mass loss rate calculation matches the energy-limited formula:
    M_dot = (epsilon * pi * R_p^3 * F_XUV) / (G * M_p * K_tide)
    """
    mass = 1.0 * EARTH_MASS
    radius = 1.0 * EARTH_RADIUS
    cumulative_flux = 1e10  # erg/s/cm^2
    age = 1e9  # years
    
    result = calculate_retention_fraction(
        mass=mass,
        radius=radius,
        cumulative_flux=cumulative_flux,
        age=age
    )
    
    # Calculate expected M_dot manually
    F_XUV_W_m2 = cumulative_flux * 1e-3  # erg/s/cm^2 to W/m^2
    expected_M_dot = (
        EFFICIENCY * np.pi * radius**3 * F_XUV_W_m2
    ) / (G * mass * K_TIDE)
    
    # Check that calculated M_dot matches expected (within 1% tolerance)
    assert np.isclose(result['mass_loss_rate'], expected_M_dot, rtol=0.01)
    
def test_retention_clamping():
    """
    Test that retention fraction is properly clamped to [0, 1].
    """
    # Extreme case: should clamp to 0
    mass = 1.0 * EARTH_MASS
    radius = 1.0 * EARTH_RADIUS
    cumulative_flux = 1e12  # Very high flux
    age = 1e9  # 1 Gyr
    
    result = calculate_retention_fraction(
        mass=mass,
        radius=radius,
        cumulative_flux=cumulative_flux,
        age=age
    )
    
    assert result['retention_fraction'] == 0.0
    
    # Very low flux: should be close to 1
    cumulative_flux_low = 1e3  # Very low flux
    result_low = calculate_retention_fraction(
        mass=mass,
        radius=radius,
        cumulative_flux=cumulative_flux_low,
        age=age
    )
    
    assert result_low['retention_fraction'] >= 0.99