"""
Interface definitions for Voronoi-based nearest-neighbor detection.

This module defines the abstract interface (stub) for Voronoi neighbor
calculation, which is implemented concretely in `ingest.py` (T013/T016)
using `scipy.spatial.Voronoi`.

This stub ensures type consistency and separation of concerns between
the interface definition and the concrete implementation.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Optional, Any
import numpy as np

from .models import AtomicSnapshot


class IVoronoiNeighborFinder(ABC):
    """
    Abstract interface for finding nearest neighbors using Voronoi tessellation.

    This interface defines the contract for classes that compute atomic
    neighbors based on geometric proximity, handling periodic boundary
    conditions (PBC) as required for disordered alloy simulations.

    Implementations (e.g., in `ingest.py`) must handle:
    - Input: Atomic coordinates and species from an `AtomicSnapshot`.
    - Output: A mapping of atom indices to their neighbor indices.
    - PBC: Correct handling of periodic boundaries if applicable.
    """

    @abstractmethod
    def find_neighbors(
        self,
        snapshot: AtomicSnapshot,
        pbc: Optional[Tuple[bool, bool, bool]] = None
    ) -> Dict[int, List[int]]:
        """
        Compute nearest neighbors for all atoms in the snapshot.

        Args:
            snapshot: The atomic snapshot containing positions and species.
            pbc: Optional tuple indicating periodicity in x, y, z.
                If None, defaults to (True, True, True) for periodic systems.

        Returns:
            A dictionary mapping atom index (int) to a list of neighbor indices (List[int]).
            Only neighbors connected via Voronoi facets are included.

        Raises:
            VoronoiFailure: If the Voronoi tessellation cannot be computed
                (e.g., collinear points, singularities).
            DataAvailabilityError: If the snapshot is empty or malformed.
        """
        pass

    @abstractmethod
    def get_voronoi_vertices(
        self,
        snapshot: AtomicSnapshot,
        pbc: Optional[Tuple[bool, bool, bool]] = None
    ) -> np.ndarray:
        """
        Retrieve the vertices of the Voronoi tessellation.

        Useful for debugging or visualization of the tessellation geometry.

        Args:
            snapshot: The atomic snapshot.
            pbc: Periodic boundary conditions tuple.

        Returns:
            Array of shape (N_vertices, 3) containing vertex coordinates.
        """
        pass