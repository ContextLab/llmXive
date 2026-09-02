"""
Ingestion module for the solder hardness prediction pipeline.
"""

from .aggregator import LiteratureAggregator, main as aggregator_main
from .cleaner import DataCleaner, main as cleaner_main
from .validator import DataValidator, main as validator_main
from .populate_sources import main as populate_sources_main
from .pipeline_runner import run_pipeline, main as pipeline_main
from .saver import save_raw_data_with_checksums, save_validated_data
from .citation_tracker import CitationTracker, get_tracker

__all__ = [
    "LiteratureAggregator",
    "DataCleaner", 
    "DataValidator",
    "CitationTracker",
    "run_pipeline",
    "save_raw_data_with_checksums",
    "save_validated_data",
    "aggregator_main",
    "cleaner_main",
    "validator_main",
    "populate_sources_main",
    "pipeline_main",
    "get_tracker"
]