from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import numpy as np


@dataclass
class AnomalyScore:
    """
    Represents an anomaly score with associated metadata and uncertainty.

    Attributes:
        timestamp: Unix timestamp of the observation
        score: Anomaly score (higher = more anomalous)
        uncertainty: Uncertainty estimate (e.g., standard deviation)
        component_assignments: Optional list of component assignments for the observation
        metadata: Additional metadata dictionary
    """
    timestamp: float
    score: float
    uncertainty: float
    component_assignments: Optional[List[int]] = field(default=None)
    metadata: Optional[Dict[str, Any]] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp,
            "score": self.score,
            "uncertainty": self.uncertainty,
            "component_assignments": self.component_assignments,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnomalyScore":
        """Create from dictionary representation."""
        return cls(
            timestamp=data["timestamp"],
            score=data["score"],
            uncertainty=data["uncertainty"],
            component_assignments=data.get("component_assignments"),
            metadata=data.get("metadata")
        )
