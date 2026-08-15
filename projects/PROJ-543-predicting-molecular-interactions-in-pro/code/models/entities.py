"""
Molecular Graph Entity Definitions.

This module defines the core data structures for representing protein-ligand
complexes as heterogeneous graphs. It explicitly supports 3D spatial coordinates,
steric constraints, and hydration states as required by the project's physical
validation criteria.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

@dataclass
class Atom:
    """
    Represents a single atom node in the molecular graph.

    Attributes:
        atom_type: Chemical element symbol (e.g., 'C', 'N', 'O').
        charge: Formal charge of the atom.
        coordinates_3d: 3D spatial coordinates [x, y, z] in Angstroms.
        hydrophobicity: Hydrophobicity score (e.g., from a scale like Kyte-Doolittle).
        residue_name: Name of the parent residue (e.g., 'ALA', 'LIG').
        residue_id: Integer ID of the parent residue.
        chain_id: Chain identifier (e.g., 'A', 'B').
        is_water: Boolean flag indicating if this atom belongs to a water molecule.
    """
    atom_type: str
    charge: float
    coordinates_3d: List[float]
    hydrophobicity: float
    residue_name: str
    residue_id: int
    chain_id: str
    is_water: bool = False

    def __post_init__(self):
        if len(self.coordinates_3d) != 3:
            raise ValueError(f"coordinates_3d must be a list of 3 floats, got {len(self.coordinates_3d)}")
        if not isinstance(self.atom_type, str) or len(self.atom_type) == 0:
            raise ValueError("atom_type must be a non-empty string")

    def distance_to(self, other: 'Atom') -> float:
        """
        Calculates the Euclidean distance to another atom in 3D space.

        Args:
            other: Another Atom instance.

        Returns:
            Euclidean distance in Angstroms.
        """
        if len(self.coordinates_3d) != 3 or len(other.coordinates_3d) != 3:
            raise ValueError("Coordinates must be 3D for distance calculation")
        
        coords1 = np.array(self.coordinates_3d)
        coords2 = np.array(other.coordinates_3d)
        return float(np.linalg.norm(coords1 - coords2))

@dataclass
class Edge:
    """
    Represents an interaction edge between two atoms.

    Attributes:
        source_idx: Index of the source atom in the parent graph's atom list.
        target_idx: Index of the target atom in the parent graph's atom list.
        edge_type: Type of interaction (e.g., 'covalent', 'hydrogen_bond', 'hydrophobic', 'water_mediated').
        distance: Distance between atoms in Angstroms.
    """
    source_idx: int
    target_idx: int
    edge_type: str
    distance: float

    def __post_init__(self):
        if self.source_idx < 0 or self.target_idx < 0:
            raise ValueError("Atom indices must be non-negative")
        if self.distance < 0:
            raise ValueError("Distance cannot be negative")

@dataclass
class MolecularGraph:
    """
    Represents a protein-ligand complex as a heterogeneous graph.

    This class encapsulates the graph structure (atoms and interactions) along
    with metadata required for validation against high-resolution crystallographic
    data and steric constraints.

    Attributes:
        pdb_id: PDB identifier for the complex.
        resolution: Crystallographic resolution in Angstroms.
        atoms: List of Atom nodes.
        edges: List of Edge interactions.
        water_flag: Boolean indicating presence of water-mediated interactions.
        ligand_indices: List of indices in 'atoms' that belong to the ligand.
        protein_indices: List of indices in 'atoms' that belong to the protein.
    """
    pdb_id: str
    resolution: float
    atoms: List[Atom]
    edges: List[Edge]
    water_flag: bool = False
    ligand_indices: List[int] = field(default_factory=list)
    protein_indices: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.resolution <= 0:
            raise ValueError(f"Resolution must be positive, got {self.resolution}")
        if len(self.atoms) == 0:
            raise ValueError("MolecularGraph must contain at least one atom")
        
        # Validate indices are within bounds
        max_idx = len(self.atoms) - 1
        for idx in self.ligand_indices:
            if idx < 0 or idx > max_idx:
                raise ValueError(f"Ligand index {idx} out of bounds [0, {max_idx}]")
        for idx in self.protein_indices:
            if idx < 0 or idx > max_idx:
                raise ValueError(f"Protein index {idx} out of bounds [0, {max_idx}]")

        # Validate edges
        for edge in self.edges:
            if edge.source_idx > max_idx or edge.target_idx > max_idx:
                raise ValueError(f"Edge indices {edge.source_idx}, {edge.target_idx} out of bounds")

    def get_atoms_by_type(self, atom_type: str) -> List[Atom]:
        """Returns all atoms of a specific element type."""
        return [a for a in self.atoms if a.atom_type.upper() == atom_type.upper()]

    def get_water_atoms(self) -> List[Atom]:
        """Returns all atoms belonging to water molecules."""
        return [a for a in self.atoms if a.is_water]

    def get_non_water_atoms(self) -> List[Atom]:
        """Returns all atoms not belonging to water molecules."""
        return [a for a in self.atoms if not a.is_water]

    def get_interaction_edges(self, max_distance: float, edge_types: Optional[List[str]] = None) -> List[Edge]:
        """
        Filters edges based on distance and optional edge types.

        Args:
            max_distance: Maximum distance in Angstroms.
            edge_types: Optional list of allowed edge types.

        Returns:
            List of filtered Edge objects.
        """
        filtered = [e for e in self.edges if e.distance <= max_distance]
        if edge_types:
            filtered = [e for e in filtered if e.edge_type in edge_types]
        return filtered

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the graph to a dictionary compatible with the dataset schema.

        Returns:
            Dictionary representation of the graph.
        """
        return {
            "pdb_id": self.pdb_id,
            "resolution": self.resolution,
            "water_flag": self.water_flag,
            "atom_count": len(self.atoms),
            "edge_count": len(self.edges),
            "ligand_count": len(self.ligand_indices),
            "protein_count": len(self.protein_indices),
            "atoms": [
                {
                    "atom_type": a.atom_type,
                    "charge": a.charge,
                    "coordinates_3d": a.coordinates_3d,
                    "hydrophobicity": a.hydrophobicity,
                    "residue_name": a.residue_name,
                    "residue_id": a.residue_id,
                    "chain_id": a.chain_id,
                    "is_water": a.is_water
                }
                for a in self.atoms
            ],
            "edges": [
                {
                    "source_idx": e.source_idx,
                    "target_idx": e.target_idx,
                    "edge_type": e.edge_type,
                    "distance": e.distance
                }
                for e in self.edges
            ]
        }

    def validate_steric_constraints(self, cutoff: float = 2.0) -> bool:
        """
        Checks for steric clashes (atoms too close without being covalently bonded).

        Args:
            cutoff: Minimum allowed distance between non-bonded atoms.

        Returns:
            True if no clashes are detected, False otherwise.
        """
        # Simple O(N^2) check; for large graphs, a spatial index would be better.
        # This is sufficient for validation logic in the entity class.
        for i in range(len(self.atoms)):
            for j in range(i + 1, len(self.atoms)):
                # Skip if they are covalently bonded (distance usually < 1.6A for C-C)
                # We check if an edge of type 'covalent' exists
                is_bonded = False
                for e in self.edges:
                    if (e.source_idx == i and e.target_idx == j) or \
                       (e.source_idx == j and e.target_idx == i):
                        if e.edge_type == "covalent":
                            is_bonded = True
                            break
                
                if not is_bonded:
                    dist = self.atoms[i].distance_to(self.atoms[j])
                    if dist < cutoff:
                        return False
        return True