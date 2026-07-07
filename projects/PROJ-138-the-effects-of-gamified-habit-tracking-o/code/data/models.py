"""
Data models for the habit tracking study.
Defines User, BehavioralLog, and WeeklyAggregation classes.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    """
    Represents a study participant.
    
    Attributes:
        user_id: Unique identifier for the user.
        gamification_status: True if user uses gamified apps, False otherwise.
        conscientiousness_score: Score on conscientiousness personality trait.
        need_for_achievement: Score on need for achievement scale (optional).
    """
    user_id: str
    gamification_status: bool
    conscientiousness_score: float
    need_for_achievement: Optional[float] = None

@dataclass
class BehavioralLog:
    """
    Represents a single behavioral event log.
    
    Attributes:
        user_id: ID of the user who performed the action.
        date: Date of the event.
        event_type: Type of event (e.g., 'habit_complete', 'habit_skip').
        adherence_flag: 1 if adherence behavior, 0 otherwise.
    """
    user_id: str
    date: datetime
    event_type: str
    adherence_flag: int

@dataclass
class WeeklyAggregation:
    """
    Aggregated weekly data for a user.
    
    Attributes:
        user_id: ID of the user.
        week_number: Sequential week number (1-based).
        adherence_flag: Binary flag (1 if majority adherence, else 0).
    """
    user_id: str
    week_number: int
    adherence_flag: int