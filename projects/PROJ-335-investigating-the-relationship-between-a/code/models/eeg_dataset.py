"""
Data model for EEG Dataset entities.
Represents a loaded and preprocessed EEG dataset from OpenNeuro (e.g., ds000248).
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class EEGDataset:
    """
    Represents a single EEG dataset participant or the aggregate dataset.
    
    Attributes:
        subject_id: Unique identifier for the subject (e.g., 'sub-01').
        raw_data: Raw EEG data array (n_channels, n_times).
        info: MNE info object or dictionary containing channel metadata.
        events: Event array (n_events, 3) containing time, duration, and type.
        epochs: Epochs data array (n_epochs, n_channels, n_times) if segmented.
        behavioral_scores: Dictionary of behavioral metrics (e.g., k-score, d-prime).
        preprocessing_steps: List of preprocessing steps applied.
        bids_path: Path to the BIDS-compliant file on disk.
    """
    subject_id: str
    raw_data: Optional[np.ndarray] = None
    info: Optional[Dict[str, Any]] = None
    events: Optional[np.ndarray] = None
    epochs: Optional[np.ndarray] = None
    behavioral_scores: Dict[str, float] = field(default_factory=dict)
    preprocessing_steps: List[str] = field(default_factory=list)
    bids_path: Optional[str] = None

    def add_preprocessing_step(self, step_name: str) -> None:
        """Records a preprocessing step applied to this dataset."""
        self.preprocessing_steps.append(step_name)
        logger.info(f"Applied preprocessing step '{step_name}' to subject {self.subject_id}")

    def set_epochs(self, epochs_data: np.ndarray) -> None:
        """Sets the epochs data and marks the dataset as segmented."""
        self.epochs = epochs_data
        self.add_preprocessing_step("segmentation")

    def set_behavioral_score(self, metric_name: str, value: float) -> None:
        """Sets a behavioral score for this subject."""
        self.behavioral_scores[metric_name] = value
        logger.debug(f"Set {metric_name} = {value} for subject {self.subject_id}")

    def validate(self) -> bool:
        """
        Basic validation of the dataset structure.
        Returns True if essential fields are present.
        """
        if not self.subject_id:
            logger.error("Validation failed: subject_id is missing")
            return False
        
        if self.raw_data is None and self.epochs is None:
            logger.error("Validation failed: No data (raw or epochs) present")
            return False

        if self.info is None:
            logger.warning("Validation warning: Channel info (info) is missing")
            # Not strictly fatal if raw_data exists, but good practice
        
        return True
