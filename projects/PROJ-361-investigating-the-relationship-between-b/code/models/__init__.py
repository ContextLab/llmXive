"""
Data models for the llmXive automated science pipeline.
Contains dataclasses for Subject, ConnectivityMatrix, TopologyMetrics, and IllusionScore.
"""
from .subject import Subject, SubjectStatus
from .connectivity import ConnectivityMatrix
from .topology import TopologyMetrics
from .behavioral import IllusionScore

__all__ = [
    "Subject",
    "SubjectStatus",
    "ConnectivityMatrix",
    "TopologyMetrics",
    "IllusionScore",
]
