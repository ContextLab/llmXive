from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import numpy as np


@dataclass
class Graph:
    """
    Data model representing a molecular graph derived from a Molecule.
    Contains node and edge features suitable for Graph Neural Networks.
    """
    smiles: str
    num_nodes: int
    num_edges: int
    node_features: np.ndarray
    edge_features: np.ndarray
    edge_index: np.ndarray
    molecular_weight: Optional[float] = None
    surface_area: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Graph instance to a dictionary."""
        return {
            "smiles": self.smiles,
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "node_features": self.node_features.tolist(),
            "edge_features": self.edge_features.tolist(),
            "edge_index": self.edge_index.tolist(),
            "molecular_weight": self.molecular_weight,
            "surface_area": self.surface_area,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Graph":
        """Create a Graph instance from a dictionary."""
        return cls(
            smiles=data["smiles"],
            num_nodes=data["num_nodes"],
            num_edges=data["num_edges"],
            node_features=np.array(data["node_features"]),
            edge_features=np.array(data["edge_features"]),
            edge_index=np.array(data["edge_index"]),
            molecular_weight=data.get("molecular_weight"),
            surface_area=data.get("surface_area"),
            metadata=data.get("metadata", {})
        )

    def to_torch_geometric_data(self):
        """
        Convert this Graph to a PyTorch Geometric Data object.
        Requires torch and torch_geometric to be installed.
        """
        try:
            from torch_geometric.data import Data
            import torch
        except ImportError as e:
            raise ImportError("torch and torch_geometric are required to convert to PyG Data object.") from e

        return Data(
            x=torch.tensor(self.node_features, dtype=torch.float),
            edge_index=torch.tensor(self.edge_index, dtype=torch.long),
            edge_attr=torch.tensor(self.edge_features, dtype=torch.float),
            y=torch.tensor([self.surface_area], dtype=torch.float) if self.surface_area is not None else None,
            smiles=self.smiles,
            mw=self.molecular_weight
        )

    def __post_init__(self):
        if self.num_nodes <= 0:
            raise ValueError("Number of nodes must be positive.")
        if self.num_edges < 0:
            raise ValueError("Number of edges cannot be negative.")
        if self.node_features.shape[0] != self.num_nodes:
            raise ValueError("Number of node features must match num_nodes.")
        if self.edge_index.shape[1] != self.num_edges:
            raise ValueError("Number of columns in edge_index must match num_edges.")
