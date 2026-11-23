from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json
import numpy as np

@dataclass
class RelevanceProfile:
    chunk_id: str
    scores: List[float]
    document_id: str

@dataclass
class StaticIndex:
    centroids: np.ndarray
    chunk_to_cluster: Dict[str, int]
    k: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert the StaticIndex to a JSON-serializable dictionary."""
        return {
            "centroids": self.centroids.tolist(),
            "chunk_to_cluster": self.chunk_to_cluster,
            "k": self.k
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StaticIndex":
        """Reconstruct a StaticIndex from a JSON-serializable dictionary."""
        return cls(
            centroids=np.array(data["centroids"]),
            chunk_to_cluster=data["chunk_to_cluster"],
            k=data["k"]
        )

@dataclass
class EvaluationReport:
    perplexity: float
    qa_accuracy: float
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
