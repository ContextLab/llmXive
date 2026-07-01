"""
Base data structures for MolecularGraph and InterfacePair entities.

These classes define the explicit class signatures for node/edge attributes
required for the polymer-filler interaction prediction pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


@dataclass
class MolecularGraph:
    """
    Represents a single molecular graph structure derived from a polymer or filler.

    Attributes:
        smiles (str): The SMILES string representation of the molecule.
        node_features (np.ndarray): Node feature matrix of shape (num_nodes, num_node_features).
        edge_index (np.ndarray): Edge index matrix of shape (2, num_edges) for PyTorch Geometric compatibility.
        edge_features (Optional[np.ndarray]): Edge feature matrix of shape (num_edges, num_edge_features).
        node_attributes (List[Dict[str, Any]]): List of dictionaries containing detailed node attributes (e.g., atom type, charge).
        edge_attributes (List[Dict[str, Any]]): List of dictionaries containing detailed edge attributes (e.g., bond type, conjugation).
        metadata (Dict[str, Any]): Additional metadata about the molecule (e.g., molecular weight, source).
    """
    smiles: str
    node_features: np.ndarray
    edge_index: np.ndarray
    edge_features: Optional[np.ndarray] = None
    node_attributes: List[Dict[str, Any]] = field(default_factory=list)
    edge_attributes: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate dimensions and types after initialization."""
        if not isinstance(self.node_features, np.ndarray):
            raise TypeError("node_features must be a numpy array")
        if not isinstance(self.edge_index, np.ndarray):
            raise TypeError("edge_index must be a numpy array")
        if self.edge_index.shape[0] != 2:
            raise ValueError("edge_index must have shape (2, num_edges)")
        if len(self.node_features) != len(self.node_attributes):
            # Allow empty attributes if not provided, but if provided, must match node count
            if len(self.node_attributes) > 0:
                raise ValueError("node_attributes length must match number of nodes")
        if self.edge_features is not None:
            if len(self.edge_features) != self.edge_index.shape[1]:
                raise ValueError("edge_features length must match number of edges")
            if len(self.edge_features) != len(self.edge_attributes):
                if len(self.edge_attributes) > 0:
                    raise ValueError("edge_attributes length must match number of edges")


@dataclass
class InterfacePair:
    """
    Represents a pair of interacting molecules (polymer and filler) with an associated target value.

    Attributes:
        polymer_graph (MolecularGraph): The graph representing the polymer component.
        filler_graph (MolecularGraph): The graph representing the filler component.
        adhesion_energy (Optional[float]): The target adhesion energy value (e.g., in J/m^2 or meV/A^2).
        interaction_type (Optional[str]): Classification of the interaction (e.g., 'van_der_waals', 'hydrogen_bond', 'covalent').
        metadata (Dict[str, Any]): Additional metadata about the pair (e.g., experimental conditions, source dataset).
    """
    polymer_graph: MolecularGraph
    filler_graph: MolecularGraph
    adhesion_energy: Optional[float] = None
    interaction_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the pair structure."""
        if not isinstance(self.polymer_graph, MolecularGraph):
            raise TypeError("polymer_graph must be an instance of MolecularGraph")
        if not isinstance(self.filler_graph, MolecularGraph):
            raise TypeError("filler_graph must be an instance of MolecularGraph")