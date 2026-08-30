from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


@dataclass
class Subject:
    """
    Represents a single research subject with demographic and behavioral data.

    Attributes:
        subject_id (str): Unique identifier for the subject (e.g., '100307').
        dsrt_score (float): Decision Risk-Taking score from the DSRT task.
        age (float): Age of the subject in years.
        sex (str): Biological sex of the subject (e.g., 'M', 'F').
        mean_fd (float): Mean Framewise Displacement, a measure of head motion during fMRI.
    """
    subject_id: str
    dsrt_score: float
    age: float
    sex: str
    mean_fd: float

    def __post_init__(self):
        # Ensure numeric fields are floats
        if not isinstance(self.dsrt_score, (int, float)):
            raise TypeError("dsrt_score must be numeric")
        if not isinstance(self.age, (int, float)):
            raise TypeError("age must be numeric")
        if not isinstance(self.mean_fd, (int, float)):
            raise TypeError("mean_fd must be numeric")
        if not isinstance(self.subject_id, str):
            raise TypeError("subject_id must be a string")
        if not isinstance(self.sex, str):
            raise TypeError("sex must be a string")


@dataclass
class Parcel:
    """
    Represents a cortical parcel (ROI) with its associated fMRI time series.

    Attributes:
        parcel_id (str): Unique identifier for the parcel (e.g., 'Parcel_001').
        time_series (np.ndarray): 1D numpy array representing the BOLD signal time course.
    """
    parcel_id: str
    time_series: np.ndarray = field(default_factory=lambda: np.array([]))

    def __post_init__(self):
        if not isinstance(self.parcel_id, str):
            raise TypeError("parcel_id must be a string")
        if not isinstance(self.time_series, np.ndarray):
            raise TypeError("time_series must be a numpy.ndarray")
        if self.time_series.ndim != 1:
            raise ValueError("time_series must be a 1D array")

    def get_length(self) -> int:
        """Return the number of timepoints in the series."""
        return len(self.time_series)

    def is_valid(self) -> bool:
        """Check if the parcel has a valid, non-empty time series."""
        return len(self.time_series) > 0 and not np.all(np.isnan(self.time_series))