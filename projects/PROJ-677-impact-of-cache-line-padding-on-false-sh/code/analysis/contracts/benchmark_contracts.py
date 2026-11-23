from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime
import json
import math

class BenchmarkRun(BaseModel):
    """
    Contract for a single benchmark run result row.
    Matches the CSV output schema: thread_count, configuration, iteration_count, wall_clock_time_ms
    """
    thread_count: int = Field(..., gt=0, description="Number of threads used")
    configuration: Literal["packed", "padded"] = Field(..., description="Counter configuration type")
    iteration_count: int = Field(..., gt=0, description="Number of atomic increments per thread")
    wall_clock_time_ms: float = Field(..., ge=0, description="Total wall clock time in milliseconds")

    @field_validator('configuration')
    @classmethod
    def validate_config(cls, v):
        if v not in ["packed", "padded"]:
            raise ValueError(f"configuration must be 'packed' or 'padded', got {v}")
        return v

class AggregatedResult(BaseModel):
    """
    Contract for aggregated results per thread count and configuration.
    """
    thread_count: int
    configuration: str
    mean_throughput: float
    std_dev: float

class StatisticalComparison(BaseModel):
    """
    Contract for statistical comparison results.
    """
    thread_count: int
    config: str
    t_stat: float
    p_value: float
    cohens_d: float
    fdr_adjusted_p: float
    is_significant: bool

def get_all_schemas():
    return [BenchmarkRun, AggregatedResult, StatisticalComparison]