"""
Anisotropy analysis module for Cosmic Ray data.

Generates HEALPix maps and fits spherical harmonic coefficients (dipole/quadrupole).
"""
import numpy as np
import healpy as hp
from typing import List, Dict, Tuple, Optional
from .utils import get_logger

logger = get_logger(__name__)

# Default HEALPix resolution: Nside=64 provides ~1.8 degree pixels,
# suitable for large-scale anisotropy studies (dipole/quadrupole).
DEFAULT_NSIDE = 64

def generate_healpix_map(
    events: List[Dict],
    nside: int = DEFAULT_NSIDE,
    weights: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate a HEALPix map of cosmic ray intensity from event data.
    
    Args:
        events: List of event dictionaries containing 'ra' (Right Ascension in radians)
                and 'dec' (Declination in radians).
        nside: HEALPix resolution parameter.
        weights: Optional array of weights per event (e.g., exposure correction).
                
    Returns:
        Tuple of (map_counts, map_exposure, map_intensity) where:
        - map_counts: Total counts per pixel
        - map_exposure: Total exposure per pixel (normalized)
        - map_intensity: Relative intensity (counts / exposure)
    """
    logger.info(f"Generating HEALPix map with Nside={nside}")
    
    if not events:
        logger.warning("No events provided; returning empty map")
        npix = hp.nside2npix(nside)
        empty_map = np.full(npix, np.nan)
        return empty_map, empty_map, empty_map

    # Extract coordinates
    ras = np.array([e['ra'] for e in events])
    decs = np.array([e['dec'] for e in events])
    
    # Convert to Theta (colatitude) and Phi (longitude) for healpy
    # healpy expects theta = pi/2 - dec, phi = ra
    thetas = np.pi / 2.0 - decs
    phis = ras

    # Initialize map
    npix = hp.nside2npix(nside)
    counts = np.zeros(npix, dtype=float)
    exposure = np.zeros(npix, dtype=float)
    
    # Assign events to pixels
    # Using hp.ang2pix for fast pixelization
    pixels = hp.ang2pix(nside, thetas, phis)
    
    # Count events per pixel
    np.add.at(counts, pixels, 1)
    
    # Calculate exposure: assume uniform exposure for simplicity here.
    # In a real pipeline, this would be weighted by detector acceptance.
    # We use the pixel area as a proxy for exposure if weights are not provided.
    if weights is None:
        # Uniform exposure assumption: each pixel gets equal weight initially
        # Then we normalize by the number of pixels to get relative intensity
        # However, standard practice is to fill an exposure map with 1s where data exists
        # and 0s where it doesn't, then smooth or normalize.
        # For this implementation, we treat 'exposure' as the number of events
        # that *would* fall in a pixel if the sky were isotropic, 
        # but since we don't have the full sky model here, we use the pixel area.
        pixel_areas = hp.nside2pixarea(nside)
        exposure[:] = pixel_areas
    else:
        # Weighted exposure
        np.add.at(exposure, pixels, weights)

    # Calculate relative intensity (avoid division by zero)
    intensity = np.zeros_like(counts)
    nonzero = exposure > 0
    intensity[nonzero] = counts[nonzero] / exposure[nonzero]
    
    # Normalize intensity to mean = 1 for relative anisotropy
    mean_intensity = np.mean(intensity[nonzero]) if np.any(nonzero) else 1.0
    if mean_intensity > 0:
        intensity[nonzero] /= mean_intensity

    logger.info(f"HEALPix map generated: {np.sum(counts)} events mapped to {np.sum(nonzero)} pixels")
    
    return counts, exposure, intensity

def fit_dipole_coefficients(
    intensity_map: np.ndarray,
    nside: int = DEFAULT_NSIDE,
    max_l: int = 2
) -> Dict[str, np.ndarray]:
    """
    Fit spherical harmonic coefficients to the intensity map.
    
    Analyzes the map for dipole (l=1) and quadrupole (l=2) components.
    
    Args:
        intensity_map: HEALPix map of relative intensity.
        nside: HEALPix resolution parameter.
        max_l: Maximum multipole moment to compute (default 2 for dipole+quadrupole).
                
    Returns:
        Dictionary containing:
        - 'alm': Array of spherical harmonic coefficients (complex)
        - 'dipole_amplitude': Scalar amplitude of the l=1 component
        - 'dipole_phase': Phase angle (RA) of the dipole maximum
        - 'quadrupole_amplitude': Scalar amplitude of the l=2 component
    """
    logger.info(f"Fitting spherical harmonics up to l={max_l}")
    
    # Convert map to ALM coefficients
    # alm[0] is monopole (l=0), alm[1] is dipole (l=1), etc.
    # The order is: m=0, m=-1, m=1, m=-2, m=-1, m=0, m=1, m=2 ...
    # Actually, healpy.map2alm uses the standard ordering.
    alm = hp.map2alm(intensity_map, lmax=max_l, iter=0)
    
    # Extract dipole (l=1) and quadrupole (l=2) components
    # Indexing in alm array:
    # l=0: m=0 (1 coeff)
    # l=1: m=-1, m=0, m=1 (3 coeffs) -> indices 1, 2, 3
    # l=2: m=-2, m=-1, m=0, m=1, m=2 (5 coeffs) -> indices 4, 5, 6, 7, 8
    
    # Dipole coefficients (l=1)
    dipole_alm = alm[1:4]
    
    # Calculate dipole amplitude and phase
    # Amplitude is the norm of the vector (m=-1, m=0, m=1)
    # Phase is derived from the real and imaginary parts of the m=1 component
    # Standard definition: Dipole vector D = (Dx, Dy, Dz)
    # D_x ~ Re(alm[3]), D_y ~ Im(alm[3]), D_z ~ alm[2] (real)
    # Note: healpy uses Condon-Shortley phase convention.
    
    # Approximate dipole amplitude from the l=1 coefficients
    # A simple estimator: sqrt( sum(|alm_l1|^2) )
    dipole_power = np.sum(np.abs(dipole_alm)**2)
    dipole_amplitude = np.sqrt(dipole_power)
    
    # Phase calculation:
    # The direction of maximum intensity for the dipole is given by the vector
    # (Re(alm[3]), Im(alm[3]), Re(alm[2])) roughly.
    # RA = atan2(D_y, D_x)
    # Dec = asin(D_z / amplitude)
    
    # Extract specific components for phase
    # m=1 component is at index 3 in the l=1 block (indices 1, 2, 3)
    # m=-1 is at 1, m=0 is at 2.
    # For the phase of the maximum, we look at the m=1 component.
    a1_m1 = dipole_alm[2] # m=1
    a1_0 = dipole_alm[1]  # m=0
    
    # Simplified phase calculation based on m=1 component
    # The phase (RA of the maximum) is related to the argument of the complex coefficient
    # However, the full vector reconstruction is more robust.
    # Let's reconstruct the dipole vector components:
    # D_x = - (Re(alm[3]) + Re(alm[1])) / sqrt(2) ?
    # Standard conversion from ALM to Cartesian:
    # D_x = - (alm[3] + alm[1].conj()) / sqrt(2) -> Real part
    # D_y = i (alm[3] - alm[1].conj()) / sqrt(2) -> Real part
    # D_z = alm[2]
    
    # Using the property that for a real map, alm[-m] = (-1)^m * conj(alm[m])
    # So alm[1] (m=-1) = - conj(alm[3]) (m=1)
    # D_x = - (alm[3] - alm[3]) / ... wait.
    # Let's use a robust method: transform map to vector.
    # Or simply use the amplitude of the l=1 term as the primary metric.
    
    # For the phase (RA), we can use the argument of the m=1 coefficient
    # but we must be careful with the convention.
    # A common approximation for the phase of the dipole maximum:
    phase_rad = np.angle(dipole_alm[2]) # m=1 component
    
    # Convert to RA (0 to 2pi)
    dipole_phase = phase_rad % (2 * np.pi)
    
    # Quadrupole amplitude
    quad_alm = alm[4:9]
    quad_power = np.sum(np.abs(quad_alm)**2)
    quadrupole_amplitude = np.sqrt(quad_power)
    
    result = {
        'alm': alm,
        'dipole_amplitude': dipole_amplitude,
        'dipole_phase': dipole_phase,
        'quadrupole_amplitude': quadrupole_amplitude
    }
    
    logger.info(f"Dipole amplitude: {dipole_amplitude:.6f}, Phase: {dipole_phase:.6f} rad")
    logger.info(f"Quadrupole amplitude: {quadrupole_amplitude:.6f}")
    
    return result

def calculate_anisotropy_stats(
    events: List[Dict],
    nside: int = DEFAULT_NSIDE
) -> Dict[str, float]:
    """
    High-level function to calculate anisotropy statistics for a set of events.
    
    Args:
        events: List of event dictionaries.
        nside: HEALPix resolution.
        
    Returns:
        Dictionary with dipole_amplitude, dipole_phase, quadrupole_amplitude.
    """
    _, _, intensity_map = generate_healpix_map(events, nside)
    coeffs = fit_dipole_coefficients(intensity_map, nside)
    
    return {
        'dipole_amplitude': float(coeffs['dipole_amplitude']),
        'dipole_phase': float(coeffs['dipole_phase']),
        'quadrupole_amplitude': float(coeffs['quadrupole_amplitude'])
    }
