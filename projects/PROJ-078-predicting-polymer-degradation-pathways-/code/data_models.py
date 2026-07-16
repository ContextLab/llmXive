from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import numpy as np

@dataclass
class PolymerRecord:
    """
    Represents a single polymer degradation record from external sources.
    """
    smiles: str
    temperature: Optional[float] = None
    ph: Optional[float] = None
    uv_intensity: Optional[float] = None
    degradation_pathway: Optional[str] = None
    source: Optional[str] = None
    record_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MolecularGraph:
    """
    Represents a molecular graph derived from a SMILES string.
    Contains node features, edge indices, and edge attributes suitable for GNN input.
    """
    smiles: str
    node_features: np.ndarray  # Shape: (num_atoms, num_features)
    edge_index: np.ndarray     # Shape: (2, num_edges)
    edge_attributes: np.ndarray # Shape: (num_edges,)
    num_atoms: int
    num_bonds: int
    # Optional: store original record ID or metadata if needed
    record_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
