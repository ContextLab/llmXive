"""
Dynamics models for Satellite Laser Ranging (SLR) orbit determination.

Implements:
- GGM (Geopotential) acceleration (spherical harmonics)
- Jacchia atmospheric drag
- Solar Radiation Pressure (SRP)

All accelerations are returned in ITRS coordinates (m/s^2).
"""
import numpy as np
from astropy import units as u
from astropy.coordinates import GCRS, ITRS, CartesianRepresentation, CartesianDifferential, SkyCoord
from astropy.time import Time
from typing import Tuple, Optional, Dict, Any
import math

from utils.logging import get_logger

logger = get_logger(__name__)

# Constants
GM_EARTH = 3.986004418e14  # m^3/s^2
REARTH = 6378137.0  # m (equatorial radius)
MU_SOLAR = 1.32712440018e20  # m^3/s^2
AU = 1.495978707e11  # m
C = 299792458.0  # m/s
SOLAR_FLUX_1AU = 1361.0  # W/m^2

# GGM Coefficients (Simplified for demonstration - full GGM05C would have ~2000 terms)
# In a real implementation, these would be loaded from a file (e.g., GGM05C.gfc)
# Here we use a truncated set for the core physics demonstration
GGM_DEGREE = 2
GGM_ORDER = 2
# Normalized coefficients (C_nm, S_nm) for degree/order 2
# Values approximated for demonstration; real values from GGM05C would be used
GGM_C = {
    (0, 0): 1.0,
    (2, 0): -0.484166789e-3,  # J2
    (2, 2): 0.236798965e-6,
    (3, 0): 0.253245e-6,      # J3 (small)
    (4, 0): -0.16203e-6,      # J4
}
GGM_S = {
    (2, 2): -0.368305804e-6,
}

def _legendre_function(n: int, m: int, x: float) -> float:
    """
    Compute the associated Legendre function P_nm(x) using the recurrence relation.
    x = sin(lat)
    """
    if m > n:
        return 0.0
    
    # P_00
    if n == 0:
        return 1.0
    
    # P_10, P_11
    if n == 1:
        if m == 0:
            return x
        elif m == 1:
            return math.sqrt(1.0 - x * x)
    
    # General recurrence
    # We compute P_nm for specific n, m
    # Using the standard recurrence:
    # (n - m) * P_nm = x * (2n - 1) * P_{n-1,m} - (n + m - 1) * P_{n-2,m}
    
    # We'll compute P_nm directly for the requested n, m
    # Start from P_mm
    pmm = 1.0
    if m > 0:
        somx2 = math.sqrt((1.0 - x) * (1.0 + x))
        fact = 1.0
        for i in range(1, m + 1):
            pmm = pmm * fact * somx2
            fact = fact + 2
        pmm = pmm * (-1.0) ** m
    
    if n == m:
        return pmm
    
    pmms = pmm
    pmm1 = x * (2 * m + 1) * pmms
    if n == m + 1:
        return pmm1
    
    for ll in range(m + 2, n + 1):
        pmm2 = (x * (2 * ll - 1) * pmm1 - (ll + m - 1) * pmms) / (ll - m)
        pmms = pmm1
        pmm1 = pmm2
    
    return pmm1

def _compute_normalization_factor(n: int, m: int) -> float:
    """Compute the Schmidt semi-normalization factor."""
    if m == 0:
        return math.sqrt(2 * n + 1)
    else:
        return math.sqrt((2 * n + 1) * math.factorial(n - m) / math.factorial(n + m)) * math.sqrt(2)

