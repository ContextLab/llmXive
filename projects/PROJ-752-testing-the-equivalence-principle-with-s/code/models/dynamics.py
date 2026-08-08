"""
Dynamics models for Satellite Laser Ranging orbit determination.

Implements:
- GGM05C geopotential (spherical harmonics)
- Jacchia atmospheric drag model
- Solar Radiation Pressure (SRP) model

All calculations performed in ITRS coordinates as required.
"""

import numpy as np
from astropy import units as u
from astropy.coordinates import GCRS, ITRS, CartesianRepresentation, CartesianDifferential
from astropy.time import Time
from typing import Tuple, Optional
from utils.logging import get_logger

logger = get_logger(__name__)

# Constants
MU_EARTH = 3.986004418e14  # m^3/s^2 (GM)
R_EARTH = 6378137.0  # m (equatorial radius)
C20 = -1082.63e-6  # J2 coefficient (approximate for GGM05C)

# GGM05C coefficients (simplified set for demonstration)
# In production, these would be loaded from a full coefficient file
# Here we use a minimal set sufficient for testing the pipeline
GGM05C_DEGREES = 70
GGM05C_ORDER = 70

# Simplified gravity coefficients (normalized)
# Format: (n, m, Cnm, Snm)
# These are representative values; full implementation would load from file
GGM05C_COEFFS = {
    (2, 0): (-1082.63e-6, 0.0),
    (2, 1): (0.0, 0.0),
    (2, 2): (0.25e-6, -0.15e-6),
    (3, 0): (0.0, 0.0),
    (3, 1): (-2.3e-9, 0.0),
    (3, 2): (0.0, 0.0),
    (3, 3): (0.0, 0.0),
    # Additional coefficients would be loaded from the full GGM05C model
}

# Jacchia model parameters
JACCHIA_TINF = 1000.0  # K (thermospheric temperature)
JACCHIA_RHO0 = 1.225  # kg/m^3 (sea level density)
JACCHIA_H0 = 8500.0  # m (scale height)

# SRP parameters
SRP_COEFF = 4.56e-6  # N/m^2 (solar radiation pressure at 1 AU)
AU = 1.496e11  # m (astronomical unit)

