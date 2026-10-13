"""
Base data classes/entities for the ambient noise project.

Defines Participant, NoiseLog, and TaskPerformance entities
matching the Key Entities in spec.md.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import json


@dataclass
class Participant:
    """Represents a remote worker in the study."""
    participant_id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    job_type: Optional[str] = None
    noise_sensitivity_score: Optional[float] = None
    baseline_cognitive_score: Optional[float] = None
    consent_date: Optional[str] = None
    calibration_status: Optional[str] = None
    calibration_error_margin: Optional[float] = None


@dataclass
class NoiseLog:
    """Represents a time-series record of acoustic environment."""
    participant_id: str
    timestamp: str
    decibel_level: float
    device_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class TaskPerformance:
    """Represents a single cognitive task session."""
    participant_id: str
    trial_id: str
    task_type: str  # 'switch' or 'repeat'
    reaction_time: float  # in milliseconds
    error: bool  # True if error occurred
    session_timestamp: str
    session_id: Optional[str] = None


def participants_to_json(participants: List[Participant]) -> str:
    """
    Convert a list of Participant objects to JSON string.
    
    Args:
        participants: List of Participant objects.
    
    Returns:
        JSON string representation.
    """
    return json.dumps(
        [p.__dict__ for p in participants],
        indent=2
    )


def noise_logs_to_json(logs: List[NoiseLog]) -> str:
    """
    Convert a list of NoiseLog objects to JSON string.
    
    Args:
        logs: List of NoiseLog objects.
    
    Returns:
        JSON string representation.
    """
    return json.dumps(
        [log.__dict__ for log in logs],
        indent=2
    )


def task_performances_to_json(performances: List[TaskPerformance]) -> str:
    """
    Convert a list of TaskPerformance objects to JSON string.
    
    Args:
        performances: List of TaskPerformance objects.
    
    Returns:
        JSON string representation.
    """
    return json.dumps(
        [perf.__dict__ for perf in performances],
        indent=2
    )
