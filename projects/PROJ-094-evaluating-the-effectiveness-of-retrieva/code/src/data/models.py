from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
import json


class RetrievalMethod(Enum):
    """Enumeration of supported retrieval methods."""
    BM25 = "bm25"
    NEURAL = "neural"
    RAG = "rag"


@dataclass
class CodeSnippet:
    """
    Represents a code snippet from the dataset.
    
    Schema alignment with spec:
    - id: Unique identifier for the snippet
    - repo: Repository name
    - path: File path within the repo
    - language: Programming language
    - code: The actual code content
    - docstring: Associated documentation/docstring
    - tokens: Preprocessed tokenized version (optional)
    """
    id: str
    repo: str
    path: str
    language: str
    code: str
    docstring: str
    tokens: Optional[List[str]] = None
    embeddings: Optional[List[float]] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "repo": self.repo,
            "path": self.path,
            "language": self.language,
            "code": self.code,
            "docstring": self.docstring,
            "tokens": self.tokens,
            "embeddings": self.embeddings
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CodeSnippet":
        """Create instance from dictionary."""
        return cls(
            id=data["id"],
            repo=data["repo"],
            path=data["path"],
            language=data["language"],
            code=data["code"],
            docstring=data["docstring"],
            tokens=data.get("tokens"),
            embeddings=data.get("embeddings")
        )


@dataclass
class QueryResult:
    """
    Represents a retrieval result for a specific query.
    
    Schema alignment with spec:
    - query_id: Unique identifier for the query
    - method: Retrieval method used
    - retrieved_snippets: List of retrieved CodeSnippets with scores
    - ground_truth_ids: List of ground truth snippet IDs
    - metrics: Dictionary of evaluation metrics (precision, recall, ndcg, etc.)
    """
    query_id: str
    method: RetrievalMethod
    retrieved_snippets: List[CodeSnippet] = field(default_factory=list)
    retrieved_scores: List[float] = field(default_factory=list)
    ground_truth_ids: List[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "query_id": self.query_id,
            "method": self.method.value,
            "retrieved_snippets": [s.to_dict() for s in self.retrieved_snippets],
            "retrieved_scores": self.retrieved_scores,
            "ground_truth_ids": self.ground_truth_ids,
            "metrics": self.metrics,
            "execution_time_ms": self.execution_time_ms
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "QueryResult":
        """Create instance from dictionary."""
        return cls(
            query_id=data["query_id"],
            method=RetrievalMethod(data["method"]),
            retrieved_snippets=[CodeSnippet.from_dict(s) for s in data.get("retrieved_snippets", [])],
            retrieved_scores=data.get("retrieved_scores", []),
            ground_truth_ids=data.get("ground_truth_ids", []),
            metrics=data.get("metrics", {}),
            execution_time_ms=data.get("execution_time_ms", 0.0)
        )


@dataclass
class PerformanceDelta:
    """
    Represents the performance difference between two retrieval methods.
    
    Schema alignment with spec:
    - query_id: Unique identifier for the query
    - baseline_method: The baseline retrieval method
    - rag_method: The RAG retrieval method
    - baseline_metrics: Metrics for baseline method
    - rag_metrics: Metrics for RAG method
    - delta_metrics: Absolute difference (RAG - Baseline) for each metric
    """
    query_id: str
    baseline_method: RetrievalMethod
    rag_method: RetrievalMethod
    baseline_metrics: dict = field(default_factory=dict)
    rag_metrics: dict = field(default_factory=dict)
    delta_metrics: dict = field(default_factory=dict)
    
    def compute_deltas(self) -> None:
        """Calculate the performance deltas (RAG - Baseline) for all metrics."""
        all_keys = set(self.baseline_metrics.keys()) | set(self.rag_metrics.keys())
        for key in all_keys:
            baseline_val = self.baseline_metrics.get(key, 0.0)
            rag_val = self.rag_metrics.get(key, 0.0)
            self.delta_metrics[key] = rag_val - baseline_val
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "query_id": self.query_id,
            "baseline_method": self.baseline_method.value,
            "rag_method": self.rag_method.value,
            "baseline_metrics": self.baseline_metrics,
            "rag_metrics": self.rag_metrics,
            "delta_metrics": self.delta_metrics
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PerformanceDelta":
        """Create instance from dictionary."""
        instance = cls(
            query_id=data["query_id"],
            baseline_method=RetrievalMethod(data["baseline_method"]),
            rag_method=RetrievalMethod(data["rag_method"]),
            baseline_metrics=data.get("baseline_metrics", {}),
            rag_metrics=data.get("rag_metrics", {}),
            delta_metrics=data.get("delta_metrics", {})
        )
        # Ensure deltas are computed if not present
        if not instance.delta_metrics:
            instance.compute_deltas()
        return instance
