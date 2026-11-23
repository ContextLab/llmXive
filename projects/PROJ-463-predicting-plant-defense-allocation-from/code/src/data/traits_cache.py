"""
Trait Caching Module for Plant Defense Allocation Pipeline.

This module implements caching for raw API responses from external trait databases
(TRY, Phenoscape, GBIF) to satisfy Constitution Principles III (Data Provenance)
and VII (Reproducibility).

It ensures that raw responses are saved to disk BEFORE any processing occurs,
allowing for audit trails and re-processing without re-fetching.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib

from src.utils.logger import get_logger
from src.utils.config import get_data_path

# Initialize logger
logger = get_logger(__name__)

def _get_traits_cache_dir() -> Path:
    """
    Get the directory for caching trait responses.
    Creates the directory if it doesn't exist.
    """
    data_root = get_data_path()
    cache_dir = data_root / "raw" / "traits"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def _sanitize_species_name(species_name: str) -> str:
    """
    Sanitize species name for use in filenames.
    Replaces spaces and invalid characters with underscores.
    """
    return species_name.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").strip()

def _compute_checksum(content: bytes) -> str:
    """Compute SHA256 checksum of content."""
    return hashlib.sha256(content).hexdigest()

def cache_raw_response(
    source: str,
    species: str,
    raw_response: Dict[str, Any],
    request_metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Cache a raw API response from a trait database.

    This function saves the raw JSON response to disk immediately upon receipt,
    before any processing or interpretation occurs. This satisfies Constitution
    Principles III and VII.

    Args:
        source: The data source (e.g., 'TRY', 'Phenoscape', 'GBIF')
        species: The species name for which data was fetched
        raw_response: The raw JSON response dictionary from the API
        request_metadata: Optional metadata about the request (URL, timestamp, params)

    Returns:
        Path to the cached file

    Raises:
        ValueError: If raw_response is not a valid JSON-serializable dictionary
        IOError: If the file cannot be written
    """
    if not isinstance(raw_response, dict):
        raise ValueError(f"raw_response must be a dictionary, got {type(raw_response)}")

    cache_dir = _get_traits_cache_dir()
    sanitized_species = _sanitize_species_name(species)
    filename = f"{source}_{sanitized_species}.json"
    filepath = cache_dir / filename

    # Prepare the cache entry with provenance info
    cache_entry = {
        "source": source,
        "species": species,
        "cached_at": datetime.utcnow().isoformat() + "Z",
        "request_metadata": request_metadata or {},
        "payload": raw_response
    }

    # Serialize to JSON with indentation for readability
    json_content = json.dumps(cache_entry, indent=2, ensure_ascii=False)
    content_bytes = json_content.encode('utf-8')

    # Write to disk
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_content)
        logger.info(f"Cached raw response for {source} / {species} to {filepath}")
    except IOError as e:
        logger.error(f"Failed to write cache file for {source}/{species}: {e}")
        raise

    return filepath

def load_cached_response(
    source: str,
    species: str
) -> Optional[Dict[str, Any]]:
    """
    Load a previously cached raw response.

    Args:
        source: The data source (e.g., 'TRY', 'Phenoscape', 'GBIF')
        species: The species name

    Returns:
        The cached payload dictionary, or None if not found
    """
    cache_dir = _get_traits_cache_dir()
    sanitized_species = _sanitize_species_name(species)
    filename = f"{source}_{sanitized_species}.json"
    filepath = cache_dir / filename

    if not filepath.exists():
        logger.debug(f"No cached response found for {source}/{species} at {filepath}")
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            cache_entry = json.load(f)

        # Validate structure
        if not isinstance(cache_entry, dict):
            logger.warning(f"Invalid cache format for {source}/{species}, ignoring")
            return None

        if cache_entry.get("source") != source:
            logger.warning(f"Source mismatch in cache for {species}: expected {source}, got {cache_entry.get('source')}")
            return None

        logger.info(f"Loaded cached response for {source}/{species} from {filepath}")
        return cache_entry.get("payload")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse cache file for {source}/{species}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading cache for {source}/{species}: {e}")
        return None

def clear_cache_for_species(species: str) -> int:
    """
    Remove all cached responses for a specific species.
    Useful for forcing a re-fetch during debugging.

    Args:
        species: The species name

    Returns:
        Number of files deleted
    """
    cache_dir = _get_traits_cache_dir()
    sanitized_species = _sanitize_species_name(species)
    pattern = f"*{sanitized_species}.json"
    count = 0

    for filepath in cache_dir.glob(pattern):
        try:
            filepath.unlink()
            count += 1
            logger.info(f"Deleted cache file: {filepath}")
        except Exception as e:
            logger.warning(f"Failed to delete {filepath}: {e}")

    return count

def main() -> None:
    """
    CLI entry point for the traits cache module.
    Currently supports:
      - --check <source> <species>: Check if a cache entry exists
      - --clear <species>: Clear cache for a species
      - --info: Show cache directory location
    """
    import argparse

    parser = argparse.ArgumentParser(description="Manage trait data cache")
    parser.add_argument("--check", nargs=2, metavar=("SOURCE", "SPECIES"),
                      help="Check if a cache entry exists")
    parser.add_argument("--clear", metavar="SPECIES",
                      help="Clear cache for a specific species")
    parser.add_argument("--info", action="store_true",
                      help="Show cache directory information")

    args = parser.parse_args()

    if args.info:
        cache_dir = _get_traits_cache_dir()
        print(f"Cache directory: {cache_dir}")
        print(f"Exists: {cache_dir.exists()}")
        if cache_dir.exists():
            files = list(cache_dir.glob("*.json"))
            print(f"Files in cache: {len(files)}")
        return

    if args.check:
        source, species = args.check
        cached = load_cached_response(source, species)
        if cached:
            print(f"Found: {source} / {species}")
            # Print summary of payload keys
            if isinstance(cached, dict):
                print(f"  Keys: {list(cached.keys())}")
        else:
            print(f"Missing: {source} / {species}")
        return

    if args.clear:
        species = args.clear
        count = clear_cache_for_species(species)
        print(f"Cleared {count} files for {species}")
        return

    parser.print_help()

if __name__ == "__main__":
    main()
