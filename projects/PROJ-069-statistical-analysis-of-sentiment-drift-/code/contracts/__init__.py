"""
Contract definitions for the Statistical Analysis of Sentiment Drift project.
This module exports the core Pydantic models used for data validation.
"""
from .timeseries import TimeSeries
from .model_results import ModelResult, StationarityTestResult, CointegrationTestResult, GrangerCausalityResult, CollinearityDiagnostic, BootstrapValidationResult
from .recession_periods import RecessionPeriod

__all__ = [
    "TimeSeries",
    "ModelResult",
    "StationarityTestResult",
    "CointegrationTestResult",
    "GrangerCausalityResult",
    "CollinearityDiagnostic",
    "BootstrapValidationResult",
    "RecessionPeriod",
]
