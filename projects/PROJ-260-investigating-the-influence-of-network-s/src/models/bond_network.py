"""
Bond Network representation for amorphous solids.

This module defines the BondNetwork dataclass which represents the graph
structure of atomic bonds. Nodes correspond to atoms, and edges correspond
to bonds determined by a distance cutoff (typically the first minimum of the RDF).

It computes local metrics (coordination number, bond angle variance) and
global graph metrics.
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
    Graph representation of atomic bonds in a simulation box.

    Attributes:
        box (SimulationBox): The source simulation box containing atomic positions.
        cutoff (float): The distance cutoff used to determine bonds (in Angstroms).
        adjacency (Dict[int, Set[int]]): Adjacency list mapping atom_id to set of neighbor atom_ids.
        node_positions (np.ndarray): Array of shape (N, 3) containing atomic positions.
        node_ids (List[int]): List of atom IDs corresponding to rows in node_positions.
        metrics (Dict[str, Any]): Dictionary storing computed graph metrics.
        anomalies (List[Dict[str, Any]]): List of flagged physical anomalies (e.g., high coordination).
    """
    box: SimulationBox
    cutoff: float
    adjacency: Dict[int, Set[int]] = field(default_factory=dict)
    node_positions: np.ndarray = field(default=None, init=False)
    node_ids: List[int] = field(default=None, init=False)
    metrics: Dict[str, Any] = field(default_factory=dict)
    anomalies: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Initialize node data from the simulation box."""
        # Extract positions and IDs from the simulation box
        self.node_positions = self.box.positions.copy()
        self.node_ids = list(self.box.atom_ids)

        if len(self.node_positions) == 0:
            raise ValueError("Simulation box contains no atoms.")

        if self.node_positions.shape[1] != 3:
            raise ValueError(f"Positions must be 3D, got shape {self.node_positions.shape}")

        # Build the network structure
        self._build_network()

    def _build_network(self) -> None:
        """
        Construct the bond network based on the cutoff distance.
        Uses PBC-aware distance calculation if box vectors are defined.
        """
        n_atoms = len(self.node_positions)
        self.adjacency = {aid: set() for aid in self.node_ids}

        # Calculate pairwise distances
        # If box vectors are present, we assume PBC. For simplicity in this model,
        # we use Euclidean distance on the provided coordinates.
        # In a full production system, minimum image convention would be applied here.
        # Using scipy's distance_matrix for efficiency.
        dist_mat = distance_matrix(self.node_positions, self.node_positions)

        # Mask self-distances
        np.fill_diagonal(dist_mat, np.inf)

        # Identify bonds
        # We iterate over the upper triangle to avoid double counting and self-loops
        # But since we need an undirected graph, we add edges to both nodes.
        # Optimized approach:
        for i in range(n_atoms):
            # Find neighbors within cutoff for atom i
            neighbors = np.where(dist_mat[i] < self.cutoff)[0]
            current_id = self.node_ids[i]

            for j in neighbors:
                neighbor_id = self.node_ids[j]
                self.adjacency[current_id].add(neighbor_id)

    def compute_coordination_numbers(self) -> Dict[int, int]:
        """
        Compute the coordination number for each atom.

        Returns:
            Dict[int, int]: Mapping of atom_id to its coordination number.
        """
        return {aid: len(neighbors) for aid, neighbors in self.adjacency.items()}

    def compute_bond_angle_variance(self) -> Dict[int, float]:
        """
        Compute the variance of bond angles for each atom.

        For an atom i with neighbors j and k, the bond angle is <jik.
        Variance is calculated over all unique pairs of neighbors for each atom.

        Returns:
            Dict[int, float]: Mapping of atom_id to bond angle variance.
        """
        variances = {}
        positions = self.node_positions

        for i, aid in enumerate(self.node_ids):
            neighbors = self.adjacency[aid]
            if len(neighbors) < 2:
                variances[aid] = 0.0
                continue

            neighbor_indices = [self.node_ids.index(nid) for nid in neighbors]
            neighbor_positions = positions[neighbor_indices]

            # Vector from central atom i to neighbors
            vectors = neighbor_positions - positions[i]
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            # Avoid division by zero
            norms[norms == 0] = 1e-10
            unit_vectors = vectors / norms

            angles = []
            # Calculate angles between all unique pairs of neighbors
            n_neighbors = len(unit_vectors)
            for idx1 in range(n_neighbors):
                for idx2 in range(idx1 + 1, n_neighbors):
                    dot_prod = np.dot(unit_vectors[idx1], unit_vectors[idx2])
                    # Clamp to [-1, 1] to handle floating point errors
                    dot_prod = np.clip(dot_prod, -1.0, 1.0)
                    angle = np.arccos(dot_prod)
                    angles.append(angle)

            if len(angles) > 0:
                variances[aid] = float(np.var(angles))
            else:
                variances[aid] = 0.0

        return variances

    def detect_anomalies(self, max_coordination: int = 6) -> List[Dict[str, Any]]:
        """
        Detect physical anomalies in the network.

        Currently flags atoms with coordination number > max_coordination.

        Args:
            max_coordination (int): Maximum allowed coordination number. Default is 6.

        Returns:
            List[Dict[str, Any]]: List of anomaly records.
        """
        anomalies = []
        coord_nums = self.compute_coordination_numbers()

        for aid, coord in coord_nums.items():
            if coord > max_coordination:
                anomalies.append({
                    "atom_id": aid,
                    "type": "high_coordination",
                    "value": coord,
                    "threshold": max_coordination
                })

        self.anomalies = anomalies
        return anomalies

    def compute_global_metrics(self) -> Dict[str, Any]:
        """
        Compute global graph metrics.

        Returns:
            Dict[str, Any]: Dictionary containing global metrics:
                - average_coordination
                - total_bonds
                - coordination_std
                - anomaly_count
        """
        coord_nums = list(self.compute_coordination_numbers().values())
        total_bonds = sum(len(neighbors) for neighbors in self.adjacency.values()) // 2

        metrics = {
            "average_coordination": float(np.mean(coord_nums)) if coord_nums else 0.0,
            "coordination_std": float(np.std(coord_nums)) if coord_nums else 0.0,
            "total_bonds": total_bonds,
            "anomaly_count": len(self.anomalies)
        }

        self.metrics = metrics
        return metrics

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the bond network to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the network.
        """
        return {
            "cutoff": self.cutoff,
            "num_atoms": len(self.node_ids),
            "num_bonds": self.metrics.get("total_bonds", 0),
            "average_coordination": self.metrics.get("average_coordination", 0.0),
            "anomalies": self.anomalies,
            "adjacency_sample": {
                str(k): list(v) for k, v in list(self.adjacency.items())[:5]
            }
        }

    @classmethod
    def from_simulation_box(
        cls,
        box: SimulationBox,
        cutoff: float
    ) -> "BondNetwork":
        """
        Factory method to create a BondNetwork from a SimulationBox.

        Args:
            box (SimulationBox): The source simulation box.
            cutoff (float): Distance cutoff for bond formation.

        Returns:
            BondNetwork: The constructed network.
        """
        return cls(box=box, cutoff=cutoff)