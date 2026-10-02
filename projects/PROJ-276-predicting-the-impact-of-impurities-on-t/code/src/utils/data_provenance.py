"""
Data provenance utilities for tracking the origin and processing history of datasets.
"""
from typing import Dict
from datetime import datetime


def generate_provenance_header(source: str, timestamp: str, version: str) -> dict:
    """
    Generate a standardized provenance header dictionary for data artifacts.

    Args:
        source (str): The identifier of the data source (e.g., 'Materials Project', 'SuperCon').
        timestamp (str): ISO 8601 formatted timestamp of when the data was processed.
        version (str): The version string of the processing pipeline or dataset.

    Returns:
        dict: A dictionary containing exactly the keys 'source', 'timestamp', and 'version'.
    """
    return {
        "source": source,
        "timestamp": timestamp,
        "version": version
    }
