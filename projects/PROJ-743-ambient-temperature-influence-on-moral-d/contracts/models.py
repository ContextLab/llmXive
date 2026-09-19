"""
Pydantic models for the Ambient Temperature Influence on Moral Decision Speed project.

This module defines the structural schema for the merged dataset, combining
raw Moral Machine responses with ERA5 temperature data and derived features.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class DilemmaChoice(str, Enum):
    """Enum for the derived dilemma choice variable."""
    SAVE_MANY = "save_many"
    SAVE_FEW = "save_few"
    NO_DECISION = "no_decision"


class TimeOfDayCategory(str, Enum):
    """Enum for the derived time-of-day categories."""
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


class MoralResponseRaw(BaseModel):
    """
    Raw schema for Moral Machine response data.
    Corresponds to T009b (Raw Models).
    """
    participant_id: str
    latitude: float
    longitude: float
    timestamp: datetime
    response_time: float  # in milliseconds
    country: str
    dilemma_id: str


class TemperatureRecordRaw(BaseModel):
    """
    Raw schema for ERA5 temperature record data.
    Corresponds to T009b (Raw Models).
    """
    grid_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    temperature_celsius: float


class MergedDataset(BaseModel):
    """
    Pydantic model for the merged dataset combining Moral Machine and ERA5 data.

    This model includes fields from both raw models plus derived columns.
    Note: This is a structural schema definition only. Runtime validation logic
    for derived fields (e.g., ensuring dilemma_choice is computed correctly from
    underlying dilemma parameters) is not included here as the source data for
    those derivations may not exist yet in Phase 1.

    Fields:
      - participant_id: Unique identifier for the participant.
      - latitude: Latitude of the participant's location (from Moral Machine).
      - longitude: Longitude of the participant's location (from Moral Machine).
      - timestamp: Timestamp of the response (from Moral Machine).
      - response_time: Response time in milliseconds (from Moral Machine).
      - country: Country of the participant (from Moral Machine).
      - dilemma_id: ID of the dilemma presented (from Moral Machine).
      - grid_id: ID of the ERA5 grid cell matched to the participant.
      - temperature_celsius: Ambient temperature at the matched grid cell.
      - dilemma_choice: Derived categorical variable (e.g., "save_many" vs "save_few").
      - dilemma_complexity: Derived static complexity score.
      - time_of_day: Derived time-of-day category.
      - match_quality: Quality of the geospatial match (e.g., 'high', 'low').
      - age: (Optional) Demographic covariate from World Bank or other source.
      - gender: (Optional) Demographic covariate from World Bank or other source.
      - urban_rural: (Optional) Urban or rural proxy classification.
    """
    participant_id: str
    latitude: float
    longitude: float
    timestamp: datetime
    response_time: float
    country: str
    dilemma_id: str

    # ERA5 Data
    grid_id: str
    temperature_celsius: float

    # Derived Columns
    dilemma_choice: Optional[DilemmaChoice] = None
    dilemma_complexity: Optional[float] = None
    time_of_day: Optional[TimeOfDayCategory] = None
    match_quality: Optional[Literal['high', 'low']] = None

    # Optional Covariates (may be null if fetch failed)
    age: Optional[float] = None
    gender: Optional[float] = None
    urban_rural: Optional[Literal['urban', 'rural']] = None

    @field_validator('response_time')
    @classmethod
    def validate_response_time(cls, v):
        if v < 0:
            raise ValueError('response_time must be non-negative')
        return v

    @field_validator('temperature_celsius')
    @classmethod
    def validate_temperature(cls, v):
        # Physical bounds check (approximate)
        if v < -100 or v > 100:
            raise ValueError('temperature_celsius out of physical range')
        return v