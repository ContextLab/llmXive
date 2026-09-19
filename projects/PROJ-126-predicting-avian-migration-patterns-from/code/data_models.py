"""
Data Models and Entities for Avian Migration Pipeline.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class Status(Enum):
    """Status of a grid cell observation."""
    DETERMINED = "determined"
    UNDETERMINED = "undetermined"
    INSUFFICIENT_DATA = "insufficient_data"

@dataclass
class GridCellObservation:
    """
    Represents an observation within a grid cell.
    """
    grid_id: str
    week: int
    date: date
    count: int
    status: Status = Status.INSUFFICIENT_DATA

@dataclass
class EnvironmentalPredictor:
    """
    Represents environmental predictor values for a grid cell and time.
    """
    grid_id: str
    week: int
    temperature: Optional[float] = None
    ndvi: Optional[float] = None
    date: Optional[date] = None
