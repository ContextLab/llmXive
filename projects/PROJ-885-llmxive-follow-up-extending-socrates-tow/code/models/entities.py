"""
Core data entities for the Dynamic Socio-Cognitive State Injection pipeline.

This module defines the immutable data structures used to represent
conflict trajectories and the socio-cognitive states injected into them.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import uuid


class EmotionalReactivityLevel(Enum):
    """Levels of emotional reactivity in a dialogue participant."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CulturalIdentityDiversity(Enum):
    """Levels of cultural identity diversity in a dialogue participant."""
    MONOCULTURAL = "monocultural"
    BICULTURAL = "bicultural"
    MULTICULTURAL = "multicultural"


class SocioCognitiveStateType(Enum):
    """Types of socio-cognitive states that can be injected."""
    DE_ESCALATION = "de-escalate"
    CULTURAL_VALIDATION = "validate_cultural_norms"
    EMPATHY_BUILDING = "empathy_building"
    NEUTRAL_MONITORING = "neutral_monitoring"
    COGNITIVE_REFRAMING = "cognitive_reframing"


@dataclass(frozen=True)
class SocioCognitiveState:
    """
    Represents a specific socio-cognitive state to be injected into the LLM.

    Attributes:
        state_type: The type of state (e.g., de-escalation, cultural validation).
        intensity: A float between 0.0 and 1.0 representing the intensity of the state.
        target_attribute: The specific attribute being targeted (e.g., "emotional_reactivity").
        description: A natural language description of the state for logging/debugging.
        created_at: Timestamp of state creation.
    """
    state_type: SocioCognitiveStateType
    intensity: float
    target_attribute: str
    description: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate intensity is within bounds."""
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError(f"Intensity must be between 0.0 and 1.0, got {self.intensity}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the state to a dictionary for serialization."""
        return {
            "state_type": self.state_type.value,
            "intensity": self.intensity,
            "target_attribute": self.target_attribute,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ConflictTrajectory:
    """
    Represents a complete conflict dialogue trajectory with metadata.

    A trajectory consists of a sequence of turns, participant metadata,
    and the socio-cognitive states associated with it.

    Attributes:
        trajectory_id: Unique identifier for the trajectory.
        participant_a_id: Identifier for the first participant.
        participant_b_id: Identifier for the second participant.
        turns: List of dialogue turns in chronological order.
        metadata: Additional metadata (e.g., conflict topic, duration).
        emotional_reactivity: The emotional reactivity level of the scenario.
        cultural_identity_diversity: The cultural diversity level of the scenario.
        injected_states: List of socio-cognitive states injected during the trajectory.
        created_at: Timestamp of trajectory creation.
    """
    trajectory_id: str
    participant_a_id: str
    participant_b_id: str
    turns: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    emotional_reactivity: EmotionalReactivityLevel = EmotionalReactivityLevel.MEDIUM
    cultural_identity_diversity: CulturalIdentityDiversity = CulturalIdentityDiversity.MONOCULTURAL
    injected_states: List[SocioCognitiveState] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Ensure trajectory_id is valid."""
        if not self.trajectory_id:
            raise ValueError("trajectory_id cannot be empty")
        if not self.turns:
            raise ValueError("turns cannot be empty")

    def add_turn(self, turn: Dict[str, Any]) -> None:
        """
        Add a turn to the trajectory.

        Args:
            turn: A dictionary containing turn data (speaker, text, timestamp).
        """
        self.turns.append(turn)

    def add_injected_state(self, state: SocioCognitiveState) -> None:
        """
        Add a socio-cognitive state to the trajectory.

        Args:
            state: The SocioCognitiveState to add.
        """
        self.injected_states.append(state)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the trajectory to a dictionary for serialization."""
        return {
            "trajectory_id": self.trajectory_id,
            "participant_a_id": self.participant_a_id,
            "participant_b_id": self.participant_b_id,
            "turns": self.turns,
            "metadata": self.metadata,
            "emotional_reactivity": self.emotional_reactivity.value,
            "cultural_identity_diversity": self.cultural_identity_diversity.value,
            "injected_states": [s.to_dict() for s in self.injected_states],
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConflictTrajectory":
        """
        Create a ConflictTrajectory from a dictionary.

        Args:
            data: The dictionary containing trajectory data.

        Returns:
            A ConflictTrajectory instance.
        """
        # Parse enums
        emotional_reactivity = EmotionalReactivityLevel(data["emotional_reactivity"])
        cultural_identity_diversity = CulturalIdentityDiversity(data["cultural_identity_diversity"])

        # Parse states
        states = []
        for s_data in data.get("injected_states", []):
            states.append(
                SocioCognitiveState(
                    state_type=SocioCognitiveStateType(s_data["state_type"]),
                    intensity=s_data["intensity"],
                    target_attribute=s_data["target_attribute"],
                    description=s_data["description"],
                    created_at=datetime.fromisoformat(s_data["created_at"]),
                )
            )

        # Parse timestamp
        created_at = datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat()))

        return cls(
            trajectory_id=data["trajectory_id"],
            participant_a_id=data["participant_a_id"],
            participant_b_id=data["participant_b_id"],
            turns=data["turns"],
            metadata=data.get("metadata", {}),
            emotional_reactivity=emotional_reactivity,
            cultural_identity_diversity=cultural_identity_diversity,
            injected_states=states,
            created_at=created_at,
        )