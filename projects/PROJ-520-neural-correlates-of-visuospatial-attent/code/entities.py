"""
Data entity definitions for the project.
Defines structures for Epoch, Feature, and PermutationResult.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np


@dataclass
class Epoch:
    """
    Represents a single time-locked EEG epoch.
    
    Attributes:
        subject_id: Identifier for the subject.
        condition: Task condition (e.g., 'active', 'passive').
        data: Raw EEG data array (n_channels, n_times).
        times: Time points in seconds relative to event onset.
        events: Original event information (if available).
        metadata: Additional dictionary for storing epoch-specific info.
    """
    subject_id: str
    condition: str
    data: np.ndarray
    times: np.ndarray
    events: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.data, np.ndarray):
            raise TypeError("Epoch data must be a numpy array.")
        if not isinstance(self.times, np.ndarray):
            raise TypeError("Epoch times must be a numpy array.")


@dataclass
class Feature:
    """
    Represents an extracted feature from an epoch.
    
    Attributes:
        subject_id: Identifier for the subject.
        epoch_id: Unique identifier or index for the source epoch.
        condition: Task condition associated with the epoch.
        feature_name: Name of the feature (e.g., 'alpha_power_pz').
        value: The numerical value of the feature.
        band: Frequency band (e.g., 'alpha', 'beta').
        electrode: Electrode name (e.g., 'Pz', 'F3').
    """
    subject_id: str
    epoch_id: int
    condition: str
    feature_name: str
    value: float
    band: Optional[str] = None
    electrode: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the feature to a dictionary for serialization."""
        return {
            "subject_id": self.subject_id,
            "epoch_id": self.epoch_id,
            "condition": self.condition,
            "feature_name": self.feature_name,
            "value": self.value,
            "band": self.band,
            "electrode": self.electrode
        }


@dataclass
class PermutationResult:
    """
    Represents the result of a permutation test.
    
    Attributes:
        observed_statistic: The statistic calculated on the original labels.
        permuted_statistics: List of statistics calculated on permuted labels.
        p_value: Calculated p-value (one-tailed).
        n_permutations: Total number of permutations performed.
    """
    observed_statistic: float
    permuted_statistics: List[float]
    p_value: float
    n_permutations: int

    def __post_init__(self):
        if not isinstance(self.permuted_statistics, list):
            self.permuted_statistics = list(self.permuted_statistics)
        
        if self.n_permutations == 0:
            self.p_value = 0.0
        else:
            # Calculate one-tailed p-value: (count >= observed + 1) / (n + 1)
            count = sum(1 for s in self.permuted_statistics if s >= self.observed_statistic)
            self.p_value = (count + 1) / (self.n_permutations + 1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary for serialization."""
        return {
            "observed_statistic": self.observed_statistic,
            "p_value": self.p_value,
            "n_permutations": self.n_permutations,
            "permuted_statistics_count": len(self.permuted_statistics)
        }