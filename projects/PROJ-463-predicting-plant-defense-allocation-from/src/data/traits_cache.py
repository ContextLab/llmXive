"""
Trait data caching module.

Caches raw API responses from TRY, Phenoscape, and GBIF to satisfy
Constitution Principles III (Provenance) and VII (Reproducibility).

Output: data/raw/traits/{source}_{species}.json
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib

# Ensure logging is configured
from src.utils.logger import get_logger
logger = get_logger(__name__)

# Constants
DATA_ROOT = Path(os.getenv("PROJECT_ROOT", Path(__file__).parent.parent.parent.parent))
CACHE_DIR = DATA_ROOT / "data" / "raw" / "traits"

def _ensure_cache_dir() -> Path:
    """Ensure the cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR

def _sanitize_species_name(species_name: str) -> str:
    """
    Sanitize species name for use in filenames.
    Replaces spaces and special characters with underscores.
    """
    return species_name.replace(" ", "_").replace("/", "_").replace(":", "_").replace(".", "_")

def _generate_cache_filename(source: str, species_name: str) -> str:
    """Generate the cache filename: {source}_{species}.json"""
    safe_name = _sanitize_species_name(species_name)
    return f"{source}_{safe_name}.json"

def cache_raw_response(
    source: str,
    species_name: str,
    raw_response: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Cache a raw API response to disk.
    
    Args:
        source: The data source identifier (e.g., 'try', 'phenoscape', 'gbif')
        species_name: The species name associated with the response
        raw_response: The raw JSON response dictionary from the API
        metadata: Optional additional metadata to include (e.g., timestamp, query_params)
    
    Returns:
        Path to the cached file
    
    Raises:
        ValueError: If raw_response is not a valid JSON-serializable dict
        IOError: If writing to disk fails
    """
    if not isinstance(raw_response, dict):
        raise ValueError(f"raw_response must be a dictionary, got {type(raw_response)}")

    cache_path = _ensure_cache_dir() / _generate_cache_filename(source, species_name)

    # Prepare the payload
    payload = {
        "source": source,
        "species_name": species_name,
        "cached_at": datetime.utcnow().isoformat() + "Z",
        "data": raw_response
    }

    if metadata:
        payload["metadata"] = metadata

    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        logger.info(f"Cached {source} response for {species_name} to {cache_path}")
        return cache_path
    except IOError as e:
        logger.error(f"Failed to write cache file {cache_path}: {e}")
        raise

def load_cached_response(source: str, species_name: str) -> Optional[Dict[str, Any]]:
    """
    Load a cached raw response from disk.
    
    Args:
        source: The data source identifier
        species_name: The species name
    
    Returns:
        The cached response dictionary if found, None otherwise
    """
    cache_path = _ensure_cache_dir() / _generate_cache_filename(source, species_name)
    
    if not cache_path.exists():
        logger.debug(f"Cache miss for {source} {species_name} at {cache_path}")
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded cached {source} response for {species_name}")
        return data.get("data")
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to read cache file {cache_path}: {e}")
        return None

def clear_cache_for_species(species_name: str, source: Optional[str] = None) -> int:
    """
    Clear cached responses for a specific species.
    
    Args:
        species_name: The species name
        source: Optional specific source to clear. If None, clears all sources.
    
    Returns:
        Number of files deleted
    """
    safe_name = _sanitize_species_name(species_name)
    deleted_count = 0

    for file_path in CACHE_DIR.glob(f"*{safe_name}.json"):
        if source is None or file_path.name.startswith(f"{source}_"):
            try:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"Deleted cache file: {file_path}")
            except OSError as e:
                logger.error(f"Failed to delete {file_path}: {e}")

    return deleted_count

def main():
    """
    CLI entry point for testing the caching module.
    Usage: python -m src.data.traits_cache --source <source> --species <species> --data <json_string>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Cache trait data responses")
    parser.add_argument("--source", required=True, help="Data source (try, phenoscape, gbif)")
    parser.add_argument("--species", required=True, help="Species name")
    parser.add_argument("--data", required=True, help="JSON string of the raw response")
    parser.add_argument("--load", action="store_true", help="Load instead of cache")
    
    args = parser.parse_args()

    try:
        raw_data = json.loads(args.data)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in --data: {e}")
        sys.exit(1)

    if args.load:
        result = load_cached_response(args.source, args.species)
        if result:
            print(json.dumps(result, indent=2))
            sys.exit(0)
        else:
            print(f"No cache found for {args.source} {args.species}")
            sys.exit(1)
    else:
        try:
            path = cache_raw_response(args.source, args.species, raw_data)
            print(f"Successfully cached to: {path}")
            sys.exit(0)
        except Exception as e:
            print(f"Error caching data: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
