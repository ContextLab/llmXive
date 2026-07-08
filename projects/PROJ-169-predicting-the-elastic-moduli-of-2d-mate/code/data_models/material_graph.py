"""
Data schema for MaterialGraph.
Represents a 2D material as a graph structure.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np

@dataclass
class MaterialGraph:
    """
    Graph representation of a 2D material.

    Attributes:
        material_id: Unique identifier (e.g., from Materials Project)
        composition: Chemical formula string
        nodes: List of node features (elemental properties)
        edges: List of edge features (bond distances, types)
        edge_index: Shape (2, E) tensor defining connectivity
        target_moduli: Optional dict of target elastic properties (GPa)
        metadata: Additional structural info (space group, layer count)
    """
    material_id: str
    composition: str
    nodes: np.ndarray  # Shape (N_nodes, node_feature_dim)
    edges: np.ndarray  # Shape (N_edges, edge_feature_dim)
    edge_index: np.ndarray  # Shape (2, N_edges)
    target_moduli: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "material_id": self.material_id,
            "composition": self.composition,
            "nodes": self.nodes.tolist(),
            "edges": self.edges.tolist(),
            "edge_index": self.edge_index.tolist(),
            "target_moduli": self.target_moduli,
            "metadata": self.metadata,
        }
