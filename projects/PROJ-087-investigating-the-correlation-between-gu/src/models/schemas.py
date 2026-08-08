"""
Pydantic models for the Gut Microbiome and Sleep Quality analysis pipeline.

These models define the schema for:
- MicrobiomeSample: Represents a single sample's microbiome composition and metadata.
- SleepMetric: Represents sleep quality metrics for a sample.
- CorrelationResult: Represents the result of a correlation analysis between diversity and sleep.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import date
import json
import logging

logger = logging.getLogger(__name__)


class SleepMetric(BaseModel):
    """
    Model representing sleep quality metrics.

    Attributes:
        sleep_efficiency: Percentage of time in bed spent asleep (0-100).
        sleep_duration_hours: Total sleep duration in hours.
        sleep_latency_minutes: Time taken to fall asleep in minutes.
        wake_after_sleep_onset: Minutes awake after initially falling asleep.
        sleep_quality_score: Self-reported sleep quality score (1-5).
    """
    sleep_efficiency: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Percentage of time in bed spent asleep"
    )
    sleep_duration_hours: Optional[float] = Field(
        None,
        gt=0.0,
        description="Total sleep duration in hours"
    )
    sleep_latency_minutes: Optional[float] = Field(
        None,
        ge=0.0,
        description="Time taken to fall asleep in minutes"
    )
    wake_after_sleep_onset: Optional[float] = Field(
        None,
        ge=0.0,
        description="Minutes awake after initially falling asleep"
    )
    sleep_quality_score: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Self-reported sleep quality score (1-5)"
    )

    @field_validator('sleep_efficiency', 'sleep_duration_hours', 'sleep_latency_minutes', 'wake_after_sleep_onset')
    @classmethod
    def validate_floats(cls, v, info):
        """Ensure float fields are valid numbers if provided."""
        if v is not None and not isinstance(v, (int, float)):
            try:
                return float(v)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid numeric value for {info.field_name}: {v}")
        return v


class MicrobiomeSample(BaseModel):
    """
    Model representing a single microbiome sample with metadata.

    Attributes:
        sample_id: Unique identifier for the sample.
        subject_id: Identifier for the subject from whom the sample was taken.
        collection_date: Date of sample collection.
        sequencing_depth: Total number of reads for the sample.
        antibiotic_use_last_3m: Whether the subject used antibiotics in the last 3 months.
        sleep_metrics: Embedded SleepMetric object.
        otu_counts: Dictionary mapping OTU IDs to read counts.
    """
    sample_id: str = Field(..., description="Unique sample identifier")
    subject_id: str = Field(..., description="Subject identifier")
    collection_date: Optional[date] = Field(None, description="Date of sample collection")
    sequencing_depth: Optional[int] = Field(None, ge=0, description="Total sequencing depth")
    antibiotic_use_last_3m: Optional[bool] = Field(None, description="Antibiotic use in last 3 months")
    sleep_metrics: Optional[SleepMetric] = Field(None, description="Associated sleep metrics")
    otu_counts: Dict[str, int] = Field(default_factory=dict, description="OTU count dictionary")

    @field_validator('collection_date')
    @classmethod
    def parse_date(cls, v):
        """Parse date from string if necessary."""
        if isinstance(v, str):
            try:
                return date.fromisoformat(v)
            except ValueError:
                raise ValueError(f"Invalid date format: {v}. Expected ISO format (YYYY-MM-DD).")
        return v


class CorrelationResult(BaseModel):
    """
    Model representing the result of a correlation analysis.

    Attributes:
        variable_x: Name of the first variable (e.g., Shannon Index).
        variable_y: Name of the second variable (e.g., Sleep Efficiency).
        r_value: Spearman correlation coefficient.
        p_value: Raw p-value from the correlation test.
        q_value: Adjusted p-value (FDR corrected).
        is_moderate: Boolean indicating if |r| > 0.3.
        is_meaningful: Boolean indicating if q < 0.05 AND |r| > 0.3.
        sample_size: Number of samples used in the correlation.
    """
    variable_x: str = Field(..., description="First variable name")
    variable_y: str = Field(..., description="Second variable name")
    r_value: float = Field(..., description="Spearman correlation coefficient")
    p_value: float = Field(..., description="Raw p-value")
    q_value: float = Field(..., description="FDR adjusted p-value")
    is_moderate: bool = Field(..., description="Is |r| > 0.3?")
    is_meaningful: bool = Field(..., description="Is q < 0.05 AND |r| > 0.3?")
    sample_size: int = Field(..., ge=2, description="Number of samples")

    @field_validator('r_value')
    @classmethod
    def validate_r_value(cls, v):
        """Ensure r_value is between -1 and 1."""
        if not -1.0 <= v <= 1.0:
            raise ValueError(f"r_value must be between -1 and 1, got {v}")
        return v

    @field_validator('p_value', 'q_value')
    @classmethod
    def validate_probability(cls, v):
        """Ensure p/q values are between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Probability value must be between 0 and 1, got {v}")
        return v


def models_to_dict(model: Union[BaseModel, List[BaseModel]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Convert a Pydantic model or list of models to a dictionary (or list of dicts).
    Handles nested models and excludes None values if desired (though default is to include).
    """
    if isinstance(model, list):
        return [m.model_dump() for m in model]
    return model.model_dump()