"""
Data models for polymer degradation prediction.

Defines core data structures for representing polymer records and their
corresponding molecular graph representations.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np


@dataclass
class PolymerRecord:
    """
    Represents a single polymer degradation record from a data source.

    Attributes:
        record_id: Unique identifier for the record.
        smiles: SMILES string representing the polymer structure.
        degradation_pathway: The observed degradation mechanism (e.g., 'hydrolysis', 'oxidation').
        temperature: Temperature in Kelvin (optional, may be missing in raw data).
        ph: pH value (optional, may be missing in raw data).
        uv_exposure: UV exposure level or duration (optional, may be missing).
        source: The original data source (e.g., 'NIST', 'MaterialsProject').
        metadata: Additional raw metadata as a dictionary.
    """
    record_id: str
    smiles: str
    degradation_pathway: str
    temperature: Optional[float] = None
    ph: Optional[float] = None
    uv_exposure: Optional[float] = None
    source: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_complete_environmental_data(self) -> bool:
        """
        Checks if all required environmental parameters are present.

        Returns:
            True if temperature, pH, and UV exposure are all defined.
        """
        return (
            self.temperature is not None and
            self.ph is not None and
            self.uv_exposure is not None
        )

    def to_dict(self) -> Dict[str, Any]:
        """Converts the record to a dictionary."""
        return {
            "record_id": self.record_id,
            "smiles": self.smiles,
            "degradation_pathway": self.degradation_pathway,
            "temperature": self.temperature,
            "ph": self.ph,
            "uv_exposure": self.uv_exposure,
            "source": self.source,
            "metadata": self.metadata
        }


@dataclass
class MolecularGraph:
    """
    Represents a molecular graph derived from a polymer SMILES string.

    This structure is used as input for Graph Neural Networks.

    Attributes:
        node_features: NumPy array of shape (num_nodes, num_node_features).
                       Typically includes atomic number, degree, etc.
        edge_index: NumPy array of shape (2, num_edges).
                    Source and target node indices for edges.
        edge_features: NumPy array of shape (num_edges, num_edge_features).
                       Typically includes bond type, conjugation, etc.
        y: Target label (encoded degradation pathway).
        record_id: Reference to the original PolymerRecord ID.
        atom_map: Optional mapping from node index to atom symbol for interpretability.
    """
    node_features: np.ndarray
    edge_index: np.ndarray
    edge_features: np.ndarray
    y: int
    record_id: str
    atom_map: Optional[List[str]] = None

    def __post_init__(self):
        """Ensure types are numpy arrays for consistency."""
        if not isinstance(self.node_features, np.ndarray):
            self.node_features = np.array(self.node_features)
        if not isinstance(self.edge_index, np.ndarray):
            self.edge_index = np.array(self.edge_index)
        if not isinstance(self.edge_features, np.ndarray):
            self.edge_features = np.array(self.edge_features)

        # Basic shape validation
        if self.node_features.shape[0] == 0:
            raise ValueError("MolecularGraph cannot have zero nodes.")
        if self.edge_index.shape[0] != 2:
            raise ValueError("edge_index must have shape (2, num_edges).")

    @property
    def num_nodes(self) -> int:
        """Returns the number of nodes in the graph."""
        return self.node_features.shape[0]

    @property
    def num_edges(self) -> int:
        """Returns the number of edges in the graph."""
        return self.edge_index.shape[1]