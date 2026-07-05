"""
Models package for EEG cognitive fatigue analysis.
Exports base data models for EEG segments and complexity metrics.
"""
from .eeg_segment import EEGSegment
from .complexity_metric import ComplexityMetric, MetricType

__all__ = [
    "EEGSegment",
    "ComplexityMetric",
    "MetricType"
]
