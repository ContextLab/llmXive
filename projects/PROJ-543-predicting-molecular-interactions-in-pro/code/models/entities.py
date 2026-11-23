from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from enum import Enum

class AtomType(Enum):
    """Enumeration of standard atom types found in protein-ligand complexes."""
    CARBON = "C"
    NITROGEN = "N"
    OXYGEN = "O"
    SULFUR = "S"
    PHOSPHORUS = "P"
    FLUORINE = "F"
    CHLORINE = "Cl"
    BROMINE = "Br"
    IODINE = "I"
    HYDROGEN = "H"
    METAL = "M"  # Generic metal placeholder
    OTHER = "X"

    @classmethod
    def from_symbol(cls, symbol: str) -> "AtomType":
        """Map a chemical symbol string to an AtomType enum."""
        symbol_upper = symbol.strip().upper()
        mapping = {
            "C": cls.CARBON,
            "N": cls.NITROGEN,
            "O": cls.OXYGEN,
            "S": cls.SULFUR,
            "P": cls.PHOSPHORUS,
            "F": cls.FLUORINE,
            "CL": cls.CHLORINE,
            "BR": cls.BROMINE,
            "I": cls.IODINE,
            "H": cls.HYDROGEN,
        }
        return mapping.get(symbol_upper, cls.OTHER)

@dataclass
class Atom:
    """
    Represents a single atom in the molecular graph.
    Includes 3D coordinates, chemical properties, and optional metadata.
    """
    index: int
    atom_type: AtomType
    element: str
    charge: float
    hydrophobicity: float
    coordinates: np.ndarray  # Shape (3,)
    residue_name: Optional[str] = None
    residue_id: Optional[int] = None
    chain_id: Optional[str] = None
    water_flag: bool = False  # True if this atom is part of a water-mediated interaction
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.coordinates, np.ndarray):
            self.coordinates = np.array(self.coordinates, dtype=np.float32)
        if self.coordinates.shape != (3,):
            raise ValueError(f"Coordinates must be a 1D array of shape (3,), got {self.coordinates.shape}")

    def distance_to(self, other: "Atom") -> float:
        """Calculate Euclidean distance to another atom."""
        return float(np.linalg.norm(self.coordinates - other.coordinates))

@dataclass
class Edge:
    """
    Represents a connection between two atoms in the molecular graph.
    Supports both covalent and non-covalent interactions.
    """
    source_index: int
    target_index: int
    edge_type: str  # 'covalent', 'hydrogen_bond', 'hydrophobic', 'water_mediated', 'steric'
    distance: float  # Explicit Euclidean distance in Angstroms
    interaction_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.distance, (int, float)):
            self.distance = float(self.distance)

@dataclass
class MolecularGraph:
    """
    Heterogeneous graph representing a protein-ligand complex.
    Contains nodes (Atoms) and edges (Interactions).
    """
    complex_id: str
    resolution: float
    nodes: List[Atom]
    edges: List[Edge]
    metadata: Dict[str, Any] = field(default_factory=dict)
    water_flag: bool = False  # Global flag if any water-mediated interactions exist in this complex

    def __post_init__(self):
        # Ensure nodes and edges are lists
        if not isinstance(self.nodes, list):
            self.nodes = list(self.nodes)
        if not isinstance(self.edges, list):
            self.edges = list(self.edges)
        
        # Validate node indices match the expected sequence
        for i, node in enumerate(self.nodes):
            if node.index != i:
                raise ValueError(f"Node index mismatch: expected {i}, got {node.index}")

    def get_node_by_index(self, index: int) -> Optional[Atom]:
        """Retrieve a node by its index."""
        if 0 <= index < len(self.nodes):
            return self.nodes[index]
        return None

    def get_neighbors(self, index: int) -> List[Tuple[int, Edge]]:
        """
        Get all neighbors of a node with their connecting edges.
        Returns a list of (neighbor_index, edge_object).
        """
        neighbors = []
        for edge in self.edges:
            if edge.source_index == index:
                neighbors.append((edge.target_index, edge))
            elif edge.target_index == index:
                neighbors.append((edge.source_index, edge))
        return neighbors

    def get_edge_between(self, i: int, j: int) -> Optional[Edge]:
        """Find the edge connecting two nodes, if it exists."""
        for edge in self.edges:
            if (edge.source_index == i and edge.target_index == j) or \
               (edge.source_index == j and edge.target_index == i):
                return edge
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the graph to a dictionary for serialization."""
        return {
            "complex_id": self.complex_id,
            "resolution": self.resolution,
            "water_flag": self.water_flag,
            "metadata": self.metadata,
            "nodes": [
                {
                    "index": n.index,
                    "atom_type": n.atom_type.value,
                    "element": n.element,
                    "charge": n.charge,
                    "hydrophobicity": n.hydrophobicity,
                    "coordinates": n.coordinates.tolist(),
                    "residue_name": n.residue_name,
                    "residue_id": n.residue_id,
                    "chain_id": n.chain_id,
                    "water_flag": n.water_flag,
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "source": e.source_index,
                    "target": e.target_index,
                    "type": e.edge_type,
                    "distance": e.distance,
                    "interaction_score": e.interaction_score,
                }
                for e in self.edges
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MolecularGraph":
        """Reconstruct a MolecularGraph from a dictionary."""
        nodes = []
        for n_data in data["nodes"]:
            nodes.append(Atom(
                index=n_data["index"],
                atom_type=AtomType(n_data["atom_type"]),
                element=n_data["element"],
                charge=n_data["charge"],
                hydrophobicity=n_data["hydrophobicity"],
                coordinates=np.array(n_data["coordinates"], dtype=np.float32),
                residue_name=n_data.get("residue_name"),
                residue_id=n_data.get("residue_id"),
                chain_id=n_data.get("chain_id"),
                water_flag=n_data.get("water_flag", False),
            ))
        
        edges = []
        for e_data in data["edges"]:
            edges.append(Edge(
                source_index=e_data["source"],
                target_index=e_data["target"],
                edge_type=e_data["type"],
                distance=e_data["distance"],
                interaction_score=e_data.get("interaction_score"),
            ))

        return cls(
            complex_id=data["complex_id"],
            resolution=data["resolution"],
            nodes=nodes,
            edges=edges,
            metadata=data.get("metadata", {}),
            water_flag=data.get("water_flag", False),
        )