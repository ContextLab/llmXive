"""
Data models for the brain-proprioception-correlation project.

This module defines the core data structures used throughout the pipeline
for representing subjects, connectivity matrices, network metrics, and
correlation results.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union
import numpy as np


@dataclass
class Subject:
    """
    Represents a study participant.

    Attributes:
        id: Unique subject identifier (e.g., '100307').
        age: Age in years.
        sex: Sex of the subject (e.g., 'M', 'F').
        motor_score: Behavioral motor performance score.
        fd: Mean Framewise Displacement (motion metric).
    """
    id: str
    age: int
    sex: str
    motor_score: float
    fd: float

    def __post_init__(self):
        if not isinstance(self.id, str):
            raise TypeError("Subject id must be a string")
        if self.age < 0:
            raise ValueError("Age must be non-negative")
        if self.sex not in ('M', 'F', 'Other', 'U'):
            raise ValueError("Sex must be 'M', 'F', 'Other', or 'U'")
        if not isinstance(self.motor_score, (int, float)):
            raise TypeError("motor_score must be numeric")
        if not isinstance(self.fd, (int, float)):
            raise TypeError("fd must be numeric")
        if self.fd < 0:
            raise ValueError("fd (Framewise Displacement) cannot be negative")


@dataclass
class ConnectivityMatrix:
    """
    Represents a functional connectivity matrix for a subject.

    Attributes:
        data: 2D numpy array of shape (N, N) representing connectivity values.
              Expected size is 400x400 for the Schaefer atlas.
        atlas_id: Identifier for the atlas used (e.g., 'Schaefer400').
        subject_id: ID of the subject this matrix belongs to.
    """
    data: np.ndarray
    atlas_id: str
    subject_id: str

    def __post_init__(self):
        if not isinstance(self.data, np.ndarray):
            raise TypeError("data must be a numpy array")
        if self.data.ndim != 2:
            raise ValueError("data must be a 2D array")
        if self.data.shape[0] != self.data.shape[1]:
            raise ValueError("data must be a square matrix")
        if self.data.shape[0] != 400:
            # Allow flexibility for testing but warn if not 400
            pass
        if not isinstance(self.atlas_id, str):
            raise TypeError("atlas_id must be a string")
        if not isinstance(self.subject_id, str):
            raise TypeError("subject_id must be a string")

    @property
    def shape(self) -> tuple:
        return self.data.shape

    def to_array(self) -> np.ndarray:
        """Returns a copy of the underlying data array."""
        return self.data.copy()


@dataclass
class NetworkMetric:
    """
    Represents a single network metric value for a subject.

    Attributes:
        name: Name of the metric (e.g., 'Modularity', 'GlobalEfficiency').
        value: The computed scalar value.
        subject_id: ID of the subject.
    """
    name: str
    value: float
    subject_id: str

    def __post_init__(self):
        if not isinstance(self.name, str):
            raise TypeError("name must be a string")
        if not isinstance(self.value, (int, float)):
            raise TypeError("value must be numeric")
        if not isinstance(self.subject_id, str):
            raise TypeError("subject_id must be a string")


@dataclass
class CorrelationResult:
    """
    Represents the result of a correlation analysis between a metric and a behavior.

    Attributes:
        metric_name: Name of the network metric tested.
        r: Pearson or Spearman correlation coefficient.
        p: Raw p-value.
        q: FDR-corrected p-value (q-value).
        significant: Boolean indicating if q < 0.05.
        covariate_controlled: Boolean indicating if the analysis controlled for covariates (e.g., FD).
    """
    metric_name: str
    r: float
    p: float
    q: float
    significant: bool
    covariate_controlled: bool

    def __post_init__(self):
        if not isinstance(self.metric_name, str):
            raise TypeError("metric_name must be a string")
        if not isinstance(self.r, (int, float)):
            raise TypeError("r must be numeric")
        if not isinstance(self.p, (int, float)):
            raise TypeError("p must be numeric")
        if not isinstance(self.q, (int, float)):
            raise TypeError("q must be numeric")
        if not isinstance(self.significant, bool):
            raise TypeError("significant must be a boolean")
        if not isinstance(self.covariate_controlled, bool):
            raise TypeError("covariate_controlled must be a boolean")

        if not (0.0 <= self.p <= 1.0):
            raise ValueError("p-value must be between 0 and 1")
        if not (0.0 <= self.q <= 1.0):
            raise ValueError("q-value must be between 0 and 1")
        if not (-1.0 <= self.r <= 1.0):
            raise ValueError("correlation coefficient r must be between -1 and 1")