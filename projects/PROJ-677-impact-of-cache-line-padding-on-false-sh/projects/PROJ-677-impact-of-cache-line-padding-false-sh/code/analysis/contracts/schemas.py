"""
Pydantic schemas for BenchmarkRun and AggregatedResult.

These schemas enforce the data contract for the benchmark pipeline:
- BenchmarkRun: Raw CSV row from the C++ benchmark executable.
- AggregatedResult: Statistical summary (mean, std, etc.) per configuration.
"""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic.alias_generators import to_snake

# ----------------------------------------------------------------------
# Raw Benchmark Run Schema
# ----------------------------------------------------------------------
class BenchmarkRun(BaseModel):
    """
    Represents a single row of output from the C++ benchmark executable.
    
    Expected CSV columns:
    - thread_count: int (1, 2, 4, 8)
    - configuration: str ('packed' or 'padded')
    - iteration_count: int (number of atomic increments per thread)
    - wall_clock_time_ms: float (execution time in milliseconds)
    - status: str (optional, 'TIMEOUT' or 'OK')
    """
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True
    )

    thread_count: int = Field(
        ..., 
        ge=1, 
        le=16, 
        description="Number of concurrent threads used"
    )
    configuration: Literal["packed", "padded"] = Field(
        ..., 
        description="Memory layout configuration"
    )
    iteration_count: int = Field(
        ..., 
        gt=0, 
        description="Number of atomic increments performed per thread"
    )
    wall_clock_time_ms: float = Field(
        ..., 
        gt=0.0, 
        description="Total wall-clock time in milliseconds"
    )
    status: Optional[Literal["OK", "TIMEOUT"]] = Field(
        "OK", 
        description="Execution status flag"
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="When the run was recorded"
    )

    @field_validator('thread_count')
    @classmethod
    def validate_thread_count(cls, v):
        if v not in [1, 2, 4, 8]:
            # Allow 1 for single-threaded validation, but warn or restrict if strict
            pass 
        return v

    @property
    def throughput_ops_per_sec(self) -> float:
        """Calculate operations per second."""
        if self.wall_clock_time_ms <= 0:
            return 0.0
        # Total ops = thread_count * iteration_count
        total_ops = self.thread_count * self.iteration_count
        return (total_ops / (self.wall_clock_time_ms / 1000.0))

    def is_valid_for_analysis(self) -> bool:
        """Check if this run is valid for statistical aggregation."""
        return self.status == "OK" and self.wall_clock_time_ms > 0.0

# ----------------------------------------------------------------------
# Aggregated Result Schema
# ----------------------------------------------------------------------
class AggregatedResult(BaseModel):
    """
    Represents the aggregated statistical results for a specific 
    (thread_count, configuration) pair.
    
    Used as the output of the analysis phase (T031).
    """
    model_config = ConfigDict(
        populate_by_name=True
    )

    thread_count: int = Field(
        ..., 
        description="Thread count for this aggregation"
    )
    configuration: Literal["packed", "padded"] = Field(
        ..., 
        description="Memory layout configuration"
    )
    
    # Basic Statistics
    sample_count: int = Field(
        ..., 
        ge=1, 
        description="Number of raw runs aggregated"
    )
    mean_throughput: float = Field(
        ..., 
        description="Mean operations per second"
    )
    std_throughput: float = Field(
        ..., 
        ge=0.0, 
        description="Standard deviation of throughput"
    )
    min_throughput: float = Field(
        ..., 
        description="Minimum observed throughput"
    )
    max_throughput: float = Field(
        ..., 
        description="Maximum observed throughput"
    )

    # Statistical Test Results (populated in T032/T033)
    t_stat: Optional[float] = Field(
        None, 
        description="T-statistic from two-sample t-test (vs packed)"
    )
    p_value: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="Raw p-value from t-test"
    )
    cohens_d: Optional[float] = Field(
        None, 
        description="Effect size (Cohen's d)"
    )
    fdr_adjusted_p: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="Benjamini-Hochberg FDR adjusted p-value"
    )

    def __hash__(self):
        return hash((self.thread_count, self.configuration))

    def __eq__(self, other):
        if not isinstance(other, AggregatedResult):
            return False
        return (
            self.thread_count == other.thread_count and
            self.configuration == other.configuration
        )