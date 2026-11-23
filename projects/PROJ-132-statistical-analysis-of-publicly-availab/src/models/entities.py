"""
Base data entities for the bird migration and climate analysis pipeline.

This module defines the core data structures (entities) used throughout the
project to represent migration records, phenology metrics, and climate variables.
These classes provide type safety, validation, and serialization capabilities.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json


class MigrationStatus(Enum):
    """Enumeration of possible migration statuses."""
    MIGRATING = "migrating"
    BREEDING = "breeding"
    WINTERING = "wintering"
    STOPOVER = "stopover"
    UNKNOWN = "unknown"


@dataclass
class MigrationRecord:
    """
    Represents a single migration observation record.

    Attributes:
        species: Scientific name of the bird species.
        checklist_id: Unique identifier for the eBird checklist.
        date: Date of the observation.
        latitude: Latitude of the observation point.
        longitude: Longitude of the observation point.
        count: Number of individuals observed.
        effort_distance_km: Distance covered during the checklist (km).
        effort_duration_minutes: Duration of the checklist (minutes).
        is_complete: Whether the checklist was completed (all species reported).
        grid_cell: Aggregated grid cell identifier (e.g., "0.5x0.5_lat_lon").
        week_number: ISO week number of the year.
        year: Year of the observation.
        status: Migration status classification.
        metadata: Additional metadata as a dictionary.
    """
    species: str
    checklist_id: str
    date: datetime
    latitude: float
    longitude: float
    count: int
    effort_distance_km: Optional[float] = None
    effort_duration_minutes: Optional[float] = None
    is_complete: bool = True
    grid_cell: Optional[str] = None
    week_number: Optional[int] = None
    year: Optional[int] = None
    status: MigrationStatus = MigrationStatus.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary for serialization."""
        return {
            "species": self.species,
            "checklist_id": self.checklist_id,
            "date": self.date.isoformat() if self.date else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "count": self.count,
            "effort_distance_km": self.effort_distance_km,
            "effort_duration_minutes": self.effort_duration_minutes,
            "is_complete": self.is_complete,
            "grid_cell": self.grid_cell,
            "week_number": self.week_number,
            "year": self.year,
            "status": self.status.value if self.status else None,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MigrationRecord":
        """Create a MigrationRecord from a dictionary."""
        date_str = data.get("date")
        date_obj = datetime.fromisoformat(date_str) if date_str else None
        status_str = data.get("status")
        status = MigrationStatus(status_str) if status_str else MigrationStatus.UNKNOWN

        return cls(
            species=data["species"],
            checklist_id=data["checklist_id"],
            date=date_obj,
            latitude=data["latitude"],
            longitude=data["longitude"],
            count=data["count"],
            effort_distance_km=data.get("effort_distance_km"),
            effort_duration_minutes=data.get("effort_duration_minutes"),
            is_complete=data.get("is_complete", True),
            grid_cell=data.get("grid_cell"),
            week_number=data.get("week_number"),
            year=data.get("year"),
            status=status,
            metadata=data.get("metadata", {})
        )

    def __post_init__(self):
        """Validate the record after initialization."""
        if not self.species:
            raise ValueError("species cannot be empty")
        if not self.checklist_id:
            raise ValueError("checklist_id cannot be empty")
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"latitude must be between -90 and 90, got {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"longitude must be between -180 and 180, got {self.longitude}")
        if self.count < 0:
            raise ValueError(f"count cannot be negative, got {self.count}")


@dataclass
class PhenologyMetric:
    """
    Represents a phenology metric computed for a species in a specific location and year.

    Attributes:
        species: Scientific name of the bird species.
        year: Year of the observation period.
        grid_cell: Aggregated grid cell identifier.
        metric_type: Type of phenology metric (e.g., 'first_arrival', 'median_arrival').
        value: The computed metric value (e.g., day of year).
        confidence_lower: Lower bound of the confidence interval.
        confidence_upper: Upper bound of the confidence interval.
        sample_size: Number of observations used to compute the metric.
        data_quality: Quality flag for the metric (e.g., 'sufficient', 'insufficient').
        metadata: Additional metadata as a dictionary.
    """
    species: str
    year: int
    grid_cell: str
    metric_type: str
    value: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    sample_size: int = 0
    data_quality: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary for serialization."""
        return {
            "species": self.species,
            "year": self.year,
            "grid_cell": self.grid_cell,
            "metric_type": self.metric_type,
            "value": self.value,
            "confidence_lower": self.confidence_lower,
            "confidence_upper": self.confidence_upper,
            "sample_size": self.sample_size,
            "data_quality": self.data_quality,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhenologyMetric":
        """Create a PhenologyMetric from a dictionary."""
        return cls(
            species=data["species"],
            year=data["year"],
            grid_cell=data["grid_cell"],
            metric_type=data["metric_type"],
            value=data["value"],
            confidence_lower=data.get("confidence_lower"),
            confidence_upper=data.get("confidence_upper"),
            sample_size=data.get("sample_size", 0),
            data_quality=data.get("data_quality", "unknown"),
            metadata=data.get("metadata", {})
        )

    def __post_init__(self):
        """Validate the metric after initialization."""
        if not self.species:
            raise ValueError("species cannot be empty")
        if not self.grid_cell:
            raise ValueError("grid_cell cannot be empty")
        if not self.metric_type:
            raise ValueError("metric_type cannot be empty")
        if self.sample_size < 0:
            raise ValueError(f"sample_size cannot be negative, got {self.sample_size}")
        if self.confidence_lower is not None and self.confidence_upper is not None:
            if self.confidence_lower > self.confidence_upper:
                raise ValueError(
                    f"confidence_lower ({self.confidence_lower}) "
                    f"must be <= confidence_upper ({self.confidence_upper})"
                )


@dataclass
class ClimateVariable:
    """
    Represents a climate variable measurement for a specific location and time.

    Attributes:
        grid_cell: Aggregated grid cell identifier.
        year: Year of the measurement.
        week_number: Week number of the year.
        variable_type: Type of climate variable (e.g., 'temperature', 'precipitation').
        value: The measured value.
        unit: Unit of measurement (e.g., 'C', 'mm').
        source: Data source identifier (e.g., 'NOAA', 'ERA5').
        is_imputed: Whether the value was imputed (True) or observed (False).
        metadata: Additional metadata as a dictionary.
    """
    grid_cell: str
    year: int
    week_number: int
    variable_type: str
    value: float
    unit: str
    source: str = "unknown"
    is_imputed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the variable to a dictionary for serialization."""
        return {
            "grid_cell": self.grid_cell,
            "year": self.year,
            "week_number": self.week_number,
            "variable_type": self.variable_type,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "is_imputed": self.is_imputed,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClimateVariable":
        """Create a ClimateVariable from a dictionary."""
        return cls(
            grid_cell=data["grid_cell"],
            year=data["year"],
            week_number=data["week_number"],
            variable_type=data["variable_type"],
            value=data["value"],
            unit=data["unit"],
            source=data.get("source", "unknown"),
            is_imputed=data.get("is_imputed", False),
            metadata=data.get("metadata", {})
        )

    def __post_init__(self):
        """Validate the variable after initialization."""
        if not self.grid_cell:
            raise ValueError("grid_cell cannot be empty")
        if not self.variable_type:
            raise ValueError("variable_type cannot be empty")
        if not self.unit:
            raise ValueError("unit cannot be empty")
        if not (1 <= self.week_number <= 52):
            raise ValueError(f"week_number must be between 1 and 52, got {self.week_number}")
