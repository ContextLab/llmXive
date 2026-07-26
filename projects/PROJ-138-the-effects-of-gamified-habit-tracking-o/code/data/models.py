"""
Data models for the project.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    user_id: str
    gamification_status: bool
    conscientiousness_score: float
    need_for_achievement: Optional[float] = None

@dataclass
class BehavioralLog:
    user_id: str
    date: datetime
    event_type: str
    adherence_flag: int = 1

@dataclass
class WeeklyAggregation:
    user_id: str
    week_number: int
    adherence_flag: int
    total_events: int
