"""
Data models for the Visual Priming study.
Defines core entities: Trial, Participant, and Stimulus.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import json
from pathlib import Path


class StimulusType(Enum):
    """Enumeration of stimulus categories."""
    PRIME = "prime"
    TARGET = "target"


@dataclass
class Stimulus:
    """
    Represents a single visual stimulus (image).
    Corresponds to files in data/primes/ or data/targets/.
    """
    stimulus_id: str
    stimulus_type: StimulusType
    file_path: str
    valence: Optional[float] = None  # -1 (negative) to 1 (positive)
    ambiguity: Optional[float] = None  # 0 (unambiguous) to 1 (ambiguous)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "stimulus_id": self.stimulus_id,
            "stimulus_type": self.stimulus_type.value,
            "file_path": self.file_path,
            "valence": self.valence,
            "ambiguity": self.ambiguity,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Stimulus":
        """Create instance from dictionary."""
        stimulus_type = StimulusType(data["stimulus_type"])
        return cls(
            stimulus_id=data["stimulus_id"],
            stimulus_type=stimulus_type,
            file_path=data["file_path"],
            valence=data.get("valence"),
            ambiguity=data.get("ambiguity"),
            metadata=data.get("metadata", {})
        )


@dataclass
class Participant:
    """
    Represents a study participant.
    Contains aggregated data and demographics.
    """
    participant_id: str
    demographic_data: Dict[str, Any] = field(default_factory=dict)
    trials: List["Trial"] = field(default_factory=list)

    def add_trial(self, trial: "Trial") -> None:
        """Add a trial to this participant's history."""
        self.trials.append(trial)

    def get_trial_count(self) -> int:
        """Return the number of trials for this participant."""
        return len(self.trials)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "participant_id": self.participant_id,
            "demographic_data": self.demographic_data,
            "trial_count": self.get_trial_count()
        }


@dataclass
class Trial:
    """
    Represents a single experimental trial.
    Links a participant, a prime, and a target stimulus.
    """
    trial_id: str
    participant_id: str
    prime_stimulus_id: str
    target_stimulus_id: str
    response_time_ms: float
    accuracy: Optional[bool] = None
    prime_condition: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "trial_id": self.trial_id,
            "participant_id": self.participant_id,
            "prime_stimulus_id": self.prime_stimulus_id,
            "target_stimulus_id": self.target_stimulus_id,
            "response_time_ms": self.response_time_ms,
            "accuracy": self.accuracy,
            "prime_condition": self.prime_condition,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trial":
        """Create instance from dictionary."""
        return cls(
            trial_id=data["trial_id"],
            participant_id=data["participant_id"],
            prime_stimulus_id=data["prime_stimulus_id"],
            target_stimulus_id=data["target_stimulus_id"],
            response_time_ms=data["response_time_ms"],
            accuracy=data.get("accuracy"),
            prime_condition=data.get("prime_condition"),
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata", {})
        )


# Helper functions for bulk operations
def save_trials_to_json(trials: List[Trial], output_path: Path) -> None:
    """Serialize a list of Trial objects to a JSON file."""
    data = [t.to_dict() for t in trials]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_trials_from_json(input_path: Path) -> List[Trial]:
    """Deserialize a list of Trial objects from a JSON file."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Trial.from_dict(item) for item in data]


def save_stimuli_to_json(stimuli: List[Stimulus], output_path: Path) -> None:
    """Serialize a list of Stimulus objects to a JSON file."""
    data = [s.to_dict() for s in stimuli]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_stimuli_from_json(input_path: Path) -> List[Stimulus]:
    """Deserialize a list of Stimulus objects from a JSON file."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Stimulus.from_dict(item) for item in data]
