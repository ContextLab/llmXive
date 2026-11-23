"""
Pydantic models for the Ambient Temperature Influence on Moral Decision Speed project.

This module defines structural schemas for:
1. Raw data entities (MoralResponse, TemperatureRecord) - defined in T009b
2. Merged dataset entity (MergedDataset) - defined in T009d
"""
from datetime import datetime
from typing import Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re

# --------------------------------------------------------------------------
# Raw Data Models (Reference from T009b)
# --------------------------------------------------------------------------

class MoralResponse(BaseModel):
    """Schema for raw Moral Machine dataset records."""
    participant_id: str = Field(..., description="Unique identifier for the participant")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude of the participant")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude of the participant")
    timestamp: datetime = Field(..., description="Timestamp of the response")
    response_time: float = Field(..., description="Response time in milliseconds")
    country: str = Field(..., description="Country of the participant")
    dilemma_id: str = Field(..., description="Unique identifier for the dilemma")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "participant_id": "P001",
                "latitude": 51.5074,
                "longitude": -0.1278,
                "timestamp": "2016-01-01T12:00:00Z",
                "response_time": 2500.0,
                "country": "United Kingdom",
                "dilemma_id": "D001"
            }
        }
    )

class TemperatureRecord(BaseModel):
    """Schema for raw ERA5 temperature dataset records."""
    grid_id: str = Field(..., description="Unique identifier for the ERA5 grid cell")
    timestamp: datetime = Field(..., description="Timestamp of the temperature record")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude of the grid center")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude of the grid center")
    temperature_celsius: float = Field(..., description="Temperature in Celsius")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "grid_id": "GRID_51.5_-0.1",
                "timestamp": "2016-01-01T12:00:00Z",
                "latitude": 51.5,
                "longitude": -0.1,
                "temperature_celsius": 8.5
            }
        }
    )

# --------------------------------------------------------------------------
# Merged Dataset Model (Target Schema for T009d)
# --------------------------------------------------------------------------

class MergedDataset(BaseModel):
    """
    Structural schema for the final merged dataset.
    
    This model combines fields from MoralResponse and TemperatureRecord,
    plus derived columns generated during the ingestion and matching process.
    
    Note: This is a structural definition. Runtime validation logic for derived
    fields that do not exist in the raw input (e.g., dilemma_choice) is not
    included here, as per Phase 1 constraints.
    """
    # Primary Keys / Identifiers
    participant_id: str = Field(..., description="Unique identifier for the participant")
    dilemma_id: str = Field(..., description="Unique identifier for the dilemma")
    grid_id: str = Field(..., description="ERA5 grid cell identifier")
    
    # Raw Location & Time
    latitude: float = Field(..., ge=-90, le=90, description="Latitude of the participant")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude of the participant")
    timestamp: datetime = Field(..., description="Timestamp of the response")
    
    # Raw Measurements
    response_time: float = Field(..., description="Response time in milliseconds")
    temperature_celsius: float = Field(..., description="Temperature in Celsius at the time of response")
    
    # Derived / Contextual Fields
    country: str = Field(..., description="Country of the participant")
    cultural_region: str = Field(..., description="Derived cultural region based on country")
    
    # Derived Moral Dilemma Attributes
    dilemma_choice: str = Field(..., description="Categorical choice made by participant (e.g., 'save_many', 'save_few')")
    dilemma_complexity: float = Field(..., ge=0.0, description="Static complexity score of the dilemma")
    
    # Derived Temporal Attributes
    time_of_day: str = Field(..., description="Categorized time of day (e.g., 'morning', 'afternoon', 'evening', 'night')")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "description": "Final merged dataset combining Moral Machine responses with ERA5 temperature data and derived features."
        }
    )

    @field_validator('time_of_day')
    @classmethod
    def validate_time_of_day(cls, v: str) -> str:
        allowed = {'morning', 'afternoon', 'evening', 'night'}
        if v.lower() not in allowed:
            raise ValueError(f"time_of_day must be one of {allowed}, got {v}")
        return v.lower()

    @field_validator('dilemma_choice')
    @classmethod
    def validate_dilemma_choice(cls, v: str) -> str:
        # Basic validation for expected categories; logic may vary based on derivation
        if not v:
            raise ValueError("dilemma_choice cannot be empty")
        return v