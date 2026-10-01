"""
Pydantic models for data validation and schema definition.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

class MoralResponse(BaseModel):
    """Schema for raw moral response data."""
    participant_id: str
    latitude: float
    longitude: float
    timestamp: datetime
    response_time: float
    country: str
    dilemma_id: str

class TemperatureRecord(BaseModel):
    """Schema for raw temperature data."""
    grid_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    temperature_celsius: float

class MergedDataset(BaseModel):
    """Schema for the final merged dataset including derived fields."""
    # Raw fields
    participant_id: str
    latitude: float
    longitude: float
    timestamp: datetime
    response_time: float
    country: str
    dilemma_id: str
    
    # Temperature fields
    grid_id: str
    temperature_celsius: float
    
    # Derived fields
    dilemma_choice: str
    dilemma_complexity: float
    time_of_day: str
    cultural_region: Optional[str] = None
    
    # Metadata
    match_quality: Optional[str] = None