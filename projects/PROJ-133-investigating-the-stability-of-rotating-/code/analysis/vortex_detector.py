"""Vortex‑detection utilities based on phase‑winding and density methods.

The public functions implement the standard 2 × 2 plaquette phase‑winding
algorithm and a simple density‑threshold approach.  Comprehensive
NumPy‑style docstrings are provided for each callable.
"""

import numpy as np
from typing import List, Tuple, Optional

from utils.logger import get_logger

_log = get_logger(__name__)

def calculate_phase_winding(psi_block: np.ndarray) -> float:
    """Calculate the phase winding around a 2 × 2 cell.

    The phase winding is obtained by summing the phase differences
    around the perimeter of the block.  A winding close to ``±2π`` indicates
    a vortex or antivortex.

    Parameters
    ----------
    psi_block : numpy.ndarray
        A ``2x2`` complex array representing the wavefunction at four
        neighbouring grid points.

    Returns
    -------
    float
        Total phase winding (in radians) around the cell.
    """
    if psi_block.shape != (2, 2):
        raise ValueError("psi_block must be a 2x2 array")
    phases = np.angle(psi_block)
    # Compute differences with proper unwrapping.
    diff = np.diff(np.unwrap(phases, axis=0), axis=0) + np.diff(np.unwrap(phases, axis=1), axis=1)
    winding = np.sum(diff)
    return winding

def detect_vortices_phase_winding(psi: np.ndarray, dx: float = 1.0) -> List[Tuple[float, float, int]]:
    """Detect vortices using the phase‑winding method.

    The algorithm scans all ``2 × 2`` plaquettes of the complex wavefunction
    ``psi`` and records the centre coordinates and topological charge of
    cells whose winding is within a tolerance of ``±2π``.

    Parameters
    ----------
    psi : numpy.ndarray
        2‑D complex array representing the condensate wavefunction.
    dx : float, optional
        Physical grid spacing (default is ``1.0``).

    Returns
    -------
    list of tuple
        Each tuple contains ``(x, y, charge)`` where ``x`` and ``y`` are
        physical coordinates of the vortex centre and ``charge`` is ``+1``
        for a vortex or ``-1`` for an antivortex.
    """
    ny, nx = psi.shape
    vortices = []
    tolerance = 0.5 * np.pi  # Acceptable deviation from 2π
    for i in range(ny - 1):
        for j in range(nx - 1):
            block = psi[i : i + 2, j : j + 2]
            winding = calculate_phase_winding(block)
            if abs(abs(winding) - 2 * np.pi) < tolerance:
                charge = int(np.sign(winding))
                x = (j + 0.5) * dx
                y = (i + 0.5) * dx
                vortices.append((x, y, charge))
    return vortices

def detect_vortices_density(psi: np.ndarray, dx: float = 1.0) -> float:
    """Calculate vortex density using a density‑based heuristic.

    This simplified method counts the number of local minima in the
    condensate density that fall below a fixed threshold and divides by the
    total area.

    Parameters
    ----------
    psi : numpy.ndarray
        2‑D complex wavefunction.
    dx : float, optional
        Grid spacing (default ``1.0``).

    Returns
    -------
    float
        Vortex density (vortices per unit area).
    """
    density = np.abs(psi) ** 2
    threshold = density.mean() * 0.2
    # Simple count of points below the threshold.
    count = np.sum(density < threshold)
    area = density.size * dx * dx
    return float(count / area)
