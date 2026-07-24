"""
Pydantic schemas for benchmark data validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class BenchmarkRun(BaseModel):
    """Schema for a single row of raw benchmark data."""
    thread_count: int = Field(..., description="Number of threads used")
    configuration: str = Field(..., description="Either 'packed' or 'padded'")
    iteration_count: int = Field(..., description="Number of atomic increments per thread")
    wall_clock_time_ms: float = Field(..., description="Time taken in milliseconds")
    status: str = Field(default="OK", description="Status of the run (OK, TIMEOUT, ERROR)")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

class AggregatedResult(BaseModel):
    """Schema for aggregated results per thread count and configuration."""
    thread_count: int
    configuration: str
    mean_throughput: float
    std_throughput: float
    count: int
    ci_95: float

class StatisticalComparison(BaseModel):
    """Schema for the final statistical comparison output."""
    thread_count: int
    config: str
    t_stat: float
    p_value: float
    cohens_d: float
    fdr_adjusted_p: float