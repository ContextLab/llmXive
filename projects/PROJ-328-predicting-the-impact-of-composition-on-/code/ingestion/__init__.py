"""
Ingestion module for data collection and preprocessing.
"""
from ingestion.aggregator import LiteratureAggregator
from ingestion.cleaner import DataCleaner
from ingestion.validator import DataValidator
from ingestion.populate_sources import parse_verified_sources, save_sources_yaml

__all__ = [
    'LiteratureAggregator',
    'DataCleaner',
    'DataValidator',
    'parse_verified_sources',
    'save_sources_yaml'
]