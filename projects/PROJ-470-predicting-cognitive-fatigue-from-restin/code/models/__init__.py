"""
Models package for EEG complexity analysis pipeline.
Exports core data structures for EEG segments and complexity metrics.
"""
from .eeg_segment import EEGSegment
from .complexity_metric import ComplexityMetric, MetricType

__all__ = ['EEGSegment', 'ComplexityMetric', 'MetricType']
