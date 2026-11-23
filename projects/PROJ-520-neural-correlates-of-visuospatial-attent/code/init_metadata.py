import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

from logger import get_logger
from config import get_paths

logger = get_logger(__name__)

def get_metadata_schema() -> Dict[str, Any]:
    """
    Return the default schema for metadata.json.
    
    Returns:
        Dictionary representing the metadata schema.
    """
    return {
        "skipped_electrodes": [],
        "assumptions": {},
        "data_source_url": None,
        "fetch_method": None
    }

def initialize_metadata(metadata_path: str) -> None:
    """
    Initialize metadata.json with the default schema if it doesn't exist.
    
    Args:
        metadata_path: Path to the metadata.json file.
    """
    path = Path(metadata_path)
    
    if path.exists():
        logger.info(f"Metadata file already exists at {metadata_path}. Skipping initialization.")
        # Verify schema keys exist, add missing ones
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            schema = get_metadata_schema()
            updated = False
            for key in schema:
                if key not in data:
                    data[key] = schema[key]
                    updated = True
            if updated:
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info("Updated existing metadata with missing schema keys.")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read existing metadata: {e}. Overwriting with default schema.")
            with open(path, 'w') as f:
                json.dump(get_metadata_schema(), f, indent=2)
    else:
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(get_metadata_schema(), f, indent=2)
        logger.info(f"Initialized metadata file at {metadata_path}")

def main():
    """Main entry point for metadata initialization."""
    paths = get_paths()
    metadata_path = paths['output_path'] / 'metadata.json'
    initialize_metadata(str(metadata_path))

if __name__ == "__main__":
    main()
