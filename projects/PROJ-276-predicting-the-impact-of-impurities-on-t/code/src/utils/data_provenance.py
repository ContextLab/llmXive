"""
Data provenance utilities for tracking data lineage and source metadata.
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional


def generate_provenance_header(
    source: str,
    timestamp: str,
    version: str,
    additional_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a minified JSON provenance header string.

    The return value is a UTF-8 encoded, minified JSON string formatted as:
    `# PROVENANCE: {...}`

    Args:
        source (str): The data source identifier (e.g., 'Materials Project', 'SuperCon').
        timestamp (str): ISO format timestamp of data generation/fetch.
        version (str): Version string of the data or processing script.
        additional_metadata (Optional[Dict[str, Any]]): Optional extra key-value pairs
            to include in the provenance object.

    Returns:
        str: A string starting with '# PROVENANCE: ' followed by a minified JSON object.
    """
    provenance_data: Dict[str, Any] = {
        "source": source,
        "timestamp": timestamp,
        "version": version
    }

    if additional_metadata:
        provenance_data.update(additional_metadata)

    # Ensure keys are sorted for reproducibility
    minified_json = json.dumps(provenance_data, separators=(',', ':'), sort_keys=True)

    return f"# PROVENANCE: {minified_json}"
