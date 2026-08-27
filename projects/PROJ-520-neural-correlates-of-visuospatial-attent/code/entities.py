from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np

@dataclass
class Epoch:
    """Represents a single EEG epoch."""
    id: str
    condition: str
    start_time: float
    end_time: float
    data: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Feature:
    """Represents a single extracted feature."""
    name: str
    electrode: str
    frequency_band: str
    value: float
    epoch_id: str

@dataclass
class ClassifierResult:
    """Represents classification results."""
    accuracy: float
    precision: float
    recall: float
    cv_mean_accuracy: float
    cv_std_accuracy: float
    cv_scores: List[float]

@dataclass
class PermutationResult:
    """Represents permutation testing results."""
    observed_accuracy: float
    p_value: float
    is_significant: bool
    n_permutations: int
    null_distribution_mean: float
    null_distribution_std: float
    null_distribution: List[float]

@dataclass
class PreprocessingReport:
    """Report of preprocessing steps and outcomes."""
    total_epochs: int
    rejected_epochs: int
    skipped_electrodes: List[str]
    event_source: str
    assumptions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeatureMetadata:
    """Metadata about extracted features."""
    electrode_collinearity: Dict[str, float]
    correlation_structure: Dict[str, Dict[str, float]]
    fwe_corrected_p_values: Optional[Dict[str, float]] = None
