"""
Pydantic schemas for BenchmarkRun and AggregatedResult.

These schemas define the strict data contract for:
1. Raw benchmark runs (output from C++ benchmark)
2. Aggregated statistical results (output from analysis)
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class CounterConfiguration(str, Enum):
    """Enumeration of counter memory layouts."""
    PACKED = "packed"
    PADDED = "padded"


class BenchmarkRun(BaseModel):
    """
    Schema for a single raw benchmark run output.
    Matches CSV columns: thread_count, configuration, iteration_count, wall_clock_time_ms
    """
    model_config = ConfigDict(strict=True)

    thread_count: int = Field(..., ge=1, description="Number of threads used in the benchmark")
    configuration: CounterConfiguration = Field(..., description="Memory layout: packed or padded")
    iteration_count: int = Field(..., gt=0, description="Number of atomic increments per thread")
    wall_clock_time_ms: float = Field(..., gt=0, description="Total wall-clock time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Time of the run")

    @field_validator('configuration')
    @classmethod
    def validate_config(cls, v):
        if isinstance(v, str):
            return CounterConfiguration(v.lower())
        return v


class AggregatedResult(BaseModel):
    """
    Schema for aggregated statistical results per thread_count and configuration.
    Used for statistical comparison and plotting.
    """
    model_config = ConfigDict(strict=True)

    thread_count: int = Field(..., ge=1, description="Number of threads")
    configuration: CounterConfiguration = Field(..., description="Memory layout")
    mean_throughput: float = Field(..., gt=0, description="Mean operations per second (throughput)")
    std_throughput: float = Field(..., ge=0, description="Standard deviation of throughput")
    sample_count: int = Field(..., ge=1, description="Number of samples used for aggregation")
    mean_time_ms: float = Field(..., gt=0, description="Mean wall-clock time in ms")
    std_time_ms: float = Field(..., ge=0, description="Standard deviation of time in ms")
    t_stat: Optional[float] = Field(None, description="T-statistic (if compared against another group)")
    p_value: Optional[float] = Field(None, description="Raw p-value (if compared)")
    cohens_d: Optional[float] = Field(None, description="Effect size (Cohen's d)")
    fdr_adjusted_p: Optional[float] = Field(None, description="Benjamini-Hochberg adjusted p-value")

    @field_validator('configuration')
    @classmethod
    def validate_config(cls, v):
        if isinstance(v, str):
            return CounterConfiguration(v.lower())
        return v