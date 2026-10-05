from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np

@dataclass
class PolymerRecord:
    """
    Data class representing a polymer degradation record.
    Fields: smiles, temperature, ph, uv, degradation_pathway, source_id.
    """
    smiles: str
    temperature: Optional[float] = None
    ph: Optional[float] = None
    uv: Optional[float] = None
    degradation_pathway: Optional[str] = None
    source_id: Optional[str] = None
    
    # Additional fields for compatibility with existing codebase if needed
    polymer_id: str = field(default_factory=lambda: "")
    molecular_weight: Optional[float] = None
    source: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_complete(self) -> bool:
        """Check if all required fields are present."""
        return all([
            self.smiles,
            self.degradation_pathway,
            self.temperature is not None,
            self.ph is not None,
            self.uv is not None
        ])

    def has_missing_env_data(self) -> bool:
        """Check if any environmental data is missing."""
        return any([
            self.temperature is None,
            self.ph is None,
            self.uv is None
        ])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'smiles': self.smiles,
            'temperature': self.temperature,
            'ph': self.ph,
            'uv': self.uv,
            'degradation_pathway': self.degradation_pathway,
            'source_id': self.source_id,
            'polymer_id': self.polymer_id,
            'molecular_weight': self.molecular_weight,
            'source': self.source,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PolymerRecord':
        """Create from dictionary."""
        return cls(
            smiles=data.get('smiles', ''),
            temperature=data.get('temperature'),
            ph=data.get('ph'),
            uv=data.get('uv'),
            degradation_pathway=data.get('degradation_pathway'),
            source_id=data.get('source_id'),
            polymer_id=data.get('polymer_id', ''),
            molecular_weight=data.get('molecular_weight'),
            source=data.get('source', 'unknown'),
            metadata=data.get('metadata', {})
        )

@dataclass
class MolecularGraph:
    """
    Data class representing a molecular graph derived from SMILES.
    Fields: atom_features, bond_features, edge_index, environment_vector.
    """
    atom_features: np.ndarray
    bond_features: Optional[np.ndarray] = None
    edge_index: np.ndarray
    environment_vector: Optional[np.ndarray] = None
    
    # Additional fields for compatibility
    polymer_id: str = field(default_factory=lambda: "")
    graph_label: Optional[str] = None
    smiles: Optional[str] = None
    is_valid: bool = True
    error_message: Optional[str] = None
    node_features: Optional[np.ndarray] = None  # Alias for atom_features if needed
    edge_attributes: Optional[np.ndarray] = None  # Alias for bond_features if needed

    def __post_init__(self):
        # Ensure atom_features is a numpy array
        if not isinstance(self.atom_features, np.ndarray):
            self.atom_features = np.array(self.atom_features)
        # Ensure edge_index is a numpy array
        if not isinstance(self.edge_index, np.ndarray):
            self.edge_index = np.array(self.edge_index)
        # Ensure bond_features is a numpy array if present
        if self.bond_features is not None and not isinstance(self.bond_features, np.ndarray):
            self.bond_features = np.array(self.bond_features)
        # Ensure environment_vector is a numpy array if present
        if self.environment_vector is not None and not isinstance(self.environment_vector, np.ndarray):
            self.environment_vector = np.array(self.environment_vector)

        # Set aliases for compatibility
        if self.node_features is None:
            self.node_features = self.atom_features
        if self.edge_attributes is None:
            self.edge_attributes = self.bond_features

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'atom_features': self.atom_features.tolist(),
            'bond_features': self.bond_features.tolist() if self.bond_features is not None else None,
            'edge_index': self.edge_index.tolist(),
            'environment_vector': self.environment_vector.tolist() if self.environment_vector is not None else None,
            'polymer_id': self.polymer_id,
            'graph_label': self.graph_label,
            'smiles': self.smiles,
            'is_valid': self.is_valid,
            'error_message': self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MolecularGraph':
        """Create from dictionary."""
        return cls(
            atom_features=np.array(data['atom_features']),
            bond_features=np.array(data['bond_features']) if data.get('bond_features') is not None else None,
            edge_index=np.array(data['edge_index']),
            environment_vector=np.array(data['environment_vector']) if data.get('environment_vector') is not None else None,
            polymer_id=data.get('polymer_id', ''),
            graph_label=data.get('graph_label'),
            smiles=data.get('smiles'),
            is_valid=data.get('is_valid', True),
            error_message=data.get('error_message')
        )