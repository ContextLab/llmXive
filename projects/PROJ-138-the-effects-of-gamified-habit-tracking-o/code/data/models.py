"""
Data models.
Implements T007.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    user_id: str
    gamification_status: bool
    conscientiousness_score: float

@dataclass
class BehavioralLog:
    user_id: str
    date: datetime
    event_type: str

@dataclass
class WeeklyAggregation:
    user_id: str
    week_number: int
    adherence_flag: int
    conscientiousness_score: Optional[float] = None
    gamification_status: Optional[bool] = None