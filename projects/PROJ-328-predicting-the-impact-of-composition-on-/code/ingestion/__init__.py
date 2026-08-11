"""
Ingestion module for solder hardness data aggregation and validation.

This module provides the core infrastructure for fetching, cleaning,
and validating solder alloy composition and hardness data from various sources.
"""

from .aggregator import LiteratureAggregator, main as aggregator_main
from .cleaner import DataCleaner, main as cleaner_main
from .validator import DataValidator, DataInsufficientError, main as validator_main
from .citation_tracker import CitationTracker, get_tracker, reset_tracker
from .logger_setup import IngestionLogger, setup_ingestion_logging
from .saver import calculate_md5, save_raw_data_with_checksums, save_validated_data
from .pipeline_runner import run_pipeline
from .generate_validation_report import generate_validation_report, save_report

__all__ = [
    'LiteratureAggregator',
    'DataCleaner', 
    'DataValidator',
    'DataInsufficientError',
    'CitationTracker',
    'get_tracker',
    'reset_tracker',
    'IngestionLogger',
    'setup_ingestion_logging',
    'calculate_md5',
    'save_raw_data_with_checksums',
    'save_validated_data',
    'run_pipeline',
    'generate_validation_report',
    'save_report',
    'aggregator_main',
    'cleaner_main',
    'validator_main'
]

# Initialize logger when module is imported
def _setup_module_logging():
    """Set up logging for the ingestion module."""
    try:
        setup_ingestion_logging()
    except Exception:
        # Logger might already be configured
        pass

_setup_module_logging()