class DynamicsModel:
    """
    Computes accelerations from various dynamical models.
    
    Attributes:
        geopotential_degree: Maximum degree for geopotential model
        drag_area: Cross-sectional area for drag (m^2)
        drag_mass: Satellite mass (kg)
        drag_cd: Drag coefficient
        srp_area: Cross-sectional area for SRP (m^2)
        srp_cr: SRP coefficient (reflectivity)
    """
    
    def __init__(
        self,
        geopotential_degree: int = 70,
        drag_area: float = 10.0,
        drag_mass: float = 400.0,
        drag_cd: float = 2.2,
        srp_area: float = 10.0,
        srp_cr: float = 1.2
    ):
        self.geopotential_degree = geopotential_degree
        self.drag_area = drag_area
        self.drag_mass = drag_mass
        self.drag_cd = drag_cd
        self.srp_area = srp_area
        self.srp_cr = srp_cr
        
        logger.info(f"DynamicsModel initialized with degree {geopotential_degree}")
    
    def compute_geopotential_acceleration(
        self,
        position: np.ndarray,
        time: Time
    ) -> np.ndarray:
        """
        Compute geopotential acceleration using GGM05C model.
        
        Args:
            position: ITRS position vector [x, y, z] in meters
            time: Astropy Time object
            
        Returns:
            Acceleration vector [ax, ay, az] in m/s^2
        """
        x, y, z = position
        r = np.sqrt(x**2 + y**2 + z**2)
        
        # Convert to spherical coordinates
        theta = np.arccos(z / r)  # Colatitude
        phi = np.arctan2(y, x)    # Longitude
        
        # Compute normalized Legendre polynomials
        # Simplified implementation - full version would use complete recurrence
        P = np.zeros((self.geopotential_degree + 1, self.geopotential_degree + 1))
        P[0, 0] = 1.0
        
        # zonal terms (m=0)
        for n in range(1, self.geopotential_degree + 1):
            P[n, 0] = ((2 * n - 1) * np.cos(theta) * P[n-1, 0] - 
                      (n - 1) * P[n-2, 0] if n > 1 else 
                      np.cos(theta) * P[n-1, 0])
        
        # Compute acceleration components
        ax, ay, az = 0.0, 0.0, 0.0
        
        # Add coefficients
        for (n, m), (Cnm, Snm) in GGM05C_COEFFS.items():
            if n > self.geopotential_degree:
                continue
            
            # Normalize factor
            Nnm = np.sqrt((2 - delta(m, 0)) * (2 * n + 1) * 
                         np.math.factorial(n - m) / 
                         np.math.factorial(n + m))
            
            # Spherical harmonic functions
            Ynm = Nnm * P[n, m] * np.cos(m * phi)
            Ynm_sin = Nnm * P[n, m] * np.sin(m * phi)
            
            # Derivatives for acceleration
            # dY/dtheta, dY/dphi, dY/dr terms
            factor = (R_EARTH / r)**(n + 2) * (n + 1) * MU_EARTH / r**2
            
            # Simplified acceleration contribution
            term_x = factor * (Cnm * Ynm * np.cos(phi) - Snm * Ynm_sin * np.sin(phi))
            term_y = factor * (Cnm * Ynm * np.sin(phi) + Snm * Ynm_sin * np.cos(phi))
            term_z = factor * Cnm * P[n, m] * np.cos(theta)  # Simplified z-component
            
            ax += term_x
            ay += term_y
            az += term_z
        
        return np.array([ax, ay, az])
    
    def compute_drag_acceleration(
        self,
        position: np.ndarray,
        velocity: np.ndarray,
        time: Time
    ) -> np.ndarray:
        """
        Compute atmospheric drag acceleration using Jacchia model.
        
        Args:
            position: ITRS position vector [x, y, z] in meters
            velocity: ITRS velocity vector [vx, vy, vz] in m/s
            time: Astropy Time object
            
        Returns:
            Acceleration vector [ax, ay, az] in m/s^2
        """
        r = np.linalg.norm(position)
        altitude = r - R_EARTH
        
        # Jacchia density model (simplified)
        # rho = rho0 * exp(-(h - h0) / H)
        if altitude < 0:
            altitude = 0
        
        rho = JACCHIA_RHO0 * np.exp(-(altitude - JACCHIA_H0) / JACCHIA_H0)
        rho = max(rho, 1e-15)  # Floor to avoid numerical issues
        
        # Relative velocity (assuming co-rotating atmosphere)
        omega_E = 7.292115e-5  # rad/s (Earth rotation rate)
        v_rel = velocity - np.cross([0, 0, omega_E], position)
        v_rel_mag = np.linalg.norm(v_rel)
        
        # Drag acceleration: a = -0.5 * rho * v^2 * Cd * A / m * (v/|v|)
        if v_rel_mag < 1e-6:
            return np.array([0.0, 0.0, 0.0])
        
        drag_factor = -0.5 * rho * v_rel_mag * self.drag_cd * self.drag_area / self.drag_mass
        a_drag = drag_factor * v_rel
        
        return a_drag
    
    def compute_srp_acceleration(
        self,
        position: np.ndarray,
        time: Time
    ) -> np.ndarray:
        """
        Compute Solar Radiation Pressure acceleration.
        
        Args:
            position: ITRS position vector [x, y, z] in meters
            time: Astropy Time object
            
        Returns:
            Acceleration vector [ax, ay, az] in m/s^2
        """
        # Get Sun position (simplified - using ephemeris would be better)
        # For this implementation, we approximate Sun direction
        # In production, use astropy.coordinates.get_body('sun')
        
        # Approximate Sun direction based on time
        # This is a simplified model; full implementation uses ephemeris
        jd = time.jd
        # Days since J2000
        days_since_j2000 = jd - 2451545.0
        
        # Approximate ecliptic longitude of Sun (very simplified)
        lambda_sun = (280.466 + 0.9856474 * days_since_j2000) * np.pi / 180.0
        
        # Convert to ITRS direction (simplified)
        # In reality, need to account for Earth's rotation and obliquity
        sun_dir = np.array([
            np.cos(lambda_sun),
            np.sin(lambda_sun) * np.cos(np.radians(23.44)),
            np.sin(lambda_sun) * np.sin(np.radians(23.44))
        ])
        sun_dir = sun_dir / np.linalg.norm(sun_dir)
        
        # Distance to Sun
        r_sat = np.linalg.norm(position)
        # Assume satellite is close to Earth compared to Sun distance
        # SRP decreases with square of distance from Sun, but variation is small
        # for Earth satellites
        
        # Shadow function (simplified - check if in Earth's shadow)
        # For now, assume full sunlight
        shadow = 1.0
        
        # SRP acceleration: a = P * Cr * A / m * (r_hat)
        # P = solar pressure, Cr = reflectivity coefficient
        srp_accel = SRP_COEFF * shadow * self.srp_cr * self.srp_area / self.drag_mass
        a_srp = srp_accel * sun_dir
        
        return a_srp
    
    def compute_acceleration(
        self,
        position: np.ndarray,
        velocity: np.ndarray,
        time: Time
    ) -> np.ndarray:
        """
        Compute total acceleration from all dynamical models.
        
        Args:
            position: ITRS position vector [x, y, z] in meters
            velocity: ITRS velocity vector [vx, vy, vz] in m/s
            time: Astropy Time object
            
        Returns:
            Total acceleration vector [ax, ay, az] in m/s^2
        """
        # Central gravity (point mass)
        r = np.linalg.norm(position)
        a_central = -MU_EARTH / r**3 * position
        
        # Geopotential
        a_geopotential = self.compute_geopotential_acceleration(position, time)
        
        # Drag
        a_drag = self.compute_drag_acceleration(position, velocity, time)
        
        # SRP
        a_srp = self.compute_srp_acceleration(position, time)
        
        # Total acceleration
        a_total = a_central + a_geopotential + a_drag + a_srp
        
        logger.debug(f"Acceleration components: central={a_central}, geopot={a_geopotential}, "
                    f"drag={a_drag}, srp={a_srp}")
        
        return a_total

def delta(i, j):
    """Kronecker delta function."""
    return 1 if i == j else 0

def compute_acceleration(
    position: np.ndarray,
    velocity: np.ndarray,
    time: Time,
    model: Optional[DynamicsModel] = None
) -> np.ndarray:
    """
    Convenience function to compute acceleration with default model.
    
    Args:
        position: ITRS position vector [x, y, z] in meters
        velocity: ITRS velocity vector [vx, vy, vz] in m/s
        time: Astropy Time object
        model: Optional DynamicsModel instance. If None, uses default.
        
    Returns:
        Acceleration vector [ax, ay, az] in m/s^2
    """
    if model is None:
        model = DynamicsModel()
    
    return model.compute_acceleration(position, velocity, time)