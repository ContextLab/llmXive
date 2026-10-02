"""
Contracts module for benchmark data schemas.
Provides Pydantic models for validation of benchmark runs, aggregated results,
and statistical comparisons.
"""
from .benchmark_contracts import BenchmarkRun, AggregatedResult, StatisticalComparison, get_all_schemas

__all__ = [
    "BenchmarkRun",
    "AggregatedResult",
    "StatisticalComparison",
    "get_all_schemas",
]
