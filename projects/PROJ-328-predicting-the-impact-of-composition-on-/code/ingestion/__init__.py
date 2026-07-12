"""
Ingestion module for solder hardness data.
Contains aggregators, cleaners, validators, and savers.
"""
from .aggregator import LiteratureAggregator, main as aggregator_main
from .cleaner import DataCleaner, main as cleaner_main
from .validator import DataValidator, main as validator_main
from .saver import calculate_md5, save_raw_data_with_checksums, main as saver_main

__all__ = [
    'LiteratureAggregator', 'aggregator_main',
    'DataCleaner', 'cleaner_main',
    'DataValidator', 'validator_main',
    'calculate_md5', 'save_raw_data_with_checksums', 'saver_main'
]
