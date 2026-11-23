"""
Data entities for the neural correlates pipeline.

This module defines the data classes used throughout the pipeline to represent
epochs, features, classification results, and metadata.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np

@dataclass
class Epoch:
    """Represents a single EEG epoch."""
    data: np.ndarray
    time: np.ndarray
    condition: str
    electrode_labels: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Feature:
    """Represents a single feature extracted from an epoch."""
    name: str
    value: float
    electrode: str
    band: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ClassifierResult:
    """Represents the result of a classification task."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: np.ndarray
    cv_scores: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PermutationResult:
    """Represents the result of a permutation test."""
    p_value: float
    null_distribution: np.ndarray
    observed_statistic: float
    n_permutations: int
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PreprocessingReport:
    """Report of preprocessing steps applied to the data."""
    n_epochs_total: int
    n_epochs_rejected: int
    rejected_components: List[int] = field(default_factory=list)
    skipped_electrodes: List[str] = field(default_factory=list)
    event_source: str = "raw"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeatureMetadata:
    """Metadata about the extracted features."""
    feature_count: int
    epoch_count: int
    electrodes: Dict[str, List[str]]
    bands: Dict[str, str]
    validation: Dict[str, Any] = field(default_factory=dict)
    fwe_corrected_p_values: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
