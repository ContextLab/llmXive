"""
Pydantic models for data validation and schema definition.

Defines the core data structures for atomic snapshots and defect networks
used throughout the heat transport analysis pipeline.
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
import numpy as np
from .utils import DataAvailabilityError, VoronoiFailure

class AtomicSnapshot(BaseModel):
    """
    Represents a single snapshot of atomic positions and species.
    
    Attributes:
        snapshot_id: Unique identifier for the snapshot
        species: List of species labels (e.g., ['Cu', 'Ni'])
        coordinates: List of [x, y, z] coordinates for each atom
        box_size: Simulation box dimensions [Lx, Ly, Lz]
        thermal_conductivity_W_m_K: Target property (optional)
        metadata: Additional key-value pairs
    """
    snapshot_id: str = Field(..., description="Unique identifier for the snapshot")
    species: List[str] = Field(..., description="List of species labels (e.g., ['Cu', 'Ni'])")
    coordinates: List[List[float]] = Field(..., description="List of [x, y, z] coordinates")
    box_size: List[float] = Field(..., description="Simulation box dimensions [Lx, Ly, Lz]")
    thermal_conductivity_W_m_K: Optional[float] = Field(None, description="Target property")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('coordinates')
    @classmethod
    def validate_coordinates(cls, v: List[List[float]]) -> List[List[float]]:
        if not v:
            raise ValueError("Coordinates list cannot be empty")
        if not all(len(coord) == 3 for coord in v):
            raise ValueError("Each coordinate must be a list of 3 floats [x, y, z]")
        return v

    @field_validator('species')
    @classmethod
    def validate_species(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Species list cannot be empty")
        if len(v) != len(v): # Redundant but explicit check
            raise ValueError("Species list must match coordinate count")
        return v

    @field_validator('box_size')
    @classmethod
    def validate_box_size(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError("Box size must be a list of 3 floats [Lx, Ly, Lz]")
        if any(dim <= 0 for dim in v):
            raise ValueError("Box dimensions must be positive")
        return v

    @model_validator(mode='after')
    def check_consistency(self) -> 'AtomicSnapshot':
        if len(self.species) != len(self.coordinates):
            raise DataAvailabilityError(
                f"Species count ({len(self.species)}) does not match "
                f"coordinate count ({len(self.coordinates)}) for snapshot {self.snapshot_id}"
            )
        return self

    @property
    def n_atoms(self) -> int:
        """Return the number of atoms in the snapshot."""
        return len(self.coordinates)

    @property
    def n_species(self) -> int:
        """Return the number of unique species."""
        return len(set(self.species))

    def to_numpy(self) -> np.ndarray:
        """Convert coordinates to a numpy array for efficient computation."""
        return np.array(self.coordinates, dtype=np.float64)

    def get_species_mask(self, species_label: str) -> np.ndarray:
        """Return a boolean mask for atoms of a specific species."""
        return np.array([s == species_label for s in self.species], dtype=bool)

class DefectGraph(BaseModel):
    """
    Represents the graph derived from atomic neighbors.
    
    Nodes are atoms, edges connect nearest neighbors of mismatched species.
    
    Attributes:
        graph_id: Unique identifier for the graph
        snapshot_id: Reference to the source snapshot
        node_count: Number of atoms (nodes)
        edge_count: Number of mismatched neighbor pairs (edges)
        adjacency_list: Node ID to list of neighbor IDs
        node_attributes: Attributes for each node (e.g., species, position)
        metrics: Pre-computed graph metrics (to be filled by T020+)
    """
    graph_id: str = Field(..., description="Unique identifier for the graph")
    snapshot_id: str = Field(..., description="Reference to the source snapshot")
    node_count: int = Field(..., description="Number of atoms")
    edge_count: int = Field(..., description="Number of mismatched neighbor pairs")
    adjacency_list: Dict[str, List[str]] = Field(..., description="Node ID to list of neighbor IDs")
    node_attributes: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)

    @field_validator('adjacency_list')
    @classmethod
    def validate_adjacency(cls, v: Dict[str, List[str]]) -> Dict[str, List[str]]:
        if not v:
            raise ValueError("Adjacency list cannot be empty")
        return v

    @model_validator(mode='after')
    def check_node_consistency(self) -> 'DefectGraph':
        if len(self.adjacency_list) != self.node_count:
            raise VoronoiFailure(
                f"Adjacency list size ({len(self.adjacency_list)}) does not "
                f"match node_count ({self.node_count}) for graph {self.graph_id}"
            )
        
        # Verify all neighbor IDs exist in the graph
        all_nodes = set(self.adjacency_list.keys())
        for node, neighbors in self.adjacency_list.items():
            for neighbor in neighbors:
                if neighbor not in all_nodes:
                    raise VoronoiFailure(
                        f"Neighbor '{neighbor}' of node '{node}' not found in graph {self.graph_id}"
                    )
        return self

    @property
    def nodes(self) -> List[str]:
        """Return list of all node IDs."""
        return list(self.adjacency_list.keys())

    def get_neighbors(self, node_id: str) -> List[str]:
        """Return neighbors of a specific node."""
        return self.adjacency_list.get(node_id, [])

    def degree(self, node_id: str) -> int:
        """Return the degree of a specific node."""
        return len(self.adjacency_list.get(node_id, []))

    def has_edge(self, node_a: str, node_b: str) -> bool:
        """Check if an edge exists between two nodes."""
        return node_b in self.adjacency_list.get(node_a, [])