"""
Data provenance utilities for tracking data lineage and metadata.
"""
from typing import Dict


def generate_provenance_header(source: str, timestamp: str, version: str) -> Dict[str, str]:
    """
    Generate a standardized provenance header dictionary for data files.

    Args:
        source (str): Identifier for the data source (e.g., 'Materials Project', 'SuperCon').
        timestamp (str): ISO 8601 formatted timestamp of data generation or extraction.
        version (str): Version string of the dataset or processing pipeline.

    Returns:
        Dict[str, str]: A dictionary containing exactly the keys: 'source', 'timestamp', 'version'.
    """
    return {
        "source": source,
        "timestamp": timestamp,
        "version": version
    }
