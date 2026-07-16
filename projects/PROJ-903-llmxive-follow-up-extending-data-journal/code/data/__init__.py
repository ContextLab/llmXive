"""
Data module for the llmXive automated science pipeline.

This package handles all data ingestion, validation, and preprocessing
for the Counterfactual Inspector Agent.

Public API:
- load_registry: Load dataset registry from YAML
- validate_registry: Validate registry entries against disk
- fetch_dataset: Download and cache datasets from real sources
- process_dataset: Clean and impute missing values
- LowPowerError: Exception for insufficient sample sizes
"""

from .registry import load_registry
from .validate_registry import validate_registry
from .loader import fetch_dataset, LowPowerError
from .processor import process_dataset, generate_basic_summary

__all__ = [
    "load_registry",
    "validate_registry",
    "fetch_dataset",
    "process_dataset",
    "generate_basic_summary",
    "LowPowerError",
]