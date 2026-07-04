from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Union
import json

@dataclass
class Participant:
    id: str
    disability_type: str
    interface_sequence: List[str]

@dataclass
class Session:
    session_id: str
    participant_id: str
    interface_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    error_count: int = 0
    explanation_engagement_time_seconds: float = 0.0
    sus_score: Optional[float] = None
    skip_count: int = 0
    status: str = "in_progress"

@dataclass
class Metric:
    metric_name: str
    interface_type: str
    mean: float
    std_dev: float
    p_value: Optional[float] = None
    confidence_interval: Optional[tuple] = None
    test_method: Optional[str] = None

def main():
    print("Data models loaded.")
