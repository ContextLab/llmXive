"""
Pydantic models for the Gut Microbiome and Sleep Quality study.

These models define the schema for:
- MicrobiomeSample: Represents a single sample's microbial composition and metadata.
- SleepMetric: Represents the sleep quality metrics associated with a sample.
- CorrelationResult: Represents the statistical output of correlation analysis.
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
    Derived from the verified schema requirements (T012d).
    """
    sample_id: str = Field(..., description="Unique identifier for the sample")
    sleep_efficiency: float = Field(..., ge=0.0, le=1.0, description="Ratio of time asleep to time in bed")
    sleep_duration_hours: float = Field(..., gt=0.0, description="Total sleep duration in hours")
    sleep_latency_minutes: Optional[float] = Field(None, ge=0.0, description="Time to fall asleep")
    wake_after_sleep_onset_minutes: Optional[float] = Field(None, ge=0.0, description="Minutes awake after initially falling asleep")
    num_awakenings: Optional[int] = Field(None, ge=0, description="Number of times awakened during the night")
    sleep_quality_rating: Optional[int] = Field(None, ge=1, le=5, description="Subjective sleep quality rating 1-5")

    @field_validator('sleep_efficiency')
    @classmethod
    def validate_efficiency(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('sleep_efficiency must be between 0.0 and 1.0')
        return v


class MicrobiomeSample(BaseModel):
    """
    Model representing a microbiome sample with associated metadata.
    Includes antibiotic use status as a key filter criterion.
    """
    sample_id: str = Field(..., description="Unique identifier matching SleepMetric")
    antibiotic_use_last_3m: bool = Field(..., description="Whether antibiotics were used in the last 3 months")
    sequencing_depth: int = Field(..., gt=0, description="Total number of reads/OTUs for the sample")
    # OTU/ASV counts would typically be stored in a separate table or as a dict/list
    # For schema definition purposes, we define the structure if embedded, 
    # but typically this model links to the OTU table in the pipeline.
    otu_counts: Optional[Dict[str, int]] = Field(None, description="Mapping of OTU ID to count")
    alpha_diversity_shannon: Optional[float] = Field(None, ge=0.0, description="Shannon diversity index")
    alpha_diversity_simpson: Optional[float] = Field(None, ge=0.0, description="Simpson diversity index")
    alpha_diversity_observed_otus: Optional[int] = Field(None, ge=0, description="Number of observed OTUs")

    @field_validator('otu_counts')
    @classmethod
    def validate_otu_counts(cls, v):
        if v is not None:
            if not all(isinstance(k, str) and isinstance(val, int) for k, val in v.items()):
                raise ValueError('otu_counts must be a dictionary mapping strings to integers')
        return v


class CorrelationResult(BaseModel):
    """
    Model representing the result of a correlation test between a diversity metric and a sleep metric.
    """
    diversity_metric: str = Field(..., description="Name of the diversity metric (e.g., 'shannon', 'simpson')")
    sleep_metric: str = Field(..., description="Name of the sleep metric (e.g., 'sleep_efficiency', 'sleep_duration_hours')")
    spearman_r: float = Field(..., description="Spearman rank correlation coefficient")
    p_value: float = Field(..., ge=0.0, le=1.0, description="Raw p-value from the correlation test")
    q_value: float = Field(..., ge=0.0, le=1.0, description="Benjamini-Hochberg adjusted p-value (FDR)")
    is_moderate: bool = Field(..., description="True if |r| > 0.3")
    is_meaningful: bool = Field(..., description="True if q-value < 0.05 AND |r| > 0.3")
    sample_size: int = Field(..., gt=0, description="Number of samples used in the calculation")

    @field_validator('spearman_r')
    @classmethod
    def validate_r(cls, v):
        if v < -1.0 or v > 1.0:
            raise ValueError('spearman_r must be between -1.0 and 1.0')
        return v

    @field_validator('p_value', 'q_value')
    @classmethod
    def validate_p_q(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('p-value and q-value must be between 0.0 and 1.0')
        return v


def models_to_dict(model_instance: Any) -> Dict[str, Any]:
    """
    Utility function to convert Pydantic model instances to dictionaries.
    Handles nested models and ensures JSON serializability.
    """
    if hasattr(model_instance, 'model_dump'):
        return model_instance.model_dump()
    elif hasattr(model_instance, 'dict'):
        # Fallback for older pydantic versions
        return model_instance.dict()
    else:
        logger.warning(f"Object {type(model_instance)} does not have model_dump or dict method")
        return {}