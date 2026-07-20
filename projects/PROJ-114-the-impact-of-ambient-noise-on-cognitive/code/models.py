"""
Base data classes/entities for the study.

These classes represent the core entities defined in the project specification:
Participant, NoiseLog, and TaskPerformance.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import json

@dataclass
class Participant:
    """
    Represents a study participant and their metadata.
    
    Attributes:
        participant_id: Unique identifier for the participant.
        device_type: Type of device used for recording (e.g., 'mobile', 'desktop').
        calibration_status: Status of the device calibration ('ok', 'failed', 'missing').
        calibration_error_margin_db: Error margin in dB from calibration check.
        inclusion_criteria_met: Whether the participant meets all inclusion criteria.
    """
    participant_id: str
    device_type: str
    calibration_status: Optional[str] = None
    calibration_error_margin_db: Optional[float] = None
    inclusion_criteria_met: bool = False

    def to_dict(self) -> dict:
        """Convert the participant object to a dictionary."""
        return {
            'participant_id': self.participant_id,
            'device_type': self.device_type,
            'calibration_status': self.calibration_status,
            'calibration_error_margin_db': self.calibration_error_margin_db,
            'inclusion_criteria_met': self.inclusion_criteria_met
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Participant':
        """Create a Participant instance from a dictionary."""
        return cls(
            participant_id=data['participant_id'],
            device_type=data['device_type'],
            calibration_status=data.get('calibration_status'),
            calibration_error_margin_db=data.get('calibration_error_margin_db'),
            inclusion_criteria_met=data.get('inclusion_criteria_met', False)
        )

@dataclass
class NoiseLog:
    """
    Represents a single noise measurement log entry.
    
    Attributes:
        timestamp: Timestamp of the measurement.
        participant_id: ID of the participant associated with this log.
        decibel_level: Measured noise level in dB.
        device_type: Type of device used for measurement.
        is_valid: Flag indicating if the log entry is valid (not a gap/anomaly).
    """
    timestamp: datetime
    participant_id: str
    decibel_level: float
    device_type: str
    is_valid: bool = True

    def to_dict(self) -> dict:
        """Convert the noise log object to a dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'participant_id': self.participant_id,
            'decibel_level': self.decibel_level,
            'device_type': self.device_type,
            'is_valid': self.is_valid
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'NoiseLog':
        """Create a NoiseLog instance from a dictionary."""
        timestamp_str = data.get('timestamp')
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            timestamp = timestamp_str
        
        return cls(
            timestamp=timestamp,
            participant_id=data['participant_id'],
            decibel_level=float(data['decibel_level']),
            device_type=data['device_type'],
            is_valid=data.get('is_valid', True)
        )

@dataclass
class TaskPerformance:
    """
    Represents a participant's performance on a cognitive flexibility task.
    
    Attributes:
        participant_id: ID of the participant.
        session_id: Unique identifier for the task session.
        reaction_time_ms: Reaction time in milliseconds.
        error_count: Number of errors made during the task.
        noise_category: Category of noise environment (Low, Moderate, High).
        cfi_score: Cognitive Flexibility Index score (calculated metric).
    """
    participant_id: str
    session_id: str
    reaction_time_ms: float
    error_count: int
    noise_category: str
    cfi_score: Optional[float] = None

    def to_dict(self) -> dict:
        """Convert the task performance object to a dictionary."""
        return {
            'participant_id': self.participant_id,
            'session_id': self.session_id,
            'reaction_time_ms': self.reaction_time_ms,
            'error_count': self.error_count,
            'noise_category': self.noise_category,
            'cfi_score': self.cfi_score
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TaskPerformance':
        """Create a TaskPerformance instance from a dictionary."""
        return cls(
            participant_id=data['participant_id'],
            session_id=data['session_id'],
            reaction_time_ms=float(data['reaction_time_ms']),
            error_count=int(data['error_count']),
            noise_category=data['noise_category'],
            cfi_score=data.get('cfi_score')
        )

# Utility functions for bulk conversion
def participants_to_json(participants: List[Participant]) -> str:
    """Convert a list of Participants to a JSON string."""
    return json.dumps([p.to_dict() for p in participants], indent=2)

def noise_logs_to_json(logs: List[NoiseLog]) -> str:
    """Convert a list of NoiseLogs to a JSON string."""
    return json.dumps([l.to_dict() for l in logs], indent=2)

def task_performances_to_json(perfs: List[TaskPerformance]) -> str:
    """Convert a list of TaskPerformances to a JSON string."""
    return json.dumps([p.to_dict() for p in perfs], indent=2)