"""
Ingestion module for solder hardness data aggregation and processing.
"""
from .aggregator import LiteratureAggregator, main
from .cleaner import DataCleaner, main as clean_main
from .validator import DataValidator, main as validate_main
from .saver import calculate_md5, save_raw_data_with_checksums, save_validated_data, main as save_main
from .citation_tracker import CitationTracker, get_tracker, reset_tracker, main as citation_main
from .pipeline_runner import run_pipeline

__all__ = [
    "LiteratureAggregator",
    "DataCleaner",
    "DataValidator",
    "calculate_md5",
    "save_raw_data_with_checksums",
    "save_validated_data",
    "CitationTracker",
    "run_pipeline",
    "main",
    "clean_main",
    "validate_main",
    "save_main",
    "citation_main"
]
