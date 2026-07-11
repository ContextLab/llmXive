"""
IFS Instance Generator and Validation Module.

This module defines the core data structures for Iterated Function Systems (IFS)
and provides utilities for generating synthetic instances with controlled
Lipschitz constants.
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import numpy as np

@dataclass
class IFSInstance:
    """
    Represents a single Iterated Function System instance.

    Attributes:
        id: Unique identifier for this instance.
        maps: List of affine maps. Each map is a tuple of (2x2 matrix, 2x1 vector).
              Format: ((a, b, c, d), (tx, ty)) representing:
              x' = a*x + b*y + tx
              y' = c*x + d*y + ty
        lipschitz_target: The target Lipschitz constant for this IFS.
        grid_size: The number of points used for numerical validation.
        computed_lipschitz: The actual Lipschitz constant computed on the grid (optional).
        is_valid: Flag indicating if the instance passed validation checks.
    """
    id: str
    maps: List[Tuple[Tuple[float, float, float, float], Tuple[float, float]]]
    lipschitz_target: float
    grid_size: int
    computed_lipschitz: Optional[float] = None
    is_valid: bool = False