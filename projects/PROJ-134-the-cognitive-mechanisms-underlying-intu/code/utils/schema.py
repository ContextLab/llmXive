from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import numpy as np

class SalienceLevel(str, Enum):
    """Enumeration for salience levels in VR scenes."""
    LOW = "low"
    HIGH = "high"

class MFQResponse(BaseModel):
    """Single response to a Moral Foundations Questionnaire item."""
    item_id: str
    score: float

    @field_validator('score')
    @classmethod
    def validate_score(cls, v):
        if not 1 <= v <= 7:
            raise ValueError("MFQ score must be between 1 and 7")
        return v

class MFQDataset(BaseModel):
    """Container for a participant's MFQ responses."""
    participant_id: int
    responses: List[MFQResponse]
    timestamp: Optional[datetime] = None

class MoralStory(BaseModel):
    """A single moral story with salience mapping."""
    story_id: int
    text: str
    salience_level: SalienceLevel
    # Optional: mapping to VR scene parameters
    vr_scene_id: Optional[str] = None

class MoralStoriesDataset(BaseModel):
    """Container for multiple moral stories."""
    stories: List[MoralStory]
    total_count: int

class VRInteractionLog(BaseModel):
    """Log entry for a single VR interaction."""
    participant_id: int
    story_id: int
    response_time: float  # in seconds
    gaze_duration: float  # in seconds
    judgment: float  # 1-7 Likert scale
    timestamp: Optional[datetime] = None

    @field_validator('judgment')
    @classmethod
    def validate_judgment(cls, v):
        if not 1 <= v <= 7:
            raise ValueError("Judgment score must be between 1 and 7")
        return v

class VRLogsDataset(BaseModel):
    """Container for VR interaction logs."""
    logs: List[VRInteractionLog]
    total_count: int

class MergedDataset(BaseModel):
    """
    Merged dataset containing MFQ, Story, and VR Log data.
    This is the primary schema for the ingestion pipeline output.
    """
    participant_id: int
    story_id: int
    # MFQ fields (aggregated per participant)
    mfq_care: Optional[float] = None
    mfq_fairness: Optional[float] = None
    mfq_loyalty: Optional[float] = None
    mfq_authority: Optional[float] = None
    mfq_purity: Optional[float] = None
    # Story fields
    story_text: str
    salience_level: SalienceLevel
    # VR fields
    response_time: float
    gaze_duration: float
    judgment: float

def validate_mfq_data(data: Dict[str, Any]) -> bool:
    """Validate MFQ data structure."""
    try:
        MFQDataset(**data)
        return True
    except Exception:
        return False

def validate_stories_data(data: Dict[str, Any]) -> bool:
    """Validate Moral Stories data structure."""
    try:
        MoralStoriesDataset(**data)
        return True
    except Exception:
        return False

def validate_vr_logs_data(data: Dict[str, Any]) -> bool:
    """Validate VR logs data structure."""
    try:
        VRLogsDataset(**data)
        return True
    except Exception:
        return False

def validate_merged_data(data: Dict[str, Any]) -> bool:
    """Validate merged dataset structure."""
    try:
        MergedDataset(**data)
        return True
    except Exception:
        return False