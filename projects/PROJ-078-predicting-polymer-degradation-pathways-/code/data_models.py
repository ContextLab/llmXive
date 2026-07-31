from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np

@dataclass
class PolymerRecord:
    """
    Data class representing a polymer degradation record.
    """
    polymer_id: str
    smiles: str
    degradation_pathway: Optional[str] = None
    temperature: Optional[float] = None
    ph: Optional[float] = None
    uv_exposure: Optional[bool] = None
    molecular_weight: Optional[float] = None
    source: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_complete(self) -> bool:
        """Check if all required fields are present."""
        return all([
            self.polymer_id,
            self.smiles,
            self.degradation_pathway,
            self.temperature is not None,
            self.ph is not None,
            self.uv_exposure is not None
        ])

    def has_missing_env_data(self) -> bool:
        """Check if any environmental data is missing."""
        return any([
            self.temperature is None,
            self.ph is None,
            self.uv_exposure is None
        ])

@dataclass
class MolecularGraph:
    """
    Data class representing a molecular graph derived from SMILES.
    """
    polymer_id: str
    node_features: np.ndarray
    edge_index: np.ndarray
    edge_attributes: Optional[np.ndarray] = None
    graph_label: Optional[str] = None
    smiles: Optional[str] = None
    is_valid: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'polymer_id': self.polymer_id,
            'node_features': self.node_features.tolist(),
            'edge_index': self.edge_index.tolist(),
            'edge_attributes': self.edge_attributes.tolist() if self.edge_attributes is not None else None,
            'graph_label': self.graph_label,
            'smiles': self.smiles,
            'is_valid': self.is_valid,
            'error_message': self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MolecularGraph':
        """Create from dictionary."""
        return cls(
            polymer_id=data['polymer_id'],
            node_features=np.array(data['node_features']),
            edge_index=np.array(data['edge_index']),
            edge_attributes=np.array(data['edge_attributes']) if data.get('edge_attributes') is not None else None,
            graph_label=data.get('graph_label'),
            smiles=data.get('smiles'),
            is_valid=data.get('is_valid', True),
            error_message=data.get('error_message')
        )
