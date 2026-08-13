from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import json

@dataclass
class Participant:
    participant_id: str
    age: int
    gender: Optional[str] = None
    device_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    calibration_error_margin: Optional[float] = None

@dataclass
class NoiseLog:
    log_id: str
    participant_id: str
    timestamp: datetime
    decibels: float
    device_id: Optional[str] = None

@dataclass
class TaskPerformance:
    performance_id: str
    participant_id: str
    task_id: str
    reaction_time_ms: float
    error_count: int
    timestamp: datetime

def participants_to_json(participants: List[Participant]) -> str:
    return json.dumps([{k: v.isoformat() if isinstance(v, datetime) else v for k, v in p.__dict__.items()} for p in participants], indent=2)

def noise_logs_to_json(logs: List[NoiseLog]) -> str:
    return json.dumps([{k: v.isoformat() if isinstance(v, datetime) else v for k, v in l.__dict__.items()} for l in logs], indent=2)

def task_performances_to_json(performances: List[TaskPerformance]) -> str:
    return json.dumps([{k: v.isoformat() if isinstance(v, datetime) else v for k, v in p.__dict__.items()} for p in performances], indent=2)
