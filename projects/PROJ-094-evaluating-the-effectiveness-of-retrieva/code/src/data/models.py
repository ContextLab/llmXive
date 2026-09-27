"""
Data models for the RAG Code Search evaluation pipeline.

Defines core dataclasses: CodeSnippet, QueryResult, and PerformanceDelta
aligned with the project specification.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class RetrievalMethod(Enum):
    """Enumeration of supported retrieval methods."""
    BM25 = "bm25"
    NEURAL = "neural"
    RAG = "rag"


@dataclass
class CodeSnippet:
    """
    Represents a code snippet from the dataset.

    Attributes:
        id: Unique identifier for the snippet.
        language: Programming language of the snippet (e.g., 'python', 'java').
        code: The raw code content.
        docstring: The associated documentation string.
        repo: Source repository name.
        path: File path within the repository.
    """
    id: str
    language: str
    code: str
    docstring: str
    repo: str
    path: str
    # Optional fields for ground truth mapping
    query_id: Optional[str] = None
    relevance_label: Optional[int] = None  # 0: non-relevant, 1: relevant, etc.

@dataclass
class QueryResult:
    """
    Represents the result of a retrieval query.

    Attributes:
        query_id: Identifier of the query.
        method: The retrieval method used (BM25, NEURAL, RAG).
        retrieved_snippets: List of CodeSnippet objects returned, ordered by relevance score.
        scores: List of retrieval scores corresponding to the snippets.
        ground_truth_ids: List of ground truth snippet IDs for this query (for evaluation).
    """
    query_id: str
    method: RetrievalMethod
    retrieved_snippets: List[CodeSnippet] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)
    ground_truth_ids: List[str] = field(default_factory=list)

@dataclass
class PerformanceDelta:
    """
    Represents the performance difference between two retrieval methods for a query.

    Attributes:
        query_id: Identifier of the query.
        baseline_method: The baseline retrieval method.
        proposed_method: The proposed retrieval method.
        baseline_metric: Metric score (e.g., nDCG@10) for the baseline.
        proposed_metric: Metric score for the proposed method.
        delta: Absolute difference (proposed - baseline).
        percentage_change: Relative percentage change.
    """
    query_id: str
    baseline_method: RetrievalMethod
    proposed_method: RetrievalMethod
    baseline_metric: float
    proposed_metric: float
    delta: float
    percentage_change: float