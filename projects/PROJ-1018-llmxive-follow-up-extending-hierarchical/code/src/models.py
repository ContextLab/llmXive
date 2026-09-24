from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json
import numpy as np

@dataclass
class RelevanceProfile:
    """
    Represents the aggregated retrieval score matrix for a specific chunk.
    """
    chunk_id: str
    scores: List[float]
    document_id: str

@dataclass
class StaticIndex:
    """
    Represents the static lookup table generated from clustering relevance profiles.
    Contains centroids and the mapping from chunk IDs to cluster IDs.
    
    Fields:
        centroids: np.ndarray of shape (k, feature_dim) representing cluster centers.
        chunk_to_cluster: Dict mapping chunk_id (str) to cluster_id (int).
        k: int, the number of clusters.
    """
    centroids: np.ndarray
    chunk_to_cluster: Dict[str, int]
    k: int

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the StaticIndex to a dictionary compatible with JSON.
        Note: numpy arrays are converted to lists.
        """
        return {
            "centroids": self.centroids.tolist(),
            "chunk_to_cluster": self.chunk_to_cluster,
            "k": self.k
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StaticIndex":
        """
        Deserializes a dictionary back into a StaticIndex instance.
        """
        return cls(
            centroids=np.array(data["centroids"]),
            chunk_to_cluster=data["chunk_to_cluster"],
            k=data["k"]
        )

@dataclass
class EvaluationReport:
    """
    Aggregates metrics from the comparative evaluation phase.
    """
    perplexity: Dict[str, float]  # e.g., {"dynamic": 12.3, "static": 12.5}
    qa_accuracy: Dict[str, float]
    p_value: float
    latency: Dict[str, float]
    memory_footprint: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "perplexity": self.perplexity,
            "qa_accuracy": self.qa_accuracy,
            "p_value": self.p_value,
            "latency": self.latency,
            "memory_footprint": self.memory_footprint
        }
