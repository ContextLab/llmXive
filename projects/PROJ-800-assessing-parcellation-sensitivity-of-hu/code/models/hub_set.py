"""
Data model for a set of hub nodes derived from centrality scores.
"""
from dataclasses import dataclass, field
from typing import List, Set, Dict, Any, Optional
import numpy as np

from utils.logger import get_logger, ProcessingError

logger = get_logger(__name__)


@dataclass
class HubSet:
    """
    Represents a set of hub nodes identified in a connectome.

    Attributes:
        subject_id: Identifier for the subject.
        resolution: The parcellation resolution used (e.g., 'aal90').
        hub_indices: Set of integer indices corresponding to hub nodes.
        hub_ids: List of string identifiers for the hub nodes (ordered by index).
        threshold: The threshold value used to define hubs (e.g., 0.10).
        threshold_type: Type of thresholding ('proportional', 'absolute').
        total_nodes: Total number of nodes in the underlying graph.
        metadata: Additional metadata.
    """
    subject_id: str
    resolution: str
    hub_indices: Set[int]
    hub_ids: List[str]
    threshold: float
    threshold_type: str
    total_nodes: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the HubSet consistency."""
        if not isinstance(self.hub_indices, set):
            raise ProcessingError("HubSet: 'hub_indices' must be a set.")

        if len(self.hub_indices) != len(self.hub_ids):
            raise ProcessingError(
                f"HubSet: 'hub_indices' size ({len(self.hub_indices)}) does not match 'hub_ids' size ({len(self.hub_ids)})"
            )

        if self.total_nodes <= 0:
            raise ProcessingError(f"HubSet: 'total_nodes' must be positive, got {self.total_nodes}")

        # Validate indices are within bounds
        for idx in self.hub_indices:
            if not (0 <= idx < self.total_nodes):
                raise ProcessingError(
                    f"HubSet: Hub index {idx} out of bounds [0, {self.total_nodes})"
                )

    @property
    def n_hubs(self) -> int:
        """Return the number of hubs."""
        return len(self.hub_indices)

    @property
    def hub_ratio(self) -> float:
        """Return the ratio of hubs to total nodes."""
        if self.total_nodes == 0:
            return 0.0
        return self.n_hubs / self.total_nodes

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "subject_id": self.subject_id,
            "resolution": self.resolution,
            "hub_indices": sorted(list(self.hub_indices)),
            "hub_ids": self.hub_ids,
            "threshold": self.threshold,
            "threshold_type": self.threshold_type,
            "total_nodes": self.total_nodes,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HubSet":
        """Deserialize from dictionary."""
        return cls(
            subject_id=data["subject_id"],
            resolution=data["resolution"],
            hub_indices=set(data["hub_indices"]),
            hub_ids=data["hub_ids"],
            threshold=data["threshold"],
            threshold_type=data["threshold_type"],
            total_nodes=data["total_nodes"],
            metadata=data.get("metadata", {})
        )
