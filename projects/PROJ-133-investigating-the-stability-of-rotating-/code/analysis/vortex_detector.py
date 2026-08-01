"""
Vortex detection algorithms for Bose-Einstein Condensate simulations.

This module implements phase-winding based vortex detection to identify
quantized vortices in the wavefunction.
"""
import numpy as np
from typing import List, Tuple, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_phase_winding(psi_block: np.ndarray) -> float:
    """
    Calculate the phase winding around a 2x2 cell of the wavefunction.

    This function computes the line integral of the phase gradient around
    the perimeter of a 2x2 cell to detect vortices.

    Args:
        psi_block: A 2x2 complex numpy array representing the wavefunction
                   at four grid points.

    Returns:
        The total phase winding (in radians) around the cell.
        Values close to 2*pi indicate a +1 vortex.
        Values close to -2*pi indicate a -1 vortex (antivortex).
    """
    if psi_block.shape != (2, 2):
        raise ValueError("psi_block must be a 2x2 array")

    # Extract phases
    phases = np.angle(psi_block)

    # Unwrap phases to handle discontinuities
    # We need to unwrap along the path: 00 -> 01 -> 11 -> 10 -> 00
    p00, p01 = phases[0, 0], phases[0, 1]
    p11, p10 = phases[1, 1], phases[1, 0]

    # Calculate differences along the path
    # Path: (0,0) -> (0,1) -> (1,1) -> (1,0) -> (0,0)
    # Note: indices are [row, col] -> [y, x]
    # (0,0) is top-left, (0,1) is top-right, etc.
    
    d1 = p01 - p00
    d2 = p11 - p01
    d3 = p10 - p11
    d4 = p00 - p10

    # Unwrap differences to be in [-pi, pi]
    def unwrap_diff(diff):
        while diff > np.pi:
            diff -= 2 * np.pi
        while diff < -np.pi:
            diff += 2 * np.pi
        return diff

    winding = unwrap_diff(d1) + unwrap_diff(d2) + unwrap_diff(d3) + unwrap_diff(d4)

    return winding


def detect_vortices_phase_winding(psi: np.ndarray, dx: float = 1.0) -> List[Tuple[float, float, int]]:
    """
    Detect vortices in a 2D wavefunction using the phase winding method.

    This algorithm iterates over all 2x2 cells in the grid, calculates the
    phase winding around each cell, and identifies vortices where the
    winding is close to +/- 2*pi.

    Args:
        psi: 2D complex numpy array representing the wavefunction.
        dx: Grid spacing (assumed uniform in both x and y).

    Returns:
        A list of tuples (x, y, charge) representing detected vortices.
        charge is +1 for vortices and -1 for antivortices.
        Coordinates are in physical units based on dx.
    """
    if psi.ndim != 2:
        raise ValueError("psi must be a 2D array")

    rows, cols = psi.shape
    vortices = []

    # Iterate over 2x2 cells
    # A 2x2 cell is defined by corners (i, j), (i, j+1), (i+1, j+1), (i+1, j)
    for i in range(rows - 1):
        for j in range(cols - 1):
            # Extract the 2x2 block
            block = psi[i:i+2, j:j+2]

            # Calculate phase winding
            winding = calculate_phase_winding(block)

            # Check for vortex (winding close to 2*pi or -2*pi)
            # We use a threshold to account for numerical noise
            if abs(abs(winding) - 2 * np.pi) < 0.5:  # Threshold of 0.5 radians
                # Determine charge
                charge = 1 if winding > 0 else -1

                # Calculate position (center of the 2x2 cell)
                # Assuming grid starts at 0 for simplicity, or we can pass an offset
                x = (j + 0.5) * dx
                y = (i + 0.5) * dx

                vortices.append((x, y, charge))

    return vortices


def detect_vortices_density(psi: np.ndarray, dx: float = 1.0) -> float:
    """
    Calculate the vortex density (vortices per unit area) in the wavefunction.

    Args:
        psi: 2D complex numpy array representing the wavefunction.
        dx: Grid spacing.

    Returns:
        Vortex density (number of vortices / total area).
    """
    vortices = detect_vortices_phase_winding(psi, dx)
    total_area = (psi.shape[0] * dx) * (psi.shape[1] * dx)
    
    if total_area == 0:
        return 0.0
    
    return len(vortices) / total_area