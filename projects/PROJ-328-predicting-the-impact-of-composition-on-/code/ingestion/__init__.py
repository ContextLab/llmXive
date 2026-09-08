"""
Ingestion module initialization.
"""
from .aggregator import LiteratureAggregator, main
from .citation_tracker import CitationTracker, get_tracker, reset_tracker
from .cleaner import DataCleaner
from .generate_validation_report import load_ingestion_status, generate_validation_report, save_report
from .logger_setup import IngestionLogger, setup_ingestion_logging
from .pipeline_runner import run_pipeline
from .populate_sources import parse_verified_sources, save_sources_yaml
from .run_reference_validation import main as run_reference_validation_main
from .run_validation_report import main as run_validation_report_main
from .saver import calculate_md5, save_raw_data_with_checksums, save_validated_data
from .scaffold import setup_directories
from .source_search import generate_candidate_sources_file, generate_research_md_draft
from .validator import DataValidator

__all__ = [
    "LiteratureAggregator", "main",
    "CitationTracker", "get_tracker", "reset_tracker",
    "DataCleaner",
    "load_ingestion_status", "generate_validation_report", "save_report",
    "IngestionLogger", "setup_ingestion_logging",
    "run_pipeline",
    "parse_verified_sources", "save_sources_yaml",
    "run_reference_validation_main",
    "run_validation_report_main",
    "calculate_md5", "save_raw_data_with_checksums", "save_validated_data",
    "setup_directories",
    "generate_candidate_sources_file", "generate_research_md_draft",
    "DataValidator"
]
