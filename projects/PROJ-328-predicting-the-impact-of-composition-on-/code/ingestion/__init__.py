"""
Ingestion module for solder hardness data pipeline.

This package handles:
- Data aggregation from multiple sources (T012)
- Data cleaning and standardization (T013)
- Validation logic (T014)
- Scaffolding and directory setup (T005)
"""
from .aggregator import LiteratureAggregator
from .cleaner import DataCleaner
from .validator import DataValidator, DataInsufficientError
from .saver import save_raw_data_with_checksums, save_validated_data
from .scaffold import setup_directories
from .pipeline_runner import run_pipeline

__all__ = [
    "LiteratureAggregator",
    "DataCleaner",
    "DataValidator",
    "DataInsufficientError",
    "save_raw_data_with_checksums",
    "save_validated_data",
    "setup_directories",
    "run_pipeline",
]