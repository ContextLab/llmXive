"""
Data models for the RAG code search evaluation pipeline.

Defines core data structures for code snippets, queries, and performance metrics.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class RetrievalMethod(Enum):
    """Enumeration of retrieval methods used in the evaluation."""
    BM25 = "bm25"
    NEURAL = "neural"
    RAG = "rag"


@dataclass
class CodeSnippet:
    """
    Represents a code snippet from the dataset.
    
    Attributes:
        id: Unique identifier for the snippet
        language: Programming language of the code
        text: The actual code text
        url: Source URL if available
        docstring: Associated documentation string if available
    """
    id: str
    language: str
    text: str
    url: Optional[str] = None
    docstring: Optional[str] = None


@dataclass
class QueryResult:
    """
    Represents the result of a retrieval query.
    
    Attributes:
        query: The original query string
        method: Retrieval method used
        retrieved_snippets: List of (snippet, score) tuples
        ground_truth: List of ground truth snippet IDs
        metrics: Dictionary of evaluation metrics
    """
    query: str
    method: RetrievalMethod
    retrieved_snippets: List[tuple]  # (CodeSnippet, float)
    ground_truth: List[str]
    metrics: dict = field(default_factory=dict)


@dataclass
class PerformanceDelta:
    """
    Represents the performance difference between two retrieval methods.
    
    Attributes:
        query_id: Identifier for the query
        method_a: First retrieval method
        method_b: Second retrieval method
        metric: Name of the metric being compared
        delta: Difference in metric values (method_b - method_a)
        query_text: The original query text
    """
    query_id: str
    method_a: RetrievalMethod
    method_b: RetrievalMethod
    metric: str
    delta: float
    query_text: Optional[str] = None
