"""
Trait Data Caching Module (T025c)

Caches raw API responses from TRY, Phenoscape, and GBIF to ensure reproducibility
and satisfy Constitution Principles III (Provenance) and VII (Auditability).

Inputs:
    - Raw JSON responses from T025a (TRY) and T025b (Phenoscape/GBIF).
Outputs:
    - data/raw/traits/{source}_{species}.json
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Import config for paths
try:
    from src.utils.config import get_data_path
except ImportError:
    # Fallback for direct execution or different import structure
    from pathlib import Path
    def get_data_path():
        return Path(__file__).parent.parent.parent.parent / "data"

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Ensure the cache directory exists
DATA_ROOT = get_data_path()
CACHE_DIR = DATA_ROOT / "raw" / "traits"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def cache_raw_response(
    source: str,
    species_name: str,
    raw_response: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Save a raw API response to disk.

    Args:
        source: The data source identifier (e.g., 'try', 'phenoscape', 'gbif').
        species_name: The scientific name of the species (sanitized for filename).
        raw_response: The raw JSON-serializable dictionary from the API.
        metadata: Optional additional metadata to include in the cached file
                  (e.g., timestamp, request params).

    Returns:
        Path to the saved JSON file.

    Raises:
        ValueError: If raw_response is not JSON serializable.
        IOError: If writing to disk fails.
    """
    # Sanitize species name for filename
    safe_species = species_name.replace(" ", "_").replace("/", "_")
    filename = f"{source}_{safe_species}.json"
    file_path = CACHE_DIR / filename

    # Prepare the content to save
    cache_content = {
        "source": source,
        "species_name": species_name,
        "cached_at": datetime.utcnow().isoformat() + "Z",
        "metadata": metadata or {},
        "payload": raw_response
    }

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(cache_content, f, indent=2, ensure_ascii=False)
        logger.info(f"Cached raw response for {species_name} from {source} to {file_path}")
        return file_path
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize response for {species_name} from {source}: {e}")
        raise
    except IOError as e:
        logger.error(f"Failed to write cache file {file_path}: {e}")
        raise

def load_cached_response(
    source: str,
    species_name: str
) -> Optional[Dict[str, Any]]:
    """
    Load a previously cached raw response.

    Args:
        source: The data source identifier.
        species_name: The scientific name of the species.

    Returns:
        The cached dictionary if found, None otherwise.
    """
    safe_species = species_name.replace(" ", "_").replace("/", "_")
    filename = f"{source}_{safe_species}.json"
    file_path = CACHE_DIR / filename

    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.warning(f"Corrupt cache file {file_path}: {e}")
        return None

def main():
    """
    CLI Entry point for T025c.
    This script is primarily a utility module, but can be run to verify the cache directory.
    """
    logger.info(f"Trait cache directory initialized at: {CACHE_DIR}")
    if not CACHE_DIR.exists():
        logger.error("Cache directory could not be created.")
        sys.exit(1)
    logger.info("Cache system ready.")

if __name__ == "__main__":
    main()