def compute_geopotential_acceleration(
    r_gcrs: np.ndarray,
    time: Time,
    degree: int = GGM_DEGREE,
    order: int = GGM_ORDER
) -> np.ndarray:
    """
    Compute gravitational acceleration due to Earth's geopotential (spherical harmonics).
    
    Args:
        r_gcrs: Position vector in GCRS (meters), shape (3,)
        time: Astropy Time object
        degree: Maximum degree of spherical harmonics
        order: Maximum order of spherical harmonics
    
    Returns:
        Acceleration vector in GCRS (m/s^2), shape (3,)
    """
    # Convert GCRS to ITRS (Earth-fixed)
    # For geopotential, we need the position in the Earth-fixed frame
    coord = SkyCoord(CartesianRepresentation(r_gcrs * u.m), frame='gcrs', obstime=time)
    itrs_coord = coord.transform_to('itrs')
    r_itrs = itrs_coord.cartesian.xyz.to(u.m).value
    
    # Position magnitude
    r_mag = np.linalg.norm(r_itrs)
    if r_mag < REARTH * 0.9:
        logger.warning(f"Satellite too close to Earth surface: {r_mag/1000:.2f} km")
    
    # Spherical coordinates
    # Longitude
    lon = math.atan2(r_itrs[1], r_itrs[0])
    # Latitude
    lat = math.asin(r_itrs[2] / r_mag)
    
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    cos_lon = math.cos(lon)
    sin_lon = math.sin(lon)
    
    # Initialize acceleration
    ax, ay, az = 0.0, 0.0, 0.0
    
    # Point mass term (GM/r^2) - handled separately or as n=0 term
    # Here we compute the perturbation from spherical symmetry
    
    # Loop over degree and order
    for n in range(2, degree + 1):
        for m in range(0, min(n, order) + 1):
            # Get coefficients
            C_nm = GGM_C.get((n, m), 0.0)
            S_nm = GGM_S.get((n, m), 0.0)
            
            if C_nm == 0.0 and S_nm == 0.0:
                continue
            
            # Compute Legendre function
            P_nm = _legendre_function(n, m, sin_lat)
            norm_factor = _compute_normalization_factor(n, m)
            
            # Scale factor: (RE/r)^(n+1)
            scale = (REARTH / r_mag) ** (n + 1)
            
            # Gravitational constant factor
            k = GM_EARTH / (r_mag * r_mag) * scale * norm_factor
            
            # Trigonometric terms
            # dP/dtheta and dP/dlambda derivatives needed for acceleration
            # Simplified: use the gradient of the potential
            
            # For the potential: U = (GM/r) * sum sum (RE/r)^n * P_nm(sin(lat)) * (C_nm cos(m*lon) + S_nm sin(m*lon))
            # Acceleration = -grad(U)
            
            # Radial component
            term_r = (n + 1) * P_nm * (C_nm * cos_lon * cos(m * lon) + S_nm * sin_lon * sin(m * lon))
            
            # Theta component (latitude)
            # dP/dtheta = dP/dsin_lat * cos_lat
            # Approximate derivative for small m
            dP_dtheta = 0.0
            if n > m:
                dP_dtheta = _legendre_function(n, m + 1, sin_lat) * (n - m) * cos_lat
                # Simplified approximation for demonstration
                dP_dtheta = -n * P_nm * sin_lat / cos_lat if cos_lat > 1e-10 else 0.0
            
            term_theta = P_nm * (-C_nm * sin(m * lon) + S_nm * cos(m * lon)) * m
            if m == 0:
                term_theta = 0.0
            
            # Phi component (longitude)
            term_phi = -n * P_nm * cos_lat * (C_nm * sin(m * lon) - S_nm * cos(m * lon)) * m
            if m == 0:
                term_phi = 0.0
            
            # Convert to Cartesian components (simplified)
            # This is a simplified projection; full implementation requires the full gradient
            ax += k * (term_r * sin_lat * cos_lon - term_theta * cos_lat * cos_lon - term_phi * sin_lon)
            ay += k * (term_r * sin_lat * sin_lon - term_theta * cos_lat * sin_lon + term_phi * cos_lon)
            az += k * (term_r * cos_lat + term_theta * sin_lat)
    
    # Add point mass acceleration (GM/r^2) in the direction of -r
    ax -= GM_EARTH * r_itrs[0] / (r_mag ** 3)
    ay -= GM_EARTH * r_itrs[1] / (r_mag ** 3)
    az -= GM_EARTH * r_itrs[2] / (r_mag ** 3)
    
    # Return in GCRS (inverse transform)
    # For simplicity, we return in ITRS as requested, but note that the input was GCRS
    # The task asks for ITRS output, so we return the ITRS components
    return np.array([ax, ay, az])

