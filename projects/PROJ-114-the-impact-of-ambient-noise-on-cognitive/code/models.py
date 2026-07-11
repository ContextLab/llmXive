"""
Base data classes/entities for the study.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

@dataclass
class Participant:
    participant_id: str
    device_type: str
    calibration_status: Optional[str] = None
    calibration_error_margin_db: Optional[float] = None
    inclusion_criteria_met: bool = False

@dataclass
class NoiseLog:
    timestamp: datetime
    participant_id: str
    decibel_level: float
    device_type: str
    is_valid: bool = True  # Flag for gaps or anomalies

@dataclass
class TaskPerformance:
    participant_id: str
    session_id: str
    reaction_time_ms: float
    error_count: int
    noise_category: str  # Low, Moderate, High based on FR-001
    cfi_score: Optional[float] = None
