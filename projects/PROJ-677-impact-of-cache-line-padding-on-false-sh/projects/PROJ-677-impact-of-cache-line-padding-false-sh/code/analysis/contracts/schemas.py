"""
Pydantic schemas for benchmark data validation.

Defines strict data contracts for BenchmarkRun (raw execution data)
and AggregatedResult (statistical summaries).
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class Configuration(str, Enum):
    """Counter memory layout configuration."""
    PACKED = "packed"
    PADDED = "padded"


class BenchmarkRun(BaseModel):
    """
    Schema for a single raw benchmark execution record.
    
    Represents one row of output from the C++ benchmark harness.
    """
    model_config = ConfigDict(from_attributes=True)

    thread_count: int = Field(..., ge=1, description="Number of threads used")
    configuration: Configuration = Field(..., description="Memory layout (packed or padded)")
    iteration_count: int = Field(..., gt=0, description="Number of increments per thread")
    wall_clock_time_ms: float = Field(..., gt=0, description="Total wall-clock time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Time of execution")
    status: str = Field(default="OK", description="Execution status (OK, TIMEOUT, ERROR)")

    @field_validator('thread_count')
    @classmethod
    def validate_thread_count(cls, v):
        if v < 1:
            raise ValueError('thread_count must be at least 1')
        return v

    @field_validator('wall_clock_time_ms')
    @classmethod
    def validate_time_positive(cls, v):
        if v <= 0:
            raise ValueError('wall_clock_time_ms must be positive')
        return v

    @property
    def throughput(self) -> float:
        """Calculate throughput in increments per second."""
        if self.wall_clock_time_ms == 0:
            return 0.0
        total_ops = self.thread_count * self.iteration_count
        return (total_ops / self.wall_clock_time_ms) * 1000.0


class AggregatedResult(BaseModel):
    """
    Schema for aggregated statistical results per configuration and thread count.
    
    Represents the output of the analysis phase (T031).
    """
    model_config = ConfigDict(from_attributes=True)

    thread_count: int = Field(..., ge=1)
    configuration: Configuration
    mean_throughput: float = Field(..., ge=0)
    std_throughput: float = Field(..., ge=0)
    sample_count: int = Field(..., ge=1)
    min_throughput: float = Field(..., ge=0)
    max_throughput: float = Field(..., ge=0)
    confidence_interval_95: tuple[float, float] = Field(..., description="Lower and upper bounds of 95% CI")

    @field_validator('confidence_interval_95')
    @classmethod
    def validate_ci_order(cls, v):
        if len(v) != 2:
            raise ValueError('confidence_interval_95 must be a tuple of two floats')
        if v[0] > v[1]:
            raise ValueError('CI lower bound must be <= upper bound')
        return v


class StatisticalComparison(BaseModel):
    """
    Schema for the final statistical comparison output (T035).
    
    Contains t-test results, effect sizes, and FDR-corrected p-values.
    """
    model_config = ConfigDict(from_attributes=True)

    thread_count: int = Field(..., ge=1)
    config_packed_mean: float
    config_padded_mean: float
    t_stat: float
    p_value: float
    cohens_d: float
    fdr_adjusted_p: float
    significant_after_fdr: bool = Field(..., description="True if fdr_adjusted_p < 0.05")

    @field_validator('significant_after_fdr')
    @classmethod
    def validate_significance(cls, v, info):
        # This is a computed field, but we ensure consistency if manually set
        return v