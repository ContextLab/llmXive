from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np

@dataclass
class MaterialGraph:
    """Graph representation of a 2D material.
    
    This schema defines the structure for storing material data as a graph,
    where nodes represent atoms and edges represent bonds or interactions.
    Target values are elastic moduli derived from DFT calculations.
    
    Attributes:
        material_id: Unique identifier for the material (e.g., MP-12345)
        composition: Dictionary mapping element symbols to stoichiometric ratios
        nodes: List of node feature dictionaries (atomic number, electronegativity, etc.)
        edges: List of edge feature dictionaries (bond length, type, etc.)
        edge_index: 2xE numpy array defining graph connectivity (source, target indices)
        target_tensor: Optional 6-component elastic tensor (Voigt notation)
        family: Chemical family classification (e.g., 'TMDC', 'MXene')
        space_group: International space group number
    """
    
    material_id: str
    composition: Dict[str, float]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    edge_index: np.ndarray
    target_tensor: Optional[np.ndarray] = None  # 6-component elastic tensor
    family: Optional[str] = None
    space_group: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the MaterialGraph to a dictionary for serialization."""
        return {
            'material_id': self.material_id,
            'composition': self.composition,
            'nodes': self.nodes,
            'edges': self.edges,
            'edge_index': self.edge_index.tolist(),
            'target_tensor': self.target_tensor.tolist() if self.target_tensor is not None else None,
            'family': self.family,
            'space_group': self.space_group
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialGraph':
        """Reconstruct a MaterialGraph from a dictionary."""
        edge_index = np.array(data['edge_index'])
        target_tensor = np.array(data['target_tensor']) if data.get('target_tensor') is not None else None
        
        return cls(
            material_id=data['material_id'],
            composition=data['composition'],
            nodes=data['nodes'],
            edges=data['edges'],
            edge_index=edge_index,
            target_tensor=target_tensor,
            family=data.get('family'),
            space_group=data.get('space_group')
        )
    
    def validate(self) -> bool:
        """Validate the integrity of the graph structure and data types.
        
        Returns:
            bool: True if the graph is valid, False otherwise.
        """
        if not self.material_id or not isinstance(self.material_id, str):
            return False
        
        if not self.composition or not isinstance(self.composition, dict):
            return False
        
        if not self.nodes or not isinstance(self.nodes, list):
            return False
        
        if not self.edges or not isinstance(self.edges, list):
            return False
        
        if self.edge_index.shape[0] != 2:
            return False
        
        if self.target_tensor is not None:
            if self.target_tensor.shape != (6,):
                return False
        
        return True