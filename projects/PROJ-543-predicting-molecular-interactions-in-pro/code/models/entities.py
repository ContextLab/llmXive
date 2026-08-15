"""
Molecular Graph Entity Classes for Protein-Ligand Interaction Prediction.

This module defines the core data structures representing molecular graphs,
incorporating 3D spatial coordinates, atomic properties, and interaction flags.
It addresses the steric constraints and hydration states highlighted in
recent research reviews by explicitly storing 3D coordinates and water flags.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from enum import Enum


class AtomType(Enum):
    """Enumeration of standard atom types found in protein-ligand complexes."""
    C = "C"
    N = "N"
    O = "O"
    S = "S"
    P = "P"
    H = "H"
    F = "F"
    CL = "Cl"
    BR = "Br"
    I = "I"
    METAL = "Metal"
    WATER_O = "O_W"  # Oxygen in water molecule
    WATER_H = "H_W"  # Hydrogen in water molecule
    UNKNOWN = "X"


@dataclass
class Atom:
    """
    Represents a single atom within the molecular graph.

    Attributes:
        index: Unique integer identifier for the atom within the graph.
        atom_type: The chemical element or type (e.g., 'C', 'O', 'Metal').
        coordinates_3d: 3D spatial coordinates [x, y, z] in Angstroms.
        charge: Partial atomic charge (float).
        hydrophobicity: Hydrophobicity score (float).
        is_water: Boolean flag indicating if this atom belongs to a water molecule.
        metadata: Dictionary for additional properties (e.g., residue name, chain ID).
    """
    index: int
    atom_type: AtomType
    coordinates_3d: List[float]
    charge: float = 0.0
    hydrophobicity: float = 0.0
    is_water: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if len(self.coordinates_3d) != 3:
            raise ValueError(f"coordinates_3d must be a list of 3 floats, got {len(self.coordinates_3d)}")
        # Ensure coordinates are numpy array for efficient math later
        self._coords_array = np.array(self.coordinates_3d, dtype=np.float32)

    @property
    def coords_array(self) -> np.ndarray:
        """Returns the coordinates as a numpy array."""
        return self._coords_array

    def distance_to(self, other: 'Atom') -> float:
        """Calculates Euclidean distance to another atom."""
        if not isinstance(other, Atom):
            raise TypeError("Distance can only be calculated between Atom instances")
        return float(np.linalg.norm(self._coords_array - other._coords_array))


@dataclass
class Edge:
    """
    Represents an interaction edge between two atoms.

    Attributes:
        source_index: Index of the source atom.
        target_index: Index of the target atom.
        edge_type: Type of interaction (e.g., 'covalent', 'hydrogen_bond', 'hydrophobic', 'water_mediated').
        distance: Distance between atoms in Angstroms.
        metadata: Additional edge properties.
    """
    source_index: int
    target_index: int
    edge_type: str
    distance: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.distance < 0:
            raise ValueError("Distance cannot be negative")


@dataclass
class MolecularGraph:
    """
    Represents the full molecular graph of a protein-ligand complex.

    This class encapsulates the heterogeneous graph structure including
    protein atoms, ligand atoms, and water molecules, along with their
    interactions. It serves as the primary input for the GNN models.

    Attributes:
        complex_id: Unique identifier for the complex (e.g., PDB ID).
        atoms: List of Atom objects.
        edges: List of Edge objects.
        water_flag: Boolean indicating if water-mediated interactions are present.
        resolution: Crystallographic resolution in Angstroms (if available).
        metadata: General metadata about the complex.
    """
    complex_id: str
    atoms: List[Atom] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)
    water_flag: bool = False
    resolution: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_atom(self, atom: Atom) -> None:
        """Adds an atom to the graph."""
        self.atoms.append(atom)

    def add_edge(self, edge: Edge) -> None:
        """Adds an edge to the graph."""
        self.edges.append(edge)

    def get_atom_by_index(self, index: int) -> Optional[Atom]:
        """Retrieves an atom by its index."""
        for atom in self.atoms:
            if atom.index == index:
                return atom
        return None

    def get_neighbors(self, atom_index: int, max_distance: Optional[float] = None) -> List[Tuple[Atom, Edge]]:
        """
        Retrieves all atoms connected to the given atom by an edge.

        Args:
            atom_index: The index of the source atom.
            max_distance: Optional filter to only return edges within this distance.

        Returns:
            List of tuples (neighbor_atom, edge_object).
        """
        neighbors = []
        for edge in self.edges:
            if edge.source_index == atom_index:
                neighbor = self.get_atom_by_index(edge.target_index)
                if neighbor:
                    if max_distance is None or edge.distance <= max_distance:
                        neighbors.append((neighbor, edge))
            elif edge.target_index == atom_index:
                neighbor = self.get_atom_by_index(edge.source_index)
                if neighbor:
                    if max_distance is None or edge.distance <= max_distance:
                        neighbors.append((neighbor, edge))
        return neighbors

    def filter_by_resolution(self, max_resolution: float) -> bool:
        """
        Checks if the complex meets the resolution threshold.

        Args:
            max_resolution: Maximum allowed resolution in Angstroms.

        Returns:
            True if the complex is valid (resolution <= max_resolution), False otherwise.
            If resolution is not set, returns True (assumes valid).
        """
        if self.resolution is None:
            return True
        return self.resolution <= max_resolution

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the graph to a dictionary for JSON/YAML export."""
        return {
            "complex_id": self.complex_id,
            "water_flag": self.water_flag,
            "resolution": self.resolution,
            "atom_count": len(self.atoms),
            "edge_count": len(self.edges),
            "atoms": [
                {
                    "index": a.index,
                    "type": a.atom_type.value,
                    "coords": a.coordinates_3d,
                    "charge": a.charge,
                    "is_water": a.is_water
                }
                for a in self.atoms
            ],
            "edges": [
                {
                    "source": e.source_index,
                    "target": e.target_index,
                    "type": e.edge_type,
                    "distance": e.distance
                }
                for e in self.edges
            ]
        }

    def validate(self) -> List[str]:
        """
        Validates the graph structure against basic constraints.

        Returns:
            List of error messages. Empty if valid.
        """
        errors = []
        atom_indices = set()

        # Check for unique atom indices
        for atom in self.atoms:
            if atom.index in atom_indices:
                errors.append(f"Duplicate atom index found: {atom.index}")
            atom_indices.add(atom.index)

        # Check edge consistency
        for edge in self.edges:
            if edge.source_index not in atom_indices:
                errors.append(f"Edge {edge} references non-existent source index {edge.source_index}")
            if edge.target_index not in atom_indices:
                errors.append(f"Edge {edge} references non-existent target index {edge.target_index}")
            if edge.distance <= 0:
                errors.append(f"Edge {edge} has invalid distance: {edge.distance}")

        # Check resolution constraint if set
        if self.resolution is not None and self.resolution <= 0:
            errors.append(f"Invalid resolution: {self.resolution}")

        return errors