from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np

@dataclass
class MaterialGraph:
    """Graph representation of a 2D material."""
    
    material_id: str
    composition: Dict[str, float]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    edge_index: np.ndarray
    target_tensor: Optional[np.ndarray] = None  # 6-component elastic tensor
    family: Optional[str] = None
    space_group: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
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
