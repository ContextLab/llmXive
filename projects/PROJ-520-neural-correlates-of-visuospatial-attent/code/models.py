"""
Data model entities.
Defines core data structures for the pipeline.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np

@dataclass
class Epoch:
    """Represents a single epoch of EEG data."""
    id: str
    condition: str
    start_time: float
    data: np.ndarray
    info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Feature:
    """Represents a single extracted feature."""
    name: str
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ClassifierResult:
    """Stores classification metrics."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: np.ndarray
    cross_val_scores: List[float] = field(default_factory=list)

@dataclass
class PreprocessingReport:
    """Report on preprocessing steps."""
    n_epochs_total: int
    n_epochs_rejected: int
    rejected_components: List[int] = field(default_factory=list)
    skipped_electrodes: List[str] = field(default_factory=list)
    event_source: str = "direct" # or "landmark_fallback"

@dataclass
class FeatureMetadata:
    """Metadata about the extracted feature matrix."""
    n_epochs: int
    n_features: int
    electrode_list: List[str]
    frequency_bands: List[str]
    feature_names: List[str] = field(default_factory=list)
    fwe_corrected_p_values: Dict[str, float] = field(default_factory=dict)

@dataclass
class PermutationResult:
    """Result of permutation testing."""
    p_value: float
    null_distribution: np.ndarray
    observed_statistic: float
    n_permutations: int
    significant: bool