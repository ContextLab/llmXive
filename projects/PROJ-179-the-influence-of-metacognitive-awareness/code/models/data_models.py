"""
Data models for the Metacognitive Awareness project.

Defines core entities: Participant and Trial.
These classes structure the data derived from the behavioral dataset
validated in T006 and preprocessed in T012.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class StimulusModality(Enum):
    """Enumeration of stimulus modalities supported in the study."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    UNKNOWN = "unknown"


class SourceLabel(Enum):
    """
    Enumeration of source labels.
    Represents the ground truth of the stimulus origin.
    """
    REAL = "real"
    FABRICATED = "fabricated"
    UNKNOWN = "unknown"


@dataclass
class Participant:
    """
    Represents a study participant.
    
    Attributes:
        participant_id: Unique identifier for the participant.
        age: Age of the participant in years.
        gender: Gender of the participant (stored as string for flexibility).
        working_memory: Working memory capacity score (optional).
        trials: List of trials associated with this participant.
    """
    participant_id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    working_memory: Optional[float] = None
    trials: List['Trial'] = field(default_factory=list)

    def add_trial(self, trial: 'Trial') -> None:
        """Adds a trial to the participant's collection."""
        self.trials.append(trial)

    def get_trial_count(self) -> int:
        """Returns the total number of trials for this participant."""
        return len(self.trials)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the participant to a dictionary representation."""
        return {
            'participant_id': self.participant_id,
            'age': self.age,
            'gender': self.gender,
            'working_memory': self.working_memory,
            'trial_count': self.get_trial_count()
        }


@dataclass
class Trial:
    """
    Represents a single trial in the experiment.
    
    Attributes:
        trial_id: Unique identifier for the trial.
        participant_id: ID of the participant who performed this trial.
        stimulus_modality: The modality of the stimulus (visual/auditory).
        source_label: The ground truth source (real/fabricated).
        participant_response: The response given by the participant.
        confidence_rating: The confidence rating given by the participant (e.g., 1-4).
        reaction_time: Reaction time in seconds (optional).
    """
    trial_id: str
    participant_id: str
    stimulus_modality: StimulusModality
    source_label: SourceLabel
    participant_response: str  # e.g., "real", "fabricated", or mapped to SourceLabel
    confidence_rating: float
    reaction_time: Optional[float] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> 'Trial':
        """
        Factory method to create a Trial from a dictionary row (e.g., from pandas).
        
        Args:
            row: Dictionary containing trial data.
        
        Returns:
            A new Trial instance.
        """
        # Handle potential string inputs for enums
        modality_str = str(row.get('stimulus_modality', 'unknown')).lower()
        try:
            modality = StimulusModality(modality_str)
        except ValueError:
            modality = StimulusModality.UNKNOWN

        source_str = str(row.get('source_label', 'unknown')).lower()
        try:
            source = SourceLabel(source_str)
        except ValueError:
            source = SourceLabel.UNKNOWN

        return cls(
            trial_id=str(row.get('trial_id', str(uuid.uuid4()))),
            participant_id=str(row.get('participant_id')),
            stimulus_modality=modality,
            source_label=source,
            participant_response=str(row.get('participant_response', '')),
            confidence_rating=float(row.get('confidence_rating', 0.0)),
            reaction_time=float(row.get('reaction_time')) if row.get('reaction_time') is not None else None
        )

    def is_correct(self) -> bool:
        """
        Determines if the participant's response matches the ground truth source.
        
        Returns:
            True if the response matches the source_label, False otherwise.
        """
        # Normalize comparison: assume response string matches enum value
        return self.participant_response.lower() == self.source_label.value

    def to_dict(self) -> Dict[str, Any]:
        """Converts the trial to a dictionary representation."""
        return {
            'trial_id': self.trial_id,
            'participant_id': self.participant_id,
            'stimulus_modality': self.stimulus_modality.value,
            'source_label': self.source_label.value,
            'participant_response': self.participant_response,
            'confidence_rating': self.confidence_rating,
            'reaction_time': self.reaction_time,
            'is_correct': self.is_correct()
        }
