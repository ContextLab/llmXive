"""
Models package for EEG data structures.
"""
from .eeg_dataset import EEGDataset
from .alpha_power import AlphaPowerMetric
from .plv_metric import PLVMetric
from .wm_capacity import WMCapacity

__all__ = [
    'EEGDataset',
    'AlphaPowerMetric',
    'PLVMetric',
    'WMCapacity'
]
