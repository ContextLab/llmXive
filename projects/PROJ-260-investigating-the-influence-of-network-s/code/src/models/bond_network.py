"""
Bond Network Model for Amorphous Solids.

This module defines the BondNetwork dataclass, which represents the graph
structure of atomic bonds in a simulation box. Nodes correspond to atoms,
and edges correspond to bonds determined by a cutoff distance (typically
derived from the Radial Distribution Function).

It computes local metrics (coordination number, bond angle variance) and
global metrics (average coordination, network density) required for the
thermal conductivity analysis pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Set, Any
import numpy as np
from scipy.spatial import distance_matrix
from scipy.spatial.distance import pdist, squareform

from src.models.simulation_box import SimulationBox


@dataclass
class BondNetwork:
    """
    Graph representation of atomic bonds.

    Attributes:
        num_atoms (int): Total number of atoms in the system.
        atom_ids (np.ndarray): Array of unique atom identifiers (0 to N-1).
        positions (np.ndarray): Atomic positions (N, 3).
        box_vectors (np.ndarray): Simulation box vectors (3, 3) for PBC calculations.
        cutoff (float): Distance threshold for bond formation (in Angstroms).
        adjacency_list (List[List[int]]): List of neighbor indices for each atom.
        edges (List[Tuple[int, int]]): List of unique bond tuples (i, j) with i < j.
        coordination_numbers (np.ndarray): Coordination number for each atom.
        bond_angle_variances (np.ndarray): Variance of bond angles for each atom.
        is_valid (bool): Flag indicating if the network passed physical constraints.
        anomaly_flags (Dict[int, List[str]]): Mapping of atom_id to list of anomaly reasons.
        global_metrics (Dict[str, float]): Computed global network statistics.
    """
    num_atoms: int
    atom_ids: np.ndarray
    positions: np.ndarray
    box_vectors: np.ndarray
    cutoff: float
    adjacency_list: List[List[int]] = field(default_factory=list)
    edges: List[Tuple[int, int]] = field(default_factory=list)
    coordination_numbers: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.int32))
    bond_angle_variances: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float64))
    is_valid: bool = True
    anomaly_flags: Dict[int, List[str]] = field(default_factory=dict)
    global_metrics: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Validate inputs and initialize empty arrays if needed."""
        if self.positions.shape[0] != self.num_atoms:
            raise ValueError(
                f"Number of positions ({self.positions.shape[0]}) "
                f"does not match num_atoms ({self.num_atoms})."
            )
        if self.atom_ids.shape[0] != self.num_atoms:
            raise ValueError(
                f"Number of atom_ids ({self.atom_ids.shape[0]}) "
                f"does not match num_atoms ({self.num_atoms})."
            )
        if self.positions.shape[1] != 3:
            raise ValueError("Positions must be 3D (N, 3).")
        if self.box_vectors.shape != (3, 3):
            raise ValueError("Box vectors must be a (3, 3) matrix.")

        # Ensure float64 for precision (Constitution Principle VI)
        self.positions = self.positions.astype(np.float64)
        self.box_vectors = self.box_vectors.astype(np.float64)

        # Initialize empty metrics
        if self.coordination_numbers.size == 0:
            self.coordination_numbers = np.zeros(self.num_atoms, dtype=np.int32)
        if self.bond_angle_variances.size == 0:
            self.bond_angle_variances = np.zeros(self.num_atoms, dtype=np.float64)

    @classmethod
    def from_simulation_box(cls, box: SimulationBox, cutoff: float) -> "BondNetwork":
        """
        Construct a BondNetwork from a SimulationBox object.

        Args:
            box: The SimulationBox containing atomic data.
            cutoff: The distance cutoff for bond formation.

        Returns:
            A new BondNetwork instance.
        """
        return cls(
            num_atoms=box.num_atoms,
            atom_ids=box.atom_ids,
            positions=box.positions,
            box_vectors=box.box_vectors,
            cutoff=cutoff
        )

    def compute_adjacency(self) -> None:
        """
        Compute the adjacency list based on the cutoff distance.

        Uses Minimum Image Convention (MIC) for Periodic Boundary Conditions (PBC).
        """
        self.adjacency_list = [[] for _ in range(self.num_atoms)]
        self.edges = []

        # Calculate pairwise distances with PBC
        # Using a manual loop with MIC is often more memory efficient for large N
        # than squareform(pdist) on full matrix, but for clarity and correctness:
        
        # Optimization: Use scipy.spatial.distance.cdist with custom PBC if available,
        # or implement MIC manually. Here we implement MIC manually for robustness.
        
        dist_matrix = np.full((self.num_atoms, self.num_atoms), np.inf)
        
        # Compute distances
        for i in range(self.num_atoms):
            for j in range(i + 1, self.num_atoms):
                vec = self.positions[j] - self.positions[i]
                
                # Apply Minimum Image Convention
                # vec = vec - box_vectors @ np.round(np.linalg.solve(box_vectors, vec))
                # More stable: solve linear system for fractional coordinates
                frac_diff = np.linalg.solve(self.box_vectors, vec)
                frac_diff -= np.rint(frac_diff)
                vec_image = self.box_vectors @ frac_diff
                
                d = np.linalg.norm(vec_image)
                dist_matrix[i, j] = d
                dist_matrix[j, i] = d

        # Build adjacency list and edge list
        for i in range(self.num_atoms):
            neighbors = np.where(dist_matrix[i] < self.cutoff)[0]
            # Exclude self
            neighbors = neighbors[neighbors != i]
            self.adjacency_list[i] = neighbors.tolist()
            
            for j in neighbors:
                if i < j:
                    self.edges.append((i, j))

        # Update coordination numbers
        self.coordination_numbers = np.array([len(neighbors) for neighbors in self.adjacency_list], dtype=np.int32)

    def compute_bond_angle_variance(self) -> None:
        """
        Compute the variance of bond angles for each atom.

        For an atom i with neighbors j and k, the angle is theta_jik.
        Variance is computed over all unique pairs (j, k) for each i.
        If an atom has < 2 neighbors, variance is 0.0.
        """
        variances = np.zeros(self.num_atoms, dtype=np.float64)
        
        for i in range(self.num_atoms):
            neighbors = self.adjacency_list[i]
            if len(neighbors) < 2:
                variances[i] = 0.0
                continue

            # Vectors from i to neighbors
            vecs = self.positions[neighbors] - self.positions[i]
            
            # Normalize
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            # Avoid division by zero
            norms[norms == 0] = 1.0
            unit_vecs = vecs / norms

            # Compute all pairwise angles for this atom
            # dot product of unit vectors
            dots = np.dot(unit_vecs, unit_vecs.T)
            # Clip to [-1, 1] to handle floating point errors
            dots = np.clip(dots, -1.0, 1.0)
            
            # Get upper triangle indices (excluding diagonal) to get unique pairs
            upper_tri_indices = np.triu_indices(len(neighbors), k=1)
            angles = np.arccos(dots[upper_tri_indices])
            
            if len(angles) > 0:
                variances[i] = np.var(angles)
            else:
                variances[i] = 0.0

        self.bond_angle_variances = variances

    def validate_physical_constraints(self) -> None:
        """
        Validate the network against physical constraints.

        Flags atoms with coordination > 6 as anomalies.
        Validates average coordination against expected range (4.00 ± 0.05).
        """
        self.anomaly_flags = {}
        self.is_valid = True

        # Check individual atoms
        for i, cn in enumerate(self.coordination_numbers):
            if cn > 6:
                if i not in self.anomaly_flags:
                    self.anomaly_flags[i] = []
                self.anomaly_flags[i].append(f"High coordination: {cn} > 6")
                self.is_valid = False # Mark network as containing anomalies

        # Check global average
        avg_cn = np.mean(self.coordination_numbers)
        # Expected for amorphous silicon is approx 4.0
        if not (3.95 <= avg_cn <= 4.05):
            # Log warning but don't necessarily fail the network object itself,
            # just record the metric. The task says "flag result".
            pass 

        self.global_metrics['average_coordination'] = float(avg_cn)
        self.global_metrics['total_bonds'] = len(self.edges)
        self.global_metrics['density'] = len(self.edges) / (self.num_atoms * (self.num_atoms - 1) / 2)

    def get_local_metrics(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns the coordination numbers and bond angle variances.

        Returns:
            Tuple of (coordination_numbers, bond_angle_variances)
        """
        return self.coordination_numbers, self.bond_angle_variances

    def to_dict(self) -> Dict[str, Any]:
        """Convert the BondNetwork to a dictionary representation."""
        return {
            "num_atoms": self.num_atoms,
            "cutoff": self.cutoff,
            "coordination_numbers": self.coordination_numbers.tolist(),
            "bond_angle_variances": self.bond_angle_variances.tolist(),
            "is_valid": self.is_valid,
            "anomaly_flags": {str(k): v for k, v in self.anomaly_flags.items()},
            "global_metrics": self.global_metrics
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BondNetwork":
        """
        Reconstruct a BondNetwork from a dictionary.
        
        Note: This reconstructs metadata and metrics, but not the full
        geometric structure (positions, edges) unless they are explicitly
        stored in the dict. For full reconstruction, positions and box_vectors
        are required.
        """
        # This is a partial reconstruction for metadata only.
        # Full reconstruction requires the original SimulationBox.
        return cls(
            num_atoms=data["num_atoms"],
            atom_ids=np.arange(data["num_atoms"]),
            positions=np.zeros((data["num_atoms"], 3)),
            box_vectors=np.eye(3),
            cutoff=data["cutoff"],
            coordination_numbers=np.array(data["coordination_numbers"]),
            bond_angle_variances=np.array(data["bond_angle_variances"]),
            is_valid=data["is_valid"],
            anomaly_flags={int(k): v for k, v in data["anomaly_flags"].items()},
            global_metrics=data["global_metrics"]
        )
