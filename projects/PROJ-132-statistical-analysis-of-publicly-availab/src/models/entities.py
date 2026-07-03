"""
Base data entities for the bird migration statistical analysis pipeline.

This module defines the core data structures used to represent migration records,
phenology metrics, and climate variables throughout the analysis pipeline.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import date
import math


@dataclass
class MigrationRecord:
    """
    Represents a single bird observation record from eBird or similar sources.

    Attributes:
        species: Scientific name of the species (e.g., 'Turdus migratorius')
        checklist_id: Unique identifier for the observation checklist
        date: Date of observation
        latitude: Latitude in decimal degrees (WGS84)
        longitude: Longitude in decimal degrees (WGS84)
        count: Number of individuals observed (must be >= 0)
        effort_distance_km: Distance covered during the checklist (km)
        effort_duration_min: Duration of the checklist (minutes)
        is_complete: Whether the checklist was marked as complete by the observer
        species_code: CLO species code if available
    """
    species: str
    checklist_id: str
    date: date
    latitude: float
    longitude: float
    count: int
    effort_distance_km: Optional[float] = None
    effort_duration_min: Optional[float] = None
    is_complete: bool = True
    species_code: Optional[str] = None

    def __post_init__(self):
        """Validate record constraints."""
        if self.latitude < -90 or self.latitude > 90:
            raise ValueError(f"Latitude {self.latitude} out of range [-90, 90]")
        if self.longitude < -180 or self.longitude > 180:
            raise ValueError(f"Longitude {self.longitude} out of range [-180, 180]")
        if self.count < 0:
            raise ValueError(f"Count {self.count} cannot be negative")

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary representation."""
        return {
            'species': self.species,
            'checklist_id': self.checklist_id,
            'date': self.date.isoformat(),
            'latitude': self.latitude,
            'longitude': self.longitude,
            'count': self.count,
            'effort_distance_km': self.effort_distance_km,
            'effort_duration_min': self.effort_duration_min,
            'is_complete': self.is_complete,
            'species_code': self.species_code
        }


@dataclass
class PhenologyMetric:
    """
    Represents a computed phenology metric for a species in a specific grid cell.

    Attributes:
        species: Scientific name of the species
        grid_cell_id: Unique identifier for the grid cell (e.g., "45.5_-122.5")
        year: Calendar year of the observation period
        week_number: ISO week number (1-53)
        metric_type: Type of metric ('first_arrival', 'median_arrival', 'stopover_duration')
        value: The computed metric value (date for arrival, days for duration)
        sample_size: Number of observations used to compute the metric
        confidence_lower: Lower bound of confidence interval (if applicable)
        confidence_upper: Upper bound of confidence interval (if applicable)
        is_imputed: Whether this value was derived via interpolation
        data_quality_flag: Quality flag ('good', 'moderate', 'insufficient')
    """
    species: str
    grid_cell_id: str
    year: int
    week_number: int
    metric_type: str
    value: float  # days since start of year or day-of-year
    sample_size: int
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    is_imputed: bool = False
    data_quality_flag: str = 'good'

    def __post_init__(self):
        """Validate metric constraints."""
        valid_types = ['first_arrival', 'median_arrival', 'stopover_duration']
        if self.metric_type not in valid_types:
            raise ValueError(f"metric_type must be one of {valid_types}")
        if self.sample_size < 1:
            raise ValueError(f"sample_size must be >= 1, got {self.sample_size}")
        if self.data_quality_flag not in ['good', 'moderate', 'insufficient']:
            raise ValueError(f"Invalid data_quality_flag: {self.data_quality_flag}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary representation."""
        return {
            'species': self.species,
            'grid_cell_id': self.grid_cell_id,
            'year': self.year,
            'week_number': self.week_number,
            'metric_type': self.metric_type,
            'value': self.value,
            'sample_size': self.sample_size,
            'confidence_lower': self.confidence_lower,
            'confidence_upper': self.confidence_upper,
            'is_imputed': self.is_imputed,
            'data_quality_flag': self.data_quality_flag
        }


@dataclass
class ClimateVariable:
    """
    Represents a climate variable measurement for a specific location and time.

    Attributes:
        grid_cell_id: Unique identifier for the grid cell
        year: Calendar year
        week_number: ISO week number
        variable_type: Type of variable ('temperature', 'precipitation', 'humidity')
        value: Measured or imputed value
        unit: Unit of measurement (e.g., 'Celsius', 'mm', '%')
        source: Data source ('NOAA', 'PRISM', 'imputed')
        is_imputed: Whether this value was derived via interpolation
        imputation_method: Method used for imputation if applicable
        quality_flag: Quality assessment ('verified', 'estimated', 'low_confidence')
    """
    grid_cell_id: str
    year: int
    week_number: int
    variable_type: str
    value: float
    unit: str
    source: str
    is_imputed: bool = False
    imputation_method: Optional[str] = None
    quality_flag: str = 'verified'

    def __post_init__(self):
        """Validate variable constraints."""
        valid_types = ['temperature', 'precipitation', 'humidity']
        if self.variable_type not in valid_types:
            raise ValueError(f"variable_type must be one of {valid_types}")
        if self.source not in ['NOAA', 'PRISM', 'imputed']:
            raise ValueError(f"Invalid source: {self.source}")
        if self.quality_flag not in ['verified', 'estimated', 'low_confidence']:
            raise ValueError(f"Invalid quality_flag: {self.quality_flag}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert variable to dictionary representation."""
        return {
            'grid_cell_id': self.grid_cell_id,
            'year': self.year,
            'week_number': self.week_number,
            'variable_type': self.variable_type,
            'value': self.value,
            'unit': self.unit,
            'source': self.source,
            'is_imputed': self.is_imputed,
            'imputation_method': self.imputation_method,
            'quality_flag': self.quality_flag
        }

    @staticmethod
    def aggregate_mean(
        variables: List['ClimateVariable'],
        variable_type: str,
        tolerance_weeks: int = 1
    ) -> Optional['ClimateVariable']:
        """
        Aggregate multiple climate variables by taking the mean value.

        Args:
            variables: List of ClimateVariable objects to aggregate
            variable_type: The type of variable to aggregate
            tolerance_weeks: Number of weeks to consider as the same period

        Returns:
            A new ClimateVariable with the mean value, or None if no valid data
        """
        valid_vars = [
            v for v in variables
            if v.variable_type == variable_type and v.quality_flag != 'low_confidence'
        ]

        if not valid_vars:
            return None

        values = [v.value for v in valid_vars]
        mean_value = sum(values) / len(values)

        # Use the most reliable source
        source_priority = {'NOAA': 3, 'PRISM': 2, 'imputed': 1}
        sorted_vars = sorted(
            valid_vars,
            key=lambda v: source_priority.get(v.source, 0),
            reverse=True
        )
        best_source = sorted_vars[0].source

        return ClimateVariable(
            grid_cell_id=valid_vars[0].grid_cell_id,
            year=valid_vars[0].year,
            week_number=valid_vars[0].week_number,
            variable_type=variable_type,
            value=mean_value,
            unit=valid_vars[0].unit,
            source=best_source,
            is_imputed=all(v.is_imputed for v in valid_vars),
            imputation_method='mean_aggregation' if any(v.is_imputed for v in valid_vars) else None,
            quality_flag='estimated' if any(v.quality_flag == 'estimated' for v in valid_vars) else 'verified'
        )