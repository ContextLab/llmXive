"""
Data models specific to the PROJ-540 research project.

Defines domain-specific entities for social media engagement and anxiety metrics.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class DoomscrollingSession:
    """Represents a single session of doomscrolling behavior."""
    user_id: str
    session_start: datetime
    session_duration_minutes: float
    scroll_depth_avg: float  # 0.0 to 1.0
    content_types_consumed: list[str]
    anxiety_pre_session: Optional[float] = None
    anxiety_post_session: Optional[float] = None

@dataclass
class AnxietySurveyResponse:
    """Structured response from an anxiety survey participant."""
    participant_id: str
    survey_date: datetime
    baseline_anxiety: float
    current_anxiety: float
    news_exposure_freq: int  # Times per day
    social_media_engagement: float  # Composite score
    age: int
    gender: Optional[str] = None

@dataclass
class AnalysisResult:
    """Container for statistical analysis results."""
    model_id: str
    correlation_coefficient: float
    p_value: float
    regression_coefficients: dict
    assumption_checks: dict
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
