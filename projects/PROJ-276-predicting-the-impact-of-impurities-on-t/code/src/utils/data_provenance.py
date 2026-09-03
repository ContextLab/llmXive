"""
Data provenance utilities for tracking data lineage and metadata.
"""
from typing import Dict


def generate_provenance_header(source: str, timestamp: str, version: str) -> Dict[str, str]:
    """
    Generate a provenance header dictionary for data files.

    This function creates a standardized metadata dictionary to track the origin,
    generation time, and version of processed data files.

    Args:
        source: The name or identifier of the data source (e.g., 'Materials Project', 'SuperCon')
        timestamp: ISO format timestamp of when the data was processed
        version: Version string of the processing pipeline

    Returns:
        A dictionary containing exactly three keys: 'source', 'timestamp', and 'version'

    Example:
        >>> header = generate_provenance_header("Materials Project", "2023-10-27T10:00:00", "1.0.0")
        >>> assert header == {
        ...     "source": "Materials Project",
        ...     "timestamp": "2023-10-27T10:00:00",
        ...     "version": "1.0.0"
        ... }
    """
    return {
        "source": source,
        "timestamp": timestamp,
        "version": version
    }
