"""
Models package for EEG complexity analysis pipeline.
"""
from .eeg_segment import EEGSegment
from .complexity_metric import MetricType, ComplexityMetric

__all__ = [
    'EEGSegment',
    'MetricType',
    'ComplexityMetric'
]
