"""
Ingestion package for the solder hardness prediction pipeline.
Handles data fetching, cleaning, and validation.
"""

from ingestion.aggregator import LiteratureAggregator, main as aggregator_main
from ingestion.cleaner import DataCleaner, main as cleaner_main
from ingestion.validator import DataValidator, main as validator_main
from ingestion.pipeline_runner import run_pipeline, main as pipeline_main
from ingestion.populate_sources import parse_verified_sources, save_sources_yaml, main as populate_main
from ingestion.run_reference_validation import main as reference_validation_main
from ingestion.logger_setup import IngestionLogger, CitationTracker, setup_ingestion_logging, main as logger_setup_main
from ingestion.source_search import generate_candidate_sources_file, generate_research_md_draft, main as source_search_main
from ingestion.saver import calculate_md5, save_raw_data_with_checksums, save_validated_data, main as saver_main
from ingestion.report_generator import load_ingestion_status, generate_validation_report, main as report_main
from ingestion.generate_validation_report import load_ingestion_status, generate_validation_report, save_report, main as gen_report_main

__all__ = [
    'LiteratureAggregator',
    'aggregator_main',
    'DataCleaner',
    'cleaner_main',
    'DataValidator',
    'validator_main',
    'run_pipeline',
    'pipeline_main',
    'parse_verified_sources',
    'save_sources_yaml',
    'populate_main',
    'reference_validation_main',
    'IngestionLogger',
    'CitationTracker',
    'setup_ingestion_logging',
    'logger_setup_main',
    'generate_candidate_sources_file',
    'generate_research_md_draft',
    'source_search_main',
    'calculate_md5',
    'save_raw_data_with_checksums',
    'save_validated_data',
    'saver_main',
    'load_ingestion_status',
    'generate_validation_report',
    'report_main',
    'save_report',
    'gen_report_main'
]
