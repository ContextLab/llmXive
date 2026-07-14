"""
Chaos Game implementation for Iterated Function Systems (IFS).

This module provides the core simulation engine to approximate the invariant
measure of an IFS by iteratively applying random affine transformations.

It supports both contractive and non-contractive maps, with built-in divergence
detection and convergence classification based on Wasserstein-2 distance and
bounding box constraints.
"""

import numpy as np
from typing import Tuple, Dict, Any, List, Optional

# Import the dataclass defined in generators.py
from generators import IFSInstance


def run_chaos_game(
    ifs_instance: IFSInstance,
    iterations: int,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute the Chaos Game simulation for a given IFS instance.

    This function generates a set of points approximating the invariant measure
    of the IFS by iteratively applying randomly selected affine maps.

    Parameters
    ----------
    ifs_instance : IFSInstance
        The IFS instance containing the affine maps and configuration.
    iterations : int
        The number of iterations to run the simulation.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    dict
        A dictionary containing:
        - 'points': np.ndarray of shape (iterations, 2) containing the generated points.
        - 'escape_flag': bool indicating if any point escaped the bounding box.
        - 'convergence_status': str ('Converged' or 'Divergent').
        - 'w2_distance': float (approximate Wasserstein-2 distance, computed if converged).

    Raises
    ------
    ValueError
        If the IFS instance has no maps or iterations is non-positive.
    """
    ...