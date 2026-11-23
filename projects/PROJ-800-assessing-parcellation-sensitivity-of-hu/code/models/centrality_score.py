"""
Data model for centrality scores computed on a connectome.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np

from utils.logger import get_logger, ProcessingError

logger = get_logger(__name__)


@dataclass
class CentralityScore:
    """
    Container for centrality metrics (Degree, Betweenness, etc.) per node.

    Attributes:
        subject_id: Identifier for the subject.
        resolution: The parcellation resolution used.
        node_ids: List of node identifiers corresponding to the scores.
        degree_centrality: Array of degree centrality scores.
        betweenness_centrality: Array of betweenness centrality scores (optional).
        hub_flags: Boolean array indicating if a node is a hub.
        threshold: The threshold used for hub definition.
        metadata: Additional metadata.
    """
    subject_id: str
    resolution: str
    node_ids: List[str]
    degree_centrality: np.ndarray
    betweenness_centrality: Optional[np.ndarray] = None
    hub_flags: Optional[np.ndarray] = None
    threshold: float = 0.10
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the CentralityScore."""
        n_nodes = len(self.node_ids)

        if len(self.degree_centrality) != n_nodes:
            raise ProcessingError(
                f"CentralityScore: 'degree_centrality' length ({len(self.degree_centrality)}) "
                f"does not match 'node_ids' length ({n_nodes})"
            )

        if self.betweenness_centrality is not None:
            if len(self.betweenness_centrality) != n_nodes:
                raise ProcessingError(
                    f"CentralityScore: 'betweenness_centrality' length ({len(self.betweenness_centrality)}) "
                    f"does not match 'node_ids' length ({n_nodes})"
                )

        if self.hub_flags is not None:
            if len(self.hub_flags) != n_nodes:
                raise ProcessingError(
                    f"CentralityScore: 'hub_flags' length ({len(self.hub_flags)}) "
                    f"does not match 'node_ids' length ({n_nodes})"
                )
            if not np.issubdtype(self.hub_flags.dtype, bool):
                # Attempt to convert if not bool but logical
                if np.issubdtype(self.hub_flags.dtype, np.integer):
                    self.hub_flags = self.hub_flags.astype(bool)
                else:
                    raise ProcessingError("CentralityScore: 'hub_flags' must be boolean array.")

    def get_hub_indices(self) -> List[int]:
        """Return indices of nodes flagged as hubs."""
        if self.hub_flags is None:
            raise ProcessingError("CentralityScore: 'hub_flags' is not set.")
        return [i for i, is_hub in enumerate(self.hub_flags) if is_hub]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result = {
            "subject_id": self.subject_id,
            "resolution": self.resolution,
            "node_ids": self.node_ids,
            "degree_centrality": self.degree_centrality.tolist(),
            "threshold": self.threshold,
            "metadata": self.metadata
        }

        if self.betweenness_centrality is not None:
            result["betweenness_centrality"] = self.betweenness_centrality.tolist()

        if self.hub_flags is not None:
            result["hub_flags"] = self.hub_flags.tolist()

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CentralityScore":
        """Deserialize from dictionary."""
        return cls(
            subject_id=data["subject_id"],
            resolution=data["resolution"],
            node_ids=data["node_ids"],
            degree_centrality=np.array(data["degree_centrality"]),
            betweenness_centrality=np.array(data.get("betweenness_centrality")) if "betweenness_centrality" in data else None,
            hub_flags=np.array(data.get("hub_flags"), dtype=bool) if "hub_flags" in data else None,
            threshold=data.get("threshold", 0.10),
            metadata=data.get("metadata", {})
        )
