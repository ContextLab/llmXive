"""
Data models for the Pupil Dilation and Cognitive Load research pipeline.

Defines core data structures for dataset records and model results.
"""

from dataclasses import dataclass
from typing import List, Optional, Union
import numpy as np


@dataclass
class Dataset:
    """
    Represents a single trial record in the eye-tracking dataset.

    Attributes:
        subject_id (str): Unique identifier for the participant.
        trial_id (str): Unique identifier for the specific trial.
        timestamp (float): Time in seconds relative to trial start.
        pupil_diameter (float): Measured pupil diameter in millimeters (or arbitrary units).
        x (float): Horizontal gaze coordinate.
        y (float): Vertical gaze coordinate.
        search_time (float): Time taken to locate the target (in seconds).
        target_salience (float): Computed salience value of the target (0.0 to 1.0).
                               Can be None if not computable.
        fixation_count (int): Number of fixations detected during the trial.
    """
    subject_id: str
    trial_id: str
    timestamp: float
    pupil_diameter: float
    x: float
    y: float
    search_time: float
    target_salience: Optional[float] = None
    fixation_count: int = 0

    def to_dict(self) -> dict:
        """Converts the record to a dictionary for serialization."""
        return {
            "subject_id": self.subject_id,
            "trial_id": self.trial_id,
            "timestamp": self.timestamp,
            "pupil_diameter": self.pupil_diameter,
            "x": self.x,
            "y": self.y,
            "search_time": self.search_time,
            "target_salience": self.target_salience,
            "fixation_count": self.fixation_count
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Dataset":
        """Creates a Dataset instance from a dictionary."""
        return cls(
            subject_id=data["subject_id"],
            trial_id=data["trial_id"],
            timestamp=data["timestamp"],
            pupil_diameter=data["pupil_diameter"],
            x=data["x"],
            y=data["y"],
            search_time=data["search_time"],
            target_salience=data.get("target_salience"),
            fixation_count=data.get("fixation_count", 0)
        )


@dataclass
class ModelResult:
    """
    Represents the output of a statistical model fit (e.g., Linear Mixed Effects).

    Attributes:
        coefficients (dict): Mapping of predictor names to their estimated coefficients.
        std_errors (dict): Mapping of predictor names to their standard errors.
        p_values (dict): Mapping of predictor names to their p-values.
        log_likelihood (float): The log-likelihood of the fitted model.
    """
    coefficients: dict
    std_errors: dict
    p_values: dict
    log_likelihood: float

    def __post_init__(self):
        """Validates that all dictionaries have matching keys."""
        if not (
            set(self.coefficients.keys()) == set(self.std_errors.keys()) == set(self.p_values.keys())
        ):
            raise ValueError(
                "Coefficient, std_error, and p_value dictionaries must have identical keys."
            )

    def to_summary_dict(self) -> dict:
        """
        Flattens the result into a single dictionary suitable for CSV export.
        Keys are formatted as 'predictor__metric'.
        """
        summary = {"log_likelihood": self.log_likelihood}
        for key in self.coefficients.keys():
            summary[f"{key}__coef"] = self.coefficients[key]
            summary[f"{key}__se"] = self.std_errors[key]
            summary[f"{key}__p"] = self.p_values[key]
        return summary

    @classmethod
    def from_arrays(
        cls,
        names: List[str],
        coefs: Union[List[float], np.ndarray],
        ses: Union[List[float], np.ndarray],
        ps: Union[List[float], np.ndarray],
        ll: float
    ) -> "ModelResult":
        """
        Factory method to create a ModelResult from parallel arrays.
        """
        coefs = list(coefs) if isinstance(coefs, np.ndarray) else coefs
        ses = list(ses) if isinstance(ses, np.ndarray) else ses
        ps = list(ps) if isinstance(ps, np.ndarray) else ps

        return cls(
            coefficients=dict(zip(names, coefs)),
            std_errors=dict(zip(names, ses)),
            p_values=dict(zip(names, ps)),
            log_likelihood=ll
        )