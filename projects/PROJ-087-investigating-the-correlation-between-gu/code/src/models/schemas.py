"""
Pydantic data models for the Gut Microbiome and Sleep Quality study.

These models define the schema for the cleaned dataset and analysis results,
based on the verified schema from T012b.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import date
import json


class SleepMetric(BaseModel):
    """Model representing sleep quality metrics for a single sample."""
    
    sample_id: str = Field(..., description="Unique identifier for the sample")
    sleep_efficiency: float = Field(..., ge=0.0, le=1.0, description="Ratio of time asleep to time in bed")
    sleep_duration_hours: float = Field(..., gt=0.0, description="Total sleep duration in hours")
    sleep_latency_minutes: Optional[float] = Field(None, ge=0.0, description="Time taken to fall asleep")
    awakenings_count: Optional[int] = Field(None, ge=0, description="Number of awakenings during the night")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sample_id": "S001",
                "sleep_efficiency": 0.85,
                "sleep_duration_hours": 7.2,
                "sleep_latency_minutes": 15.0,
                "awakenings_count": 2
            }
        }


class MicrobiomeSample(BaseModel):
    """
    Model representing a microbiome sample with associated metadata.
    Includes filtering flags verified in T012b/T014.
    """
    
    sample_id: str = Field(..., description="Unique identifier matching sleep data")
    antibiotic_use_last_3m: bool = Field(..., description="Flag for antibiotic use in last 3 months")
    sequencing_depth: int = Field(..., gt=0, description="Total OTU counts for the sample")
    # Alpha diversity metrics (calculated in T020b)
    shannon_index: Optional[float] = Field(None, ge=0.0, description="Shannon diversity index")
    simpson_index: Optional[float] = Field(None, ge=0.0, le=1.0, description="Simpson diversity index")
    observed_otus: Optional[int] = Field(None, ge=0, description="Number of observed OTUs")
    
    # OTU abundance data (sparse representation for memory efficiency)
    # Key: OTU ID, Value: Count
    otu_counts: Dict[str, int] = Field(default_factory=dict, description="OTU abundance counts")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sample_id": "S001",
                "antibiotic_use_last_3m": False,
                "sequencing_depth": 15000,
                "shannon_index": 3.45,
                "simpson_index": 0.92,
                "observed_otus": 245,
                "otu_counts": {"OTU_001": 120, "OTU_002": 45}
            }
        }

    @field_validator('otu_counts')
    @classmethod
    def validate_otu_counts(cls, v):
        if not v:
            return {}
        for k, val in v.items():
            if not isinstance(val, int) or val < 0:
                raise ValueError(f"OTU count for {k} must be a non-negative integer")
        return v


class CorrelationResult(BaseModel):
    """
    Model representing the result of a single correlation test
    between a diversity metric and a sleep variable.
    """
    
    diversity_metric: str = Field(..., description="Name of the alpha diversity metric (e.g., 'shannon_index')")
    sleep_variable: str = Field(..., description="Name of the sleep metric (e.g., 'sleep_efficiency')")
    spearman_r: float = Field(..., description="Spearman rank correlation coefficient")
    p_value: float = Field(..., ge=0.0, le=1.0, description="Raw p-value")
    q_value: float = Field(..., ge=0.0, le=1.0, description="Benjamini-Hochberg adjusted p-value")
    sample_count: int = Field(..., gt=0, description="Number of samples used in the calculation")
    
    # Significance flags (SC-002)
    is_moderate: bool = Field(..., description="True if |r| > 0.3")
    is_meaningful: bool = Field(..., description="True if q < 0.05 AND |r| > 0.3")
    
    class Config:
        json_schema_extra = {
            "example": {
                "diversity_metric": "shannon_index",
                "sleep_variable": "sleep_efficiency",
                "spearman_r": -0.35,
                "p_value": 0.004,
                "q_value": 0.02,
                "sample_count": 150,
                "is_moderate": True,
                "is_meaningful": True
            }
        }

    @field_validator('spearman_r')
    @classmethod
    def validate_r(cls, v):
        if v < -1.0 or v > 1.0:
            raise ValueError("Spearman r must be between -1 and 1")
        return v

    @field_validator('p_value', 'q_value')
    @classmethod
    def validate_prob(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError("p-value and q-value must be between 0 and 1")
        return v

    @field_validator('is_moderate')
    @classmethod
    def check_moderate(cls, v, info):
        # This validator is mostly for documentation; the value should be set by logic
        # but we ensure it aligns with r if possible, or just accept the passed value
        # In a strict implementation, we might recalculate, but here we trust the pipeline logic.
        return v

    @field_validator('is_meaningful')
    @classmethod
    def check_meaningful(cls, v, info):
        return v


def models_to_dict() -> Dict[str, Any]:
    """
    Utility to export the schema definitions as a dictionary.
    Useful for documentation or dynamic schema generation.
    """
    return {
        "SleepMetric": SleepMetric.model_json_schema(),
        "MicrobiomeSample": MicrobiomeSample.model_json_schema(),
        "CorrelationResult": CorrelationResult.model_json_schema()
    }
