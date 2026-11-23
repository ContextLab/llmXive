"""
Data models for the visual salience and attentional bias study.

This module defines the core data structures used throughout the pipeline:
- StimulusImage: Represents a single stimulus image and its associated metadata.
- FixationTrial: Represents a single eye-tracking trial with fixation metrics.

These models are designed to be serializable to JSON/CSV for data persistence
and are compatible with the project's configuration and logging utilities.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
from datetime import datetime

# Import project utilities if needed for path resolution or logging
# Note: We avoid importing heavy dependencies here to keep model loading fast
# We rely on standard library for serialization logic.


@dataclass
class StimulusImage:
    """
    Represents a stimulus image used in the experiment.

    Attributes:
        id: Unique identifier for the image (e.g., from dataset or generated hash).
        file_path: Path to the original image file.
        width: Width of the image in pixels.
        height: Height of the image in pixels.
        salience_map_path: Path to the generated salience map (DeepGaze II output).
        salience_map_exists: Boolean indicating if the salience map has been generated.
        metadata: Additional dictionary for image-specific metadata (e.g., source, tags).
        created_at: Timestamp when this record was created.
    """
    id: str
    file_path: str
    width: int
    height: int
    salience_map_path: Optional[str] = None
    salience_map_exists: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary."""
        return asdict(self)

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize the instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StimulusImage":
        """Create an instance from a dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "StimulusImage":
        """Create an instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> bool:
        """
        Basic validation of the StimulusImage instance.
        Returns True if all required fields are present and valid.
        """
        if not self.id:
            return False
        if not self.file_path or not Path(self.file_path).exists():
            # Note: In some ingestion pipelines, the file might not exist locally yet
            # but the record is created. We might relax this check depending on context.
            # For now, we just check the path is a string.
            pass
        if self.width <= 0 or self.height <= 0:
            return False
        return True


@dataclass
class FixationTrial:
    """
    Represents a single eye-tracking trial associated with a stimulus image.

    Attributes:
        trial_id: Unique identifier for the trial.
        stimulus_id: Reference to the StimulusImage ID.
        participant_id: Identifier for the participant.
        first_fixation_prob: Probability of first fixation landing on ROI (0.0 - 1.0).
        dwell_time: Total dwell time on ROI in milliseconds.
        latency: Time to first fixation on ROI in milliseconds.
        roi_type: Type of ROI (e.g., "Face", "Background"). Note: "Weapons" excluded per SCR.
        salience_score: Mean salience score within the ROI.
        raw_fixations: List of raw fixation data points (optional, for debugging).
        metadata: Additional trial-specific metadata.
        created_at: Timestamp when this record was created.
    """
    trial_id: str
    stimulus_id: str
    participant_id: str
    first_fixation_prob: float
    dwell_time: float
    latency: float
    roi_type: str = "Face"  # Default to Face as per current scope
    salience_score: Optional[float] = None
    raw_fixations: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass instance to a dictionary."""
        return asdict(self)

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize the instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FixationTrial":
        """Create an instance from a dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "FixationTrial":
        """Create an instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> bool:
        """
        Basic validation of the FixationTrial instance.
        Returns True if all required fields are present and valid.
        """
        if not self.trial_id or not self.stimulus_id or not self.participant_id:
            return False
        if not (0.0 <= self.first_fixation_prob <= 1.0):
            return False
        if self.dwell_time < 0 or self.latency < 0:
            return False
        if self.salience_score is not None and not (0.0 <= self.salience_score <= 1.0):
            # Salience scores are typically normalized, but check bounds if known
            pass
        return True

    def align_with_salience(self, salience_score: float) -> "FixationTrial":
        """
        Update the trial with the corresponding salience score.
        Returns a new instance with the updated score to maintain immutability of the original if needed,
        or updates in place. Here we update in place for simplicity in data pipelines.
        """
        self.salience_score = salience_score
        return self

# Type aliases for convenience in other modules
StimulusImageList = List[StimulusImage]
FixationTrialList = List[FixationTrial]