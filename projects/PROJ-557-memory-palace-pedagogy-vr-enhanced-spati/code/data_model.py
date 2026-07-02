"""
Data Model Schema for Memory Load-Adaptive Text Presentation.

Defines the core entities: Participant, Passage, Window, and AdaptationLabel.
Explicitly handles the limitation that the source dataset (ds004041) lacks
simplified text by defining `simplified_text` as nullable.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
import uuid


class PassageType(Enum):
    """Enumeration of passage types found in the dataset."""
    ORIGINAL = "original"
    # Simplified text is not present in the source dataset;
    # if generated later (counterfactual), it is treated as a derived type.
    SIMULATED_SIMPLIFIED = "simulated_simplified"


@dataclass
class Participant:
    """
    Represents a participant in the study.

    Attributes:
        participant_id: Unique identifier for the participant.
        age: Age of the participant (optional).
        gender: Gender of the participant (optional).
        group: Experimental group assignment (e.g., 'control', 'adaptive').
    """
    participant_id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    group: Optional[str] = None

    def __post_init__(self):
        if not self.participant_id:
            raise ValueError("participant_id cannot be empty")


@dataclass
class Passage:
    """
    Represents a text passage used in the experiment.

    Attributes:
        passage_id: Unique identifier for the passage.
        original_text: The full text of the passage as presented in the source dataset.
        simplified_text: The simplified version of the text.
                           NOTE: In the source dataset (ds004041), this is NULL/None.
                           It is only populated if counterfactual generation (T021b)
                           is performed.
        passage_type: The type of the passage (original or simulated_simplified).
    """
    passage_id: str
    original_text: str
    simplified_text: Optional[str] = None
    passage_type: PassageType = PassageType.ORIGINAL

    def __post_init__(self):
        if not self.passage_id:
            raise ValueError("passage_id cannot be empty")
        if not self.original_text:
            raise ValueError("original_text cannot be empty")


@dataclass
class Window:
    """
    Represents a time window of pupil data and associated context.

    Attributes:
        window_id: Unique identifier for the window.
        participant_id: Reference to the Participant.
        passage_id: Reference to the Passage.
        start_time: Start time of the window in seconds relative to trial start.
        end_time: End time of the window in seconds relative to trial start.
        pupil_diameter: Mean pupil diameter during the window (in mm).
        blink_rate: Number of blinks detected in the window.
        luminance: Mean screen luminance during the window (in cd/m^2).
        cli_score: Cognitive Load Index (z-score) for this window.
        is_high_load: Boolean flag indicating if CLI > threshold (0.5 SD).
    """
    window_id: str
    participant_id: str
    passage_id: str
    start_time: float
    end_time: float
    pupil_diameter: float
    blink_rate: int
    luminance: float
    cli_score: Optional[float] = None
    is_high_load: bool = False

    def __post_init__(self):
        if not self.window_id:
            raise ValueError("window_id cannot be empty")


@dataclass
class AdaptationLabel:
    """
    Represents the adaptation label assigned to a specific window.

    This entity determines which version of the text (original vs. simplified)
    would be presented in a real-time adaptive system.

    Attributes:
        label_id: Unique identifier for the label record.
        window_id: Reference to the Window.
        adaptation_type: 'adaptive' if simplified text was selected, 'control' otherwise.
        selected_text_id: The passage_id of the text actually selected for presentation.
        fallback_reason: If graceful degradation occurred (e.g., missing simplified text),
                         this field explains why the original was used.
    """
    label_id: str
    window_id: str
    adaptation_type: str  # 'adaptive' or 'control'
    selected_text_id: str
    fallback_reason: Optional[str] = None

    def __post_init__(self):
        if not self.label_id:
            raise ValueError("label_id cannot be empty")
        if not self.window_id:
            raise ValueError("window_id cannot be empty")
        if self.adaptation_type not in ('adaptive', 'control'):
            raise ValueError("adaptation_type must be 'adaptive' or 'control'")