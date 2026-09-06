"""
Base data models and schema validators for llmXive project.
Matches contracts/ YAML schemas.
"""
from .base import BaseModel
from .document import Document, Page, MiddleThirdMetadata
from .evaluation import EvaluationResult, BaselineMetrics, RetrievalMetrics
from .stats import StatisticalResult

__all__ = [
    "BaseModel",
    "Document",
    "Page",
    "MiddleThirdMetadata",
    "EvaluationResult",
    "BaselineMetrics",
    "RetrievalMetrics",
    "StatisticalResult",
]