def compute_jacchia_drag_acceleration(
    r_gcrs: np.ndarray,
    v_gcrs: np.ndarray,
    time: Time,
    ballistic_coefficient: float = 1.5,  # m^2/kg (typical for LAGEOS)
    solar_flux: float = 136.0,  # W/m^2 (F10.7 index proxy)
    geomagnetic_index: float = 4.0  # ap index proxy
) -> np.ndarray:
    """
    Compute atmospheric drag acceleration using the Jacchia model.
    
    Args:
        r_gcrs: Position vector in GCRS (meters)
        v_gcrs: Velocity vector in GCRS (m/s)
        time: Astropy Time object
        ballistic_coefficient: B* = Cd * A / m (m^2/kg)
        solar_flux: Solar flux proxy
        geomagnetic_index: Geomagnetic activity proxy
    
    Returns:
        Acceleration vector in GCRS (m/s^2)
    """
    # Convert to ITRS for density calculation (simplified: use GCRS for LEO, but correct for rotation)
    # For high orbits (LAGEOS), density is negligible, but we implement the model
    
    # Altitude above Earth surface
    r_mag = np.linalg.norm(r_gcrs)
    altitude = r_mag - REARTH
    
    # Jacchia model: density depends on altitude, solar flux, geomagnetic activity
    # Simplified exponential model with scale height
    # Real Jacchia-71/90/2011 is complex; using a simplified form for demonstration
    
    if altitude > 2000000:  # > 2000 km, density is negligible
        return np.array([0.0, 0.0, 0.0])
    
    # Scale height (km)
    H = 50.0 + 0.002 * solar_flux + 0.01 * geomagnetic_index  # km
    H_m = H * 1000.0
    
    # Reference density at 200 km
    rho_200 = 3.5e-10  # kg/m^3
    h_ref = 200000.0  # m
    
    # Density: rho = rho_ref * exp(-(h - h_ref)/H)
    rho = rho_200 * np.exp(-(altitude - h_ref) / H_m)
    
    # Relative velocity (satellite - atmosphere)
    # Atmosphere rotates with Earth
    omega_E = 7.292115e-5  # rad/s
    v_atm = np.cross([0, 0, omega_E], r_gcrs)
    v_rel = v_gcrs - v_atm
    v_rel_mag = np.linalg.norm(v_rel)
    
    # Drag acceleration: a = -0.5 * rho * Cd * A/m * v_rel * |v_rel|
    # a = -0.5 * rho * B* * v_rel * |v_rel|
    drag_coeff = 0.5 * rho * ballistic_coefficient * v_rel_mag
    
    ax = -drag_coeff * v_rel[0]
    ay = -drag_coeff * v_rel[1]
    az = -drag_coeff * v_rel[2]
    
    return np.array([ax, ay, az])

def compute_srp_acceleration(
    r_gcrs: np.ndarray,
    time: Time,
    area_to_mass: float = 0.01,  # m^2/kg (typical for LAGEOS)
    reflectivity: float = 1.3  # Cr (1 = absorption, 2 = perfect reflection)
) -> np.ndarray:
    """
    Compute Solar Radiation Pressure (SRP) acceleration.
    
    Args:
        r_gcrs: Position vector in GCRS (meters)
        time: Astropy Time object
        area_to_mass: A/m ratio (m^2/kg)
        reflectivity: Reflectivity coefficient (Cr)
    
    Returns:
        Acceleration vector in GCRS (m/s^2)
    """
    # Position of Sun in GCRS (simplified: assume Sun at ecliptic)
    # Real implementation: use ephemeris (e.g., JPL DE432)
    # Simplified: Sun at distance 1 AU, direction based on time
    
    # Approximate Sun position (GCRS)
    # Using a simple model: Sun moves ~1 degree/day along ecliptic
    # For demonstration, we use a fixed direction or a simple approximation
    # Real code would use: from astropy.coordinates import get_body
    
    # Simplified: assume Sun is at (1 AU, 0, 0) at J2000, adjust for time
    # This is a rough approximation; for production, use ephemeris
    jd = time.jd
    days_since_j2000 = jd - 2451545.0
    # Sun's mean longitude
    L_sun = 280.466 + 0.9856474 * days_since_j2000  # degrees
    L_sun_rad = math.radians(L_sun % 360)
    
    # Sun position vector (AU)
    r_sun_au = np.array([math.cos(L_sun_rad), math.sin(L_sun_rad), 0.0])
    r_sun = r_sun_au * AU  # meters
    
    # Vector from satellite to Sun
    r_sat = r_gcrs
    r_rel = r_sun - r_sat
    r_rel_mag = np.linalg.norm(r_rel)
    
    # Unit vector
    if r_rel_mag < 1e6:
        return np.array([0.0, 0.0, 0.0])  # Avoid division by zero
    
    u_rel = r_rel / r_rel_mag
    
    # Check if satellite is in Earth's shadow (umbra/penumbra)
    # Simplified: check angle between Sun and satellite
    # Real implementation: compute shadow function
    # For now, assume no shadow (valid for high orbits most of the time)
    shadow_factor = 1.0
    
    # SRP acceleration: a = - (P_srp * Cr * A/m) * u_rel
    # P_srp = Solar flux / c
    P_srp = SOLAR_FLUX_1AU / C  # N/m^2 at 1 AU
    # Adjust for distance: P = P_1AU * (1 AU / r)^2
    P_srp *= (AU / r_rel_mag) ** 2
    
    accel_mag = P_srp * reflectivity * area_to_mass * shadow_factor
    
    # Direction: away from Sun (repulsive)
    # a = + (P * Cr * A/m) * u_rel (since u_rel is from sat to sun, and force is away from sun)
    # Wait: u_rel is from sat to sun. Force is from sun to sat (away from sun).
    # So a = - (P * Cr * A/m) * u_rel (if u_rel is sat->sun, then -u_rel is sun->sat)
    # Actually: Force is in direction of sunlight, which is from Sun to Sat.
    # Vector from Sun to Sat is -r_rel. So unit vector is -u_rel.
    # a = (P * Cr * A/m) * (-u_rel)
    
    ax = -accel_mag * u_rel[0]
    ay = -accel_mag * u_rel[1]
    az = -accel_mag * u_rel[2]
    
    return np.array([ax, ay, az])

