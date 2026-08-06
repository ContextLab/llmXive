from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from datetime import date
import json
import logging

logger = logging.getLogger(__name__)

class SleepMetric(BaseModel):
    """
    Represents sleep quality metrics associated with a microbiome sample.
    Derived from the verified schema in T012b.
    """
    sample_id: str = Field(..., description="Unique identifier for the sample")
    sleep_efficiency: float = Field(..., ge=0.0, le=100.0, description="Percentage of time in bed spent asleep")
    sleep_duration_hours: float = Field(..., gt=0.0, description="Total hours of sleep")
    sleep_latency_minutes: Optional[float] = Field(None, ge=0.0, description="Time taken to fall asleep")
    wakings_count: Optional[int] = Field(None, ge=0, description="Number of awakenings during sleep period")
    date_recorded: Optional[date] = Field(None, description="Date the sleep data was recorded")

    @field_validator('sleep_efficiency')
    @classmethod
    def validate_efficiency(cls, v):
        if v is not None and (v < 0.0 or v > 100.0):
            raise ValueError('sleep_efficiency must be between 0 and 100')
        return v

    @field_validator('sleep_duration_hours')
    @classmethod
    def validate_duration(cls, v):
        if v is not None and v <= 0.0:
            raise ValueError('sleep_duration_hours must be positive')
        return v

class MicrobiomeSample(BaseModel):
    """
    Represents a microbiome sample with OTU counts and metadata.
    Includes antibiotic use status as per exclusion criteria.
    """
    sample_id: str = Field(..., description="Unique identifier matching sleep data")
    antibiotic_use_last_3m: bool = Field(..., description="Whether antibiotic was used in last 3 months")
    otu_counts: Dict[str, int] = Field(default_factory=dict, description="OTU ID to count mapping")
    sequencing_depth: int = Field(..., gt=0, description="Total reads for the sample")
    collection_date: Optional[date] = Field(None, description="Date of sample collection")
    subject_age: Optional[int] = Field(None, ge=0, description="Age of subject in years")
    subject_sex: Optional[str] = Field(None, description="Sex of subject")

    @field_validator('otu_counts')
    @classmethod
    def validate_otu_counts(cls, v):
        for k, val in v.items():
            if not isinstance(k, str):
                raise ValueError(f"OTU ID keys must be strings, got {type(k)}")
            if not isinstance(val, int) or val < 0:
                raise ValueError(f"OTU counts must be non-negative integers, got {val}")
        return v

    @field_validator('sequencing_depth')
    @classmethod
    def validate_depth(cls, v):
        if v <= 0:
            raise ValueError('sequencing_depth must be positive')
        return v

class CorrelationResult(BaseModel):
    """
    Represents the result of a statistical correlation test between
    a diversity metric and a sleep metric.
    """
    diversity_metric: str = Field(..., description="Name of the alpha-diversity index (e.g., Shannon, Simpson)")
    sleep_variable: str = Field(..., description="Name of the sleep metric (e.g., sleep_efficiency)")
    correlation_coefficient: float = Field(..., description="Spearman rank correlation coefficient (r)")
    p_value: float = Field(..., ge=0.0, le=1.0, description="Raw p-value from the test")
    q_value: float = Field(..., ge=0.0, le=1.0, description="Benjamini-Hochberg adjusted p-value")
    sample_size: int = Field(..., gt=0, description="Number of paired observations")
    is_moderate: bool = Field(..., description="True if |r| > 0.3")
    is_meaningful: bool = Field(..., description="True if q < 0.05 AND |r| > 0.3")

    @field_validator('p_value', 'q_value')
    @classmethod
    def validate_probability(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError(f"Probability value {v} must be between 0 and 1")
        return v

def models_to_dict(model: Union[BaseModel, List[BaseModel]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Helper to serialize Pydantic models to dictionaries, handling date objects.
    """
    def serialize_value(val):
        if isinstance(val, date):
            return val.isoformat()
        return val

    if isinstance(model, list):
        return [
            {k: serialize_value(v) for k, v in m.model_dump().items()}
            for m in model
        ]
    return {k: serialize_value(v) for k, v in model.model_dump().items()}