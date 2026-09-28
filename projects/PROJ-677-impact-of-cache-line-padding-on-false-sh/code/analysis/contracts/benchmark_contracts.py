"""
Pydantic schemas for benchmark data contracts.

Defines the data structures for:
- BenchmarkRun: Raw data from a single benchmark execution
- AggregatedResult: Statistical aggregation of multiple runs
- StatisticalComparison: Results of t-tests and effect size calculations
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime
import numpy as np
import json

# Type aliases for clarity
ThreadCount = int
ConfigType = Literal["packed", "padded"]

class BenchmarkRun(BaseModel):
    """
    Represents a single benchmark run result.
    
    Corresponds to one row in the raw CSV output from the C++ benchmark harness.
    """
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="ISO 8601 timestamp of the run"
    )
    thread_count: ThreadCount = Field(
        ..., 
        gt=0,
        description="Number of threads used in this run"
    )
    configuration: ConfigType = Field(
        ...,
        description="Counter configuration: 'packed' or 'padded'"
    )
    iteration_count: int = Field(
        ...,
        gt=0,
        description="Number of atomic increments performed per thread"
    )
    wall_clock_time_ms: float = Field(
        ...,
        gt=0,
        description="Total wall-clock time in milliseconds"
    )
    cpu_model: Optional[str] = Field(
        None,
        description="CPU model string from hardware detection"
    )
    cache_line_size: Optional[int] = Field(
        None,
        ge=32,
        le=128,
        description="Detected cache line size in bytes"
    )
    
    @field_validator('configuration')
    @classmethod
    def validate_config(cls, v: str) -> ConfigType:
        if v not in ("packed", "padded"):
            raise ValueError(f"configuration must be 'packed' or 'padded', got '{v}'")
        return v  # type: ignore
    
    @field_validator('wall_clock_time_ms')
    @classmethod
    def validate_time_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"wall_clock_time_ms must be positive, got {v}")
        return v
    
    @property
    def throughput_ops_per_sec(self) -> float:
        """Calculate throughput in operations per second."""
        total_ops = self.thread_count * self.iteration_count
        time_sec = self.wall_clock_time_ms / 1000.0
        return total_ops / time_sec
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump()
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json()

class AggregatedResult(BaseModel):
    """
    Represents aggregated statistics for a specific thread count and configuration.
    
    Computed from multiple BenchmarkRun instances.
    """
    thread_count: ThreadCount = Field(..., gt=0)
    configuration: ConfigType = Field(...)
    run_count: int = Field(
        ...,
        ge=1,
        description="Number of runs included in aggregation"
    )
    mean_throughput: float = Field(
        ...,
        gt=0,
        description="Mean throughput in operations per second"
    )
    std_throughput: float = Field(
        ...,
        ge=0,
        description="Standard deviation of throughput"
    )
    min_throughput: float = Field(
        ...,
        gt=0,
        description="Minimum throughput observed"
    )
    max_throughput: float = Field(
        ...,
        gt=0,
        description="Maximum throughput observed"
    )
    mean_wall_clock_ms: float = Field(
        ...,
        gt=0,
        description="Mean wall-clock time in milliseconds"
    )
    std_wall_clock_ms: float = Field(
        ...,
        ge=0,
        description="Standard deviation of wall-clock time"
    )
    iteration_count: int = Field(
        ...,
        gt=0,
        description="Iterations per thread (should be consistent across runs)"
    )
    aggregated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of aggregation"
    )
    
    @field_validator('configuration')
    @classmethod
    def validate_config(cls, v: str) -> ConfigType:
        if v not in ("packed", "padded"):
            raise ValueError(f"configuration must be 'packed' or 'padded', got '{v}'")
        return v  # type: ignore
    
    @classmethod
    def from_runs(cls, runs: List[BenchmarkRun]) -> "AggregatedResult":
        """
        Create an AggregatedResult from a list of BenchmarkRun instances.
        
        All runs must have the same thread_count, configuration, and iteration_count.
        """
        if not runs:
            raise ValueError("Cannot aggregate empty list of runs")
        
        # Validate consistency
        first = runs[0]
        for i, run in enumerate(runs[1:], 1):
            if run.thread_count != first.thread_count:
                raise ValueError(f"Run {i} has different thread_count: {run.thread_count} vs {first.thread_count}")
            if run.configuration != first.configuration:
                raise ValueError(f"Run {i} has different configuration: {run.configuration} vs {first.configuration}")
            if run.iteration_count != first.iteration_count:
                raise ValueError(f"Run {i} has different iteration_count: {run.iteration_count} vs {first.iteration_count}")
        
        throughputs = [run通过put for run in runs]
        wall_clocks = [run.wall_clock_time_ms for run in runs]
        
        return cls(
            thread_count=first.thread_count,
            configuration=first.configuration,
            run_count=len(runs),
            mean_throughput=float(np.mean(throughputs)),
            std_throughput=float(np.std(throughputs)),
            min_throughput=float(np.min(throughputs)),
            max_throughput=float(np.max(throughputs)),
            mean_wall_clock_ms=float(np.mean(wall_clocks)),
            std_wall_clock_ms=float(np.std(wall_clocks)),
            iteration_count=first.iteration_count
        )

class StatisticalComparison(BaseModel):
    """
    Represents the result of a statistical comparison between packed and padded configurations.
    
    Contains t-test results, p-values, effect sizes, and FDR-corrected p-values.
    """
    thread_count: ThreadCount = Field(..., gt=0)
    padded_mean: float = Field(..., gt=0)
    padded_std: float = Field(..., ge=0)
    padded_n: int = Field(..., ge=1)
    packed_mean: float = Field(..., gt=0)
    packed_std: float = Field(..., ge=0)
    packed_n: int = Field(..., ge=1)
    t_statistic: float = Field(...)
    p_value: float = Field(
        ...,
        ge=0,
        le=1,
        description="Raw p-value from two-sample t-test"
    )
    cohens_d: float = Field(
        ...,
        description="Effect size (Cohen's d)"
    )
    fdr_adjusted_p: float = Field(
        ...,
        ge=0,
        le=1,
        description="Benjamini-Hochberg FDR adjusted p-value"
    )
    significant_at_005: bool = Field(
        ...,
        description="Whether fdr_adjusted_p < 0.05"
    )
    significant_at_01: bool = Field(
        ...,
        description="Whether fdr_adjusted_p < 0.10"
    )
    comparison_method: str = Field(
        default="two_sample_t_test",
        description="Statistical test method used"
    )
    fdr_method: str = Field(
        default="benjamini_hochberg",
        description="FDR correction method used"
    )
    computed_at: datetime = Field(
        default_factory=datetime.utcnow
    )
    
    @field_validator('p_value', 'fdr_adjusted_p')
    @classmethod
    def validate_probability(cls, v: float) -> float:
        if not (0 <= v <= 1):
            raise ValueError(f"Probability value must be in [0, 1], got {v}")
        return v
    
    @classmethod
    def create(
        cls,
        thread_count: int,
        padded_result: AggregatedResult,
        packed_result: AggregatedResult,
        t_stat: float,
        p_val: float,
        cohens_d_val: float,
        fdr_p_val: float
    ) -> "StatisticalComparison":
        """Factory method to create a StatisticalComparison instance."""
        return cls(
            thread_count=thread_count,
            padded_mean=padded_result.mean_throughput,
            padded_std=padded_result.std_throughput,
            padded_n=padded_result.run_count,
            packed_mean=packed_result.mean_throughput,
            packed_std=packed_result.std_throughput,
            packed_n=packed_result.run_count,
            t_statistic=t_stat,
            p_value=p_val,
            cohens_d=cohens_d_val,
            fdr_adjusted_p=fdr_p_val,
            significant_at_005=fdr_p_val < 0.05,
            significant_at_01=fdr_p_val < 0.10
        )

# Schema export for documentation/verification
SCHEMA_VERSION = "1.0.0"

def get_all_schemas() -> dict:
    """Return a dictionary of all schema definitions for documentation."""
    return {
        "BenchmarkRun": BenchmarkRun.model_json_schema(),
        "AggregatedResult": AggregatedResult.model_json_schema(),
        "StatisticalComparison": StatisticalComparison.model_json_schema()
    }