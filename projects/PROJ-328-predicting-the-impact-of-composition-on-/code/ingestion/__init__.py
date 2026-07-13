"""
Ingestion module for aggregating, cleaning, and validating solder hardness data.
"""
from .aggregator import LiteratureAggregator, main as run_aggregator
from .cleaner import DataCleaner, main as run_cleaner
from .validator import DataValidator, main as run_validator
from .saver import (
    calculate_md5,
    save_raw_data_with_checksums,
    save_validated_data,
    main as run_saver,
)
from .citation_tracker import CitationTracker, get_tracker, reset_tracker
from .pipeline_runner import run_pipeline

__all__ = [
    "LiteratureAggregator",
    "run_aggregator",
    "DataCleaner",
    "run_cleaner",
    "DataValidator",
    "run_validator",
    "calculate_md5",
    "save_raw_data_with_checksums",
    "save_validated_data",
    "run_saver",
    "CitationTracker",
    "get_tracker",
    "reset_tracker",
    "run_pipeline",
]