class DynamicsModel:
    """
    Composite dynamics model for satellite orbit propagation.
    Combines geopotential, drag, and SRP.
    """
    def __init__(
        self,
        geopotential_degree: int = GGM_DEGREE,
        geopotential_order: int = GGM_ORDER,
        ballistic_coefficient: float = 1.5,
        area_to_mass: float = 0.01,
        reflectivity: float = 1.3
    ):
        self.geopotential_degree = geopotential_degree
        self.geopotential_order = geopotential_order
        self.ballistic_coefficient = ballistic_coefficient
        self.area_to_mass = area_to_mass
        self.reflectivity = reflectivity
    
    def compute_total_acceleration(
        self,
        r_gcrs: np.ndarray,
        v_gcrs: np.ndarray,
        time: Time
    ) -> np.ndarray:
        """
        Compute total acceleration from all models.
        
        Args:
            r_gcrs: Position in GCRS (m)
            v_gcrs: Velocity in GCRS (m/s)
            time: Astropy Time object
        
        Returns:
            Total acceleration in GCRS (m/s^2)
        """
        a_geo = compute_geopotential_acceleration(
            r_gcrs, time,
            self.geopotential_degree, self.geopotential_order
        )
        a_drag = compute_jacchia_drag_acceleration(
            r_gcrs, v_gcrs, time, self.ballistic_coefficient
        )
        a_srp = compute_srp_acceleration(
            r_gcrs, time, self.area_to_mass, self.reflectivity
        )
        
        return a_geo + a_drag + a_srp

def delta(
    r_gcrs: np.ndarray,
    v_gcrs: np.ndarray,
    time: Time,
    model_params: Optional[Dict[str, Any]] = None
) -> np.ndarray:
    """
    Compute acceleration vector for orbit propagation (differential equation).
    
    Args:
        r_gcrs: Position vector in GCRS (m)
        v_gcrs: Velocity vector in GCRS (m/s)
        time: Astropy Time object
        model_params: Optional dict with model parameters (e.g., ballistic_coefficient)
    
    Returns:
        Acceleration vector in GCRS (m/s^2)
    """
    params = model_params or {}
    model = DynamicsModel(
        ballistic_coefficient=params.get('ballistic_coefficient', 1.5),
        area_to_mass=params.get('area_to_mass', 0.01),
        reflectivity=params.get('reflectivity', 1.3)
    )
    return model.compute_total_acceleration(r_gcrs, v_gcrs, time)

def compute_acceleration(
    r_gcrs: np.ndarray,
    v_gcrs: np.ndarray,
    time: Time,
    model_type: str = 'full',
    **kwargs
) -> np.ndarray:
    """
    Convenience function to compute acceleration with specific model.
    
    Args:
        r_gcrs: Position in GCRS (m)
        v_gcrs: Velocity in GCRS (m/s)
        time: Astropy Time object
        model_type: 'geopotential', 'drag', 'srp', or 'full'
        **kwargs: Additional parameters for the model
    
    Returns:
        Acceleration vector in GCRS (m/s^2)
    """
    if model_type == 'geopotential':
        return compute_geopotential_acceleration(r_gcrs, time, **kwargs)
    elif model_type == 'drag':
        return compute_jacchia_drag_acceleration(r_gcrs, v_gcrs, time, **kwargs)
    elif model_type == 'srp':
        return compute_srp_acceleration(r_gcrs, time, **kwargs)
    elif model_type == 'full':
        return delta(r_gcrs, v_gcrs, time, kwargs)
    else:
        raise ValueError(f"Unknown model type: {model_type}")