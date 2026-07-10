"""Data module for alloy oxidation prediction pipeline."""
from .fetcher import fetch_data, main as fetch_main
from .processor import process_data, main as process_main

__all__ = ['fetch_data', 'fetch_main', 'process_data', 'process_main']