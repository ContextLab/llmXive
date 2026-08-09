"""
Data model for a single molecule.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import json
import numpy as np

@dataclass
class Molecule:
    """
    Represents a molecule with its SMILES string, computed features, and properties.
    
    Attributes:
        smiles (str): Canonical SMILES representation.
        molecular_weight (float): Calculated molecular weight in g/mol.
        atom_count (int): Number of atoms in the molecule.
        node_features (np.ndarray): 2D array of shape (N_atoms, N_features) containing 
                                    atom-level features (e.g., type, hybridization, charge).
        edge_features (np.ndarray): 2D array of shape (N_edges, N_features) containing 
                                    bond-level features.
        surface_area (Optional[float]): Calculated Solvent Accessible Surface Area (SASA) in Å².
        metadata (Dict[str, Any]): Additional arbitrary metadata.
    """
    smiles: str
    molecular_weight: float = 0.0
    atom_count: int = 0
    node_features: Optional[np.ndarray] = field(default=None)
    edge_features: Optional[np.ndarray] = field(default=None)
    surface_area: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure numpy arrays are properly initialized if provided as lists."""
        if self.node_features is not None and not isinstance(self.node_features, np.ndarray):
            self.node_features = np.array(self.node_features)
        if self.edge_features is not None and not isinstance(self.edge_features, np.ndarray):
            self.edge_features = np.array(self.edge_features)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the molecule to a dictionary for serialization."""
        return {
            'smiles': self.smiles,
            'molecular_weight': self.molecular_weight,
            'atom_count': self.atom_count,
            'node_features': self.node_features.tolist() if self.node_features is not None else None,
            'edge_features': self.edge_features.tolist() if self.edge_features is not None else None,
            'surface_area': self.surface_area,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Molecule':
        """Create a Molecule instance from a dictionary."""
        node_features = None
        if data.get('node_features') is not None:
            node_features = np.array(data['node_features'])
        
        edge_features = None
        if data.get('edge_features') is not None:
            edge_features = np.array(data['edge_features'])

        return cls(
            smiles=data['smiles'],
            molecular_weight=data.get('molecular_weight', 0.0),
            atom_count=data.get('atom_count', 0),
            node_features=node_features,
            edge_features=edge_features,
            surface_area=data.get('surface_area'),
            metadata=data.get('metadata', {})
        )

    def to_json(self) -> str:
        """Serialize the molecule to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'Molecule':
        """Deserialize a molecule from a JSON string."""
        return cls.from_dict(json.loads(json_str))
