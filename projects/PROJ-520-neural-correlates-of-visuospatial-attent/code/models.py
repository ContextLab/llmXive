"""
Data models for the neural correlates pipeline.
Defines core entities used throughout the analysis.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np


@dataclass
class Epoch:
    """Represents a single EEG epoch (time window around an event)."""
    data: np.ndarray  # Shape: (n_channels, n_times)
    event_type: str   # 'active' or 'passive'
    event_id: int     # Original event ID from BIDS
    electrode_labels: List[str]  # Channel names
    time: np.ndarray  # Time vector relative to event onset
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_power(self, freq_range: tuple) -> float:
        """Calculate mean power in a frequency range (placeholder for actual calculation)."""
        # This would be implemented using MNE or scipy
        raise NotImplementedError("Power calculation requires signal processing")


@dataclass
class Feature:
    """Represents a single extracted feature from an epoch."""
    name: str           # Feature name (e.g., "alpha_Pz")
    value: float        # Feature value
    electrode: str      # Electrode name
    band: str           # Frequency band (e.g., "alpha", "beta")
    epoch_id: int       # ID of source epoch
    condition: str      # Condition label
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "value": self.value,
            "electrode": self.electrode,
            "band": self.band,
            "epoch_id": self.epoch_id,
            "condition": self.condition
        }


@dataclass
class ClassifierResult:
    """Results from a classification experiment."""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: np.ndarray
    cross_val_scores: List[float]
    model_params: Dict[str, Any]
    feature_importance: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "cross_val_scores": self.cross_val_scores,
            "model_params": self.model_params,
            "feature_importance": self.feature_importance
        }


@dataclass
class PermutationResult:
    """Results from permutation testing."""
    p_value: float
    null_distribution: np.ndarray
    observed_statistic: float
    n_permutations: int
    significant: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "p_value": self.p_value,
            "n_permutations": self.n_permutations,
            "observed_statistic": float(self.observed_statistic),
            "significant": self.significant
        }


@dataclass
class PreprocessingReport:
    """Report on preprocessing pipeline execution."""
    n_epochs_total: int
    n_epochs_active: int
    n_epochs_passive: int
    rejected_components: List[int]
    skipped_electrodes: List[str]
    event_source: str  # 'bids' or 'landmark_fallback'
    processing_time_seconds: float
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "n_epochs_total": self.n_epochs_total,
            "n_epochs_active": self.n_epochs_active,
            "n_epochs_passive": self.n_epochs_passive,
            "rejected_components": self.rejected_components,
            "skipped_electrodes": self.skipped_electrodes,
            "event_source": self.event_source,
            "processing_time_seconds": self.processing_time_seconds,
            "warnings": self.warnings
        }


@dataclass
class FeatureMetadata:
    """Metadata about extracted features."""
    n_features: int
    n_epochs: int
    electrode_band_pairs: List[Dict[str, str]]
    correlation_matrix: Optional[np.ndarray] = None
    vif_values: Optional[Dict[str, float]] = None
    fwe_corrected_p_values: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "n_features": self.n_features,
            "n_epochs": self.n_epochs,
            "electrode_band_pairs": self.electrode_band_pairs,
            "fwe_corrected_p_values": self.fwe_corrected_p_values
        }
        if self.correlation_matrix is not None:
            result["correlation_matrix"] = self.correlation_matrix.tolist()
        if self.vif_values is not None:
            result["vif_values"] = self.vif_values
        return result
