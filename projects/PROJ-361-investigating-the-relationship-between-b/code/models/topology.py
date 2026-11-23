"""
Topology metrics data model.

Represents graph theory metrics computed from functional connectivity matrices.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
import numpy as np


@dataclass
class TopologyMetrics:
    """
    Represents five core graph theory metrics for a subject's brain network.
    
    Metrics:
        modularity: Q value from Louvain community detection
        characteristic_path_length: Average shortest path length
        clustering_coefficient: Average local clustering coefficient
        global_efficiency: Inverse of harmonic mean of shortest paths
        small_worldness: Ratio of clustering to path length compared to random
    
    Attributes:
        subject_id: ID of the subject
        metrics: Dictionary containing the five metric values
        parcellation: Parcellation scheme used
        threshold: Threshold applied to connectivity matrix
        n_modules: Number of modules detected (from Louvain)
        is_valid: Whether all metrics are within theoretical bounds
        validation_errors: List of validation error messages if any
    """
    subject_id: str
    metrics: Dict[str, float]
    parcellation: str = "Schaefer200"
    threshold: Optional[float] = None
    n_modules: Optional[int] = None
    is_valid: bool = True
    validation_errors: Optional[list] = None

    def __post_init__(self) -> None:
        """Validate metric names and values."""
        required_metrics = [
            "modularity",
            "characteristic_path_length",
            "clustering_coefficient",
            "global_efficiency",
            "small_worldness",
        ]
        
        missing = set(required_metrics) - set(self.metrics.keys())
        if missing:
            raise ValueError(f"Missing required metrics: {missing}")
        
        # Validate bounds
        self._validate_bounds()

    def _validate_bounds(self) -> None:
        """Check metrics against theoretical bounds."""
        self.validation_errors = []
        
        # Modularity: [0, 1]
        mod = self.metrics["modularity"]
        if not (0 <= mod <= 1):
            self.validation_errors.append(f"Modularity {mod} out of [0, 1]")
        
        # Path length: > 0
        path_len = self.metrics["characteristic_path_length"]
        if path_len <= 0:
            self.validation_errors.append(f"Path length {path_len} <= 0")
        
        # Clustering: [0, 1]
        cluster = self.metrics["clustering_coefficient"]
        if not (0 <= cluster <= 1):
            self.validation_errors.append(f"Clustering {cluster} out of [0, 1]")
        
        # Global efficiency: (0, 1] typically
        eff = self.metrics["global_efficiency"]
        if eff <= 0 or eff > 1.0:
            # Allow slight >1 due to floating point, but flag clearly
            if eff > 1.001:
                self.validation_errors.append(f"Global efficiency {eff} > 1.0")
        
        # Small-worldness: > 1 typically
        sw = self.metrics["small_worldness"]
        if sw <= 1:
            self.validation_errors.append(f"Small-worldness {sw} <= 1")
        
        self.is_valid = len(self.validation_errors) == 0

    def get_metric(self, name: str) -> float:
        """Get a specific metric value."""
        return self.metrics[name]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "subject_id": self.subject_id,
            "metrics": self.metrics,
            "parcellation": self.parcellation,
            "threshold": self.threshold,
            "n_modules": self.n_modules,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TopologyMetrics":
        """Create from dictionary."""
        return cls(
            subject_id=data["subject_id"],
            metrics=data["metrics"],
            parcellation=data.get("parcellation", "Schaefer200"),
            threshold=data.get("threshold"),
            n_modules=data.get("n_modules"),
            is_valid=data.get("is_valid", True),
            validation_errors=data.get("validation_errors"),
        )
