"""
Data model for a molecular graph representation.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import numpy as np

@dataclass
class Graph:
    """
    Represents a molecular graph suitable for Graph Neural Networks.
    
    Attributes:
        smiles (str): Canonical SMILES representation of the molecule.
        node_features (np.ndarray): 2D array of shape (N_nodes, N_features).
        edge_index (np.ndarray): 2D array of shape (2, N_edges) representing connectivity.
        edge_features (Optional[np.ndarray]): 2D array of shape (N_edges, N_features).
        molecular_weight (Optional[float]): Molecular weight for stratification.
        surface_area (Optional[float]): Target variable (SASA) if available.
        metadata (Dict[str, Any]): Additional metadata.
    """
    smiles: str
    node_features: np.ndarray
    edge_index: np.ndarray
    edge_features: Optional[np.ndarray] = None
    molecular_weight: Optional[float] = None
    surface_area: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure numpy arrays are properly typed."""
        if not isinstance(self.node_features, np.ndarray):
            self.node_features = np.array(self.node_features)
        if not isinstance(self.edge_index, np.ndarray):
            self.edge_index = np.array(self.edge_index)
        if self.edge_features is not None and not isinstance(self.edge_features, np.ndarray):
            self.edge_features = np.array(self.edge_features)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the graph to a dictionary."""
        return {
            'smiles': self.smiles,
            'node_features': self.node_features.tolist(),
            'edge_index': self.edge_index.tolist(),
            'edge_features': self.edge_features.tolist() if self.edge_features is not None else None,
            'molecular_weight': self.molecular_weight,
            'surface_area': self.surface_area,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Graph':
        """Create a Graph instance from a dictionary."""
        return cls(
            smiles=data['smiles'],
            node_features=np.array(data['node_features']),
            edge_index=np.array(data['edge_index']),
            edge_features=np.array(data['edge_features']) if data.get('edge_features') is not None else None,
            molecular_weight=data.get('molecular_weight'),
            surface_area=data.get('surface_area'),
            metadata=data.get('metadata', {})
        )
