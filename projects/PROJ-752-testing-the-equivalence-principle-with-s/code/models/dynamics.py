"""
Dynamics Model for Satellite Orbit Determination.

Implements gravitational, drag, and solar radiation pressure models.
"""

import numpy as np
from astropy import units as u
from astropy.coordinates import GCRS, ITRS, CartesianRepresentation, CartesianDifferential, SkyCoord
from astropy.time import Time
from typing import Tuple, Optional, Dict, Any

from utils.logging import get_logger

logger = get_logger(__name__)

class DynamicsModel:
    """
    Container for the dynamical model of the satellite.
    """
    def __init__(self):
        self.GM = 3.986004418e14 # m^3/s^2
        self.R_earth = 6378137.0 # m
        self.differential_acceleration = 0.0 # m/s^2, for EP violation
    
    def set_differential_acceleration(self, ac: float) -> None:
        """Set the differential acceleration parameter."""
        self.differential_acceleration = ac

    def compute_acceleration(
        self,
        state: np.ndarray,
        time: Optional[Time] = None
    ) -> np.ndarray:
        """
        Compute the total acceleration vector for a given state.

        Args:
            state: State vector [x, y, z, vx, vy, vz] in meters and m/s.
            time: Astropy Time object (optional).

        Returns:
            Acceleration vector [ax, ay, az] in m/s^2.
        """
        pos = state[:3]
        r = np.linalg.norm(pos)
        
        # 1. Point mass gravity
        a_grav = -self.GM * pos / (r**3)
        
        # 2. Apply differential acceleration if set
        # This is a simplified model; in reality, it depends on composition and direction
        a_diff = np.zeros(3)
        if abs(self.differential_acceleration) > 1e-20:
            # Assume direction is radial for simplicity
            a_diff = self.differential_acceleration * (pos / r)
        
        # 3. Drag and SRP (simplified placeholders)
        a_drag = np.zeros(3)
        a_srp = np.zeros(3)
        
        # Total acceleration
        a_total = a_grav + a_diff + a_drag + a_srp
        
        return a_total

# Global instance or factory
def delta(ac: float) -> float:
    """Helper to compute delta parameter if needed."""
    return ac

def compute_acceleration(state: np.ndarray, time: Optional[Time] = None) -> np.ndarray:
    """
    Convenience function to compute acceleration.

    Args:
        state: State vector.
        time: Time object.

    Returns:
        Acceleration vector.
    """
    model = DynamicsModel()
    return model.compute_acceleration(state, time)
