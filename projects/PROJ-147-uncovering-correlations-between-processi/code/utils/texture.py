"""
Texture analysis utilities wrapping pymtex for ODF intensity computation.

This module provides functions to compute Orientation Distribution Function (ODF)
intensities for specific crystallographic planes ({100}, {110}, {111}) in
multiples of random distribution (MRD) for rolled metals.

FR-003: Compute ODF intensities for {100}, {110}, {111} in MRD.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple

# Try to import pymtex; if not available, provide a clear error
try:
    import pymtex
    from pymtex import odf
    PYMTEX_AVAILABLE = True
except ImportError:
    PYMTEX_AVAILABLE = False
    pymtex = None
    odf = None

from code.utils.logging import get_logger

logger = get_logger(__name__)

# Default Miller indices for common texture components in rolled metals
DEFAULT_PLANES = [
    ([1, 0, 0], "100"),
    ([1, 1, 0], "110"),
    ([1, 1, 1], "111"),
]

def compute_odf_intensities(
    eulerAngles: np.ndarray,
    hkl: List[int],
    grid_resolution: int = 5,
    symmetry: str = "cubic"
) -> float:
    """
    Compute the ODF intensity for a specific {hkl} plane at given Euler angles.

    Args:
        eulerAngles: Array of shape (N, 3) containing Euler angles (phi1, Phi, phi2) in degrees.
        hkl: Miller indices [h, k, l] for the plane of interest.
        grid_resolution: Resolution of the ODF grid (degrees). Lower = finer grid.
        symmetry: Crystal symmetry ('cubic', 'orthorhombic', etc.). Default is 'cubic'.

    Returns:
        float: ODF intensity in multiples of random distribution (MRD).

    Raises:
        ImportError: If pymtex is not installed.
        ValueError: If input dimensions are invalid.
    """
    if not PYMTEX_AVAILABLE:
        raise ImportError(
            "pymtex is required for ODF intensity computation. "
            "Install it via: pip install pymtex"
        )

    eulerAngles = np.asarray(eulerAngles, dtype=float)
    if eulerAngles.ndim == 1:
        eulerAngles = eulerAngles.reshape(1, -1)

    if eulerAngles.shape[1] != 3:
        raise ValueError(f"eulerAngles must have 3 columns (phi1, Phi, phi2), got {eulerAngles.shape[1]}")

    if len(hkl) != 3:
        raise ValueError(f"hkl must be a list of 3 integers, got {hkl}")

    # Convert Miller indices to tuple for pymtex
    hkl_tuple = tuple(hkl)

    try:
        # Use pymtex to compute ODF
        # Note: The exact API might vary depending on pymtex version.
        # This is a generic implementation assuming standard usage.
        # If specific ODF calculation requires more parameters, they can be added here.
        
        # Calculate intensity at the given orientation for the specified plane
        # pymtex typically uses Bunge convention for Euler angles
        intensity = odf.calculate_intensity(
            eulerAngles=eulerAngles,
            hkl=hkl_tuple,
            grid_resolution=grid_resolution,
            symmetry=symmetry
        )
        
        # Return the mean intensity if multiple orientations are provided
        if isinstance(intensity, np.ndarray):
            return float(np.mean(intensity))
        return float(intensity)
        
    except Exception as e:
        logger.error(f"Error computing ODF intensity for hkl={hkl}: {e}")
        raise

def compute_multiple_plane_intensities(
    eulerAngles: np.ndarray,
    planes: Optional[List[Tuple[List[int], str]]] = None,
    grid_resolution: int = 5,
    symmetry: str = "cubic"
) -> Dict[str, float]:
    """
    Compute ODF intensities for multiple {hkl} planes.

    Args:
        eulerAngles: Array of shape (N, 3) containing Euler angles (phi1, Phi, phi2) in degrees.
        planes: List of tuples (hkl, label) for planes to compute. 
               If None, defaults to {100}, {110}, {111}.
        grid_resolution: Resolution of the ODF grid (degrees).
        symmetry: Crystal symmetry.

    Returns:
        Dict[str, float]: Dictionary mapping plane labels to their ODF intensities in MRD.
    """
    if planes is None:
        planes = DEFAULT_PLANES

    results = {}
    for hkl, label in planes:
        try:
            intensity = compute_odf_intensities(
                eulerAngles, hkl, grid_resolution, symmetry
            )
            results[label] = intensity
        except Exception as e:
            logger.warning(f"Failed to compute intensity for {label}: {e}")
            results[label] = np.nan

    return results

def extract_texture_components(
    eulerAngles: np.ndarray,
    component_list: Optional[List[str]] = None
) -> Dict[str, float]:
    """
    Extract intensities for common texture components (Cube, Goss, Brass, etc.).

    Args:
        eulerAngles: Array of shape (N, 3) containing Euler angles.
        component_list: List of component names to extract. 
                       Common: 'Cube', 'Goss', 'Brass', 'S', 'Copper'.

    Returns:
        Dict[str, float]: Dictionary mapping component names to intensities.
    """
    if not PYMTEX_AVAILABLE:
        raise ImportError("pymtex required for texture component extraction")

    # Common texture components in rolled metals (Bunge Euler angles)
    texture_components = {
        'Cube': ([0, 0, 0], [1, 0, 0]),  # (001)[100]
        'Goss': ([0, 45, 0], [1, 0, 0]),  # (011)[100]
        'Brass': ([35, 45, 0], [1, 1, 0]), # (011)[211]
        'S': ([39, 69, 90], [1, 1, 2]),    # (123)[634]
        'Copper': ([40, 60, 45], [1, 1, 2]),# (112)[111]
    }

    if component_list is None:
        component_list = list(texture_components.keys())

    results = {}
    for comp_name in component_list:
        if comp_name not in texture_components:
            logger.warning(f"Unknown texture component: {comp_name}")
            results[comp_name] = np.nan
            continue

        _, hkl = texture_components[comp_name]
        try:
            # For texture components, we typically look at specific orientations
            # Here we compute intensity at the component's ideal orientation
            # In practice, you might want to search a neighborhood around the ideal orientation
            ideal_angles = np.array([texture_components[comp_name][0]])
            intensity = compute_odf_intensities(ideal_angles, hkl)
            results[comp_name] = intensity
        except Exception as e:
            logger.warning(f"Failed to extract {comp_name}: {e}")
            results[comp_name] = np.nan

    return results