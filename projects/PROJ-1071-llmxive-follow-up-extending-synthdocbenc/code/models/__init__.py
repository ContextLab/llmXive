"""
Data models and schema validators for the SynthDocBench pipeline.
"""
from .base import BaseModel
from .document import MiddleThirdMetadata, Page, Document
from .evaluation import EvaluationResult, BaselineMetrics, RetrievalMetrics
from .stats import StatisticalResult
from .validators import validate_document_schema, validate_evaluation_schema, validate_stats_schema

__all__ = [
    "BaseModel",
    "MiddleThirdMetadata",
    "Page",
    "Document",
    "EvaluationResult",
    "BaselineMetrics",
    "RetrievalMetrics",
    "StatisticalResult",
    "validate_document_schema",
    "validate_evaluation_schema",
    "validate_stats_schema",
]
