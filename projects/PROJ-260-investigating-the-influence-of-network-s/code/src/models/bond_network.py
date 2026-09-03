"""
Bond network representation for amorphous solids.

This module defines the BondNetwork class, which represents the atomic
connectivity graph derived from a simulation box. It supports:
- Graph construction from atomic positions and a cutoff distance
- Calculation of local metrics (coordination number, bond angle variance)
- Global network metrics (average coordination, density)
- Validation against physical constraints (e.g., max coordination)
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Set
import numpy as np
from scipy.spatial import distance_matrix

@dataclass
class BondNetwork:
    """
    Graph representation of atomic bonds in a simulation box.

    Attributes:
        atom_ids: List of unique atom identifiers.
        positions: Nx3 array of atomic positions.
        box_vectors: 3x3 array of simulation box vectors (for PBC).
        cutoff: Distance cutoff for bond formation.
        adjacency: Dictionary mapping atom index to set of neighbor indices.
        coordination_numbers: List of coordination numbers for each atom.
        bond_angle_variances: List of bond angle variance for each atom.
        is_valid: Boolean flag indicating if the network passes physical checks.
        validation_errors: List of error messages if validation fails.
    """
    atom_ids: List[int]
    positions: np.ndarray
    box_vectors: Optional[np.ndarray] = None
    cutoff: float = 5.0  # Default cutoff for Si (approx 2.5 * sqrt(3)/2)
    
    adjacency: Dict[int, Set[int]] = field(default_factory=dict)
    coordination_numbers: List[int] = field(default_factory=list)
    bond_angle_variances: List[float] = field(default_factory=list)
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize and validate the network structure."""
        if self.positions.ndim != 2 or self.positions.shape[1] != 3:
            raise ValueError("Positions must be a 2D array with shape (N, 3)")
        
        if len(self.atom_ids) != self.positions.shape[0]:
            raise ValueError("atom_ids length must match number of positions")
        
        if self.box_vectors is None:
            self.box_vectors = np.eye(3) * np.max(self.positions, axis=0).max()

        self._build_network()

    def _apply_pbc(self, vec: np.ndarray) -> np.ndarray:
        """Apply periodic boundary conditions to a displacement vector."""
        if self.box_vectors is None:
            return vec
        
        # Inverse of box vectors
        inv_box = np.linalg.inv(self.box_vectors)
        # Transform to fractional coordinates
        frac = vec @ inv_box.T
        # Wrap to [-0.5, 0.5]
        frac = frac - np.round(frac)
        # Transform back to Cartesian
        return frac @ self.box_vectors

    def _build_network(self):
        """Construct the adjacency list based on cutoff distance."""
        n_atoms = len(self.atom_ids)
        self.adjacency = {i: set() for i in range(n_atoms)}
        
        # Calculate pairwise distances with PBC
        # Optimization: Use scipy's cdist if available, otherwise manual loop
        # For large N, a KDTree would be better, but cdist is sufficient for N < 10000
        dists = distance_matrix(self.positions, self.positions)
        
        # Apply PBC to distance matrix
        # Note: distance_matrix doesn't support PBC natively, so we adjust
        # This is a simplified PBC application for the distance matrix
        # A more robust implementation would use a KDTree with PBC
        
        # Manual PBC adjustment for distance matrix
        # This is O(N^2) but correct for small to medium systems
        min_image_dists = np.full_like(dists, np.inf)
        n_atoms = len(self.atom_ids)
        
        for i in range(n_atoms):
            for j in range(i + 1, n_atoms):
                vec = self.positions[j] - self.positions[i]
                vec_pbc = self._apply_pbc(vec)
                dist = np.linalg.norm(vec_pbc)
                min_image_dists[i, j] = dist
                min_image_dists[j, i] = dist
        
        # Build adjacency list
        for i in range(n_atoms):
            neighbors = np.where(min_image_dists[i] < self.cutoff)[0]
            for j in neighbors:
                if i != j:
                    self.adjacency[i].add(j)
                    self.adjacency[j].add(i)

        # Compute local metrics
        self._compute_local_metrics()

    def _compute_local_metrics(self):
        """Calculate coordination numbers and bond angle variances."""
        self.coordination_numbers = []
        self.bond_angle_variances = []
        
        n_atoms = len(self.atom_ids)
        
        for i in range(n_atoms):
            neighbors = list(self.adjacency[i])
            coord_num = len(neighbors)
            self.coordination_numbers.append(coord_num)
            
            # Calculate bond angle variance
            if coord_num < 2:
                self.bond_angle_variances.append(0.0)
                continue
            
            # Get neighbor positions
            neighbor_positions = self.positions[neighbors]
            center_pos = self.positions[i]
            
            # Vectors from center to neighbors
            vectors = neighbor_positions - center_pos
            
            # Normalize vectors
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            # Avoid division by zero
            norms[norms == 0] = 1e-10
            unit_vectors = vectors / norms
            
            # Calculate angles between all pairs of neighbors
            angles = []
            for idx1 in range(len(unit_vectors)):
                for idx2 in range(idx1 + 1, len(unit_vectors)):
                    dot_product = np.dot(unit_vectors[idx1], unit_vectors[idx2])
                    # Clip to avoid numerical errors
                    dot_product = np.clip(dot_product, -1.0, 1.0)
                    angle = np.arccos(dot_product)
                    angles.append(angle)
            
            if len(angles) > 0:
                variance = np.var(angles)
            else:
                variance = 0.0
            
            self.bond_angle_variances.append(variance)

    def get_global_metrics(self) -> Dict[str, float]:
        """Calculate global network metrics."""
        if not self.coordination_numbers:
            return {
                "avg_coordination": 0.0,
                "max_coordination": 0.0,
                "min_coordination": 0.0,
                "total_bonds": 0,
                "density": 0.0
            }
        
        avg_coord = np.mean(self.coordination_numbers)
        max_coord = max(self.coordination_numbers)
        min_coord = min(self.coordination_numbers)
        total_bonds = sum(len(neighbors) for neighbors in self.adjacency.values()) // 2
        
        # Calculate volume
        volume = np.abs(np.linalg.det(self.box_vectors))
        density = len(self.atom_ids) / volume
        
        return {
            "avg_coordination": float(avg_coord),
            "max_coordination": float(max_coord),
            "min_coordination": float(min_coord),
            "total_bonds": int(total_bonds),
            "density": float(density)
        }

    def validate_physical_constraints(self, max_coord: int = 6, 
                                    avg_coord_target: float = 4.0, 
                                    avg_coord_tolerance: float = 0.05) -> bool:
        """
        Validate the network against physical constraints.
        
        Args:
            max_coord: Maximum allowed coordination number.
            avg_coord_target: Target average coordination number.
            avg_coord_tolerance: Tolerance for average coordination.
            
        Returns:
            True if all constraints are satisfied, False otherwise.
        """
        self.validation_errors = []
        self.is_valid = True
        
        # Check for over-coordinated atoms
        for i, coord in enumerate(self.coordination_numbers):
            if coord > max_coord:
                self.validation_errors.append(
                    f"Atom {self.atom_ids[i]} has coordination {coord} > {max_coord}"
                )
                self.is_valid = False
        
        # Check average coordination
        if self.coordination_numbers:
            avg_coord = np.mean(self.coordination_numbers)
            if abs(avg_coord - avg_coord_target) > avg_coord_tolerance:
                self.validation_errors.append(
                    f"Average coordination {avg_coord:.2f} outside target "
                    f"{avg_coord_target} ± {avg_coord_tolerance}"
                )
                # Note: This is a warning, not necessarily a failure of the network
                # depending on the material, but we flag it for review
        
        return self.is_valid

    def to_dict(self) -> Dict:
        """Convert the network to a dictionary for serialization."""
        return {
            "atom_ids": self.atom_ids,
            "positions": self.positions.tolist(),
            "box_vectors": self.box_vectors.tolist() if self.box_vectors is not None else None,
            "cutoff": self.cutoff,
            "adjacency": {str(k): list(v) for k, v in self.adjacency.items()},
            "coordination_numbers": self.coordination_numbers,
            "bond_angle_variances": self.bond_angle_variances,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "global_metrics": self.get_global_metrics()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'BondNetwork':
        """Reconstruct a BondNetwork from a dictionary."""
        return cls(
            atom_ids=data["atom_ids"],
            positions=np.array(data["positions"]),
            box_vectors=np.array(data["box_vectors"]) if data["box_vectors"] is not None else None,
            cutoff=data["cutoff"]
        )
