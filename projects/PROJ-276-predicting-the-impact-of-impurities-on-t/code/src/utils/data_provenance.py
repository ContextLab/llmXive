from typing import Dict

def generate_provenance_header(source: str, timestamp: str, version: str) -> Dict[str, str]:
    """
    Generate a provenance header dictionary for dataset tracking.

    Args:
        source (str): The identifier of the data source (e.g., 'MaterialsProject', 'SuperCon').
        timestamp (str): The ISO format timestamp of data generation or retrieval.
        version (str): The version string of the dataset or processing pipeline.

    Returns:
        Dict[str, str]: A dictionary containing exactly the keys: 'source', 'timestamp', 'version'.
    """
    return {
        "source": source,
        "timestamp": timestamp,
        "version": version
    }
