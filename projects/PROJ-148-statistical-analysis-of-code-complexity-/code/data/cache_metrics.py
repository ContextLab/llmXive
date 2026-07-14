"""
Performance optimization: cache lizard metric results to avoid re-parsing unchanged files.

This module implements a file-content-based caching strategy for code complexity metrics.
It computes a SHA-256 hash of the source file content and stores the resulting metrics
in a JSON cache file. On subsequent runs, if the file hash matches, the cached metrics
are returned immediately without invoking the lizard parser.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import lizard

from utils.logging import get_logger
from utils.checksum import hash_file

logger = get_logger(__name__)

CACHE_VERSION = "1.0"
CACHE_FILENAME = "lizard_metrics_cache.json"


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file's content."""
    return hash_file(file_path)


def load_cache(cache_path: Path) -> Dict[str, Any]:
    """Load the existing cache from disk, or return an empty dict if not found."""
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Loaded cache with {len(data.get('files', {}))} entries from {cache_path}")
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache from {cache_path}: {e}. Starting fresh.")
            return {"version": CACHE_VERSION, "files": {}}
    else:
        logger.info(f"No existing cache found at {cache_path}. Initializing new cache.")
        return {"version": CACHE_VERSION, "files": {}}


def save_cache(cache_path: Path, cache_data: Dict[str, Any]) -> None:
    """Save the cache to disk."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2)
    logger.info(f"Saved cache with {len(cache_data.get('files', {}))} entries to {cache_path}")


def extract_metrics_for_file(
    file_path: Path,
    cache_data: Dict[str, Any],
    cache_enabled: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Extract metrics for a single file, using cache if available and enabled.

    Args:
        file_path: Path to the source file.
        cache_data: The cache dictionary to check/update.
        cache_enabled: Whether to use caching.

    Returns:
        A dictionary of metrics, or None if extraction failed.
    """
    file_hash = compute_file_hash(file_path)
    file_key = str(file_path)

    if cache_enabled and file_key in cache_data.get("files", {}):
        cached_entry = cache_data["files"][file_key]
        if cached_entry.get("hash") == file_hash:
            logger.debug(f"Cache hit for {file_path}. Returning cached metrics.")
            return cached_entry.get("metrics")
        else:
            logger.debug(f"Hash mismatch for {file_path}. Re-computing metrics.")
            # Remove stale entry
            del cache_data["files"][file_key]

    # Parse with lizard
    try:
        # lizard.analyze_file.analyze_source_code handles the parsing
        result = lizard.analyze_file.analyze_source_code(
            str(file_path),
            file_path.suffix
        )

        if not result or not result.function_list:
            logger.warning(f"No functions found in {file_path}. Skipping.")
            return None

        # Aggregate metrics from all functions in the file
        # We take the maximum/sum as appropriate for file-level metrics
        total_nesting = 0
        max_nesting = 0
        total_cc = 0
        max_cc = 0
        total_loc = 0
        total_tokens = 0
        total_halstead_volume = 0.0
        num_functions = 0

        for func in result.function_list:
            total_nesting += func.nesting_level
            max_nesting = max(max_nesting, func.nesting_level)
            total_cc += func.cyclomatic_complexity
            max_cc = max(max_cc, func.cyclomatic_complexity)
            total_loc += func.loc
            # lizard doesn't directly expose token count or Halstead volume in the standard result object
            # We will approximate or use available fields.
            # Note: lizard's standard output includes 'cyclomatic_complexity', 'loc', 'nloc', 'longest_token', etc.
            # Halstead volume is not standard in the simple result object, so we skip or approximate if needed.
            # For this implementation, we focus on the standard fields available.
            num_functions += 1

        # If lizard doesn't provide tokens/halstead directly in this context, we omit them or set to 0
        # to maintain compatibility with the expected schema.
        metrics = {
            "file_path": str(file_path),
            "num_functions": num_functions,
            "avg_cc": total_cc / num_functions if num_functions > 0 else 0,
            "max_cc": max_cc,
            "total_cc": total_cc,
            "avg_loc": total_loc / num_functions if num_functions > 0 else 0,
            "max_loc": max(total_loc, 0), # Max LOC per file is just the file's LOC roughly
            "total_loc": total_loc,
            "avg_nesting": total_nesting / num_functions if num_functions > 0 else 0,
            "max_nesting": max_nesting,
            "file_hash": file_hash,
            "metrics_source": "lizard"
        }

        # Update cache
        cache_data["files"][file_key] = {
            "hash": file_hash,
            "metrics": metrics
        }

        logger.debug(f"Computed and cached metrics for {file_path}.")
        return metrics

    except Exception as e:
        logger.error(f"Failed to parse {file_path} with lizard: {e}")
        return None


def cache_metrics_for_directory(
    source_dir: Path,
    cache_path: Path,
    extensions: List[str] = None,
    cache_enabled: bool = True
) -> pd.DataFrame:
    """
    Scan a directory for source files, compute metrics, and cache results.

    Args:
        source_dir: Root directory to scan.
        cache_path: Path to the JSON cache file.
        extensions: List of file extensions to include (e.g., ['.java']).
        cache_enabled: Whether to use caching.

    Returns:
        A DataFrame of all computed metrics.
    """
    if extensions is None:
        extensions = [".java"]

    cache_data = load_cache(cache_path)
    all_metrics = []
    processed = 0
    cached_count = 0

    for ext in extensions:
        for file_path in source_dir.rglob(f"*{ext}"):
            metrics = extract_metrics_for_file(file_path, cache_data, cache_enabled)
            if metrics:
                all_metrics.append(metrics)
                processed += 1
                if cache_enabled and file_path in cache_data["files"]:
                    # Check if it was a hit or miss by looking at the logic,
                    # but for simplicity, we just count successful extractions.
                    pass

    if cache_enabled:
        save_cache(cache_path, cache_data)

    logger.info(f"Processed {processed} files. Cache updated at {cache_path}.")
    return pd.DataFrame(all_metrics)


def main():
    """CLI entry point for caching metrics."""
    parser = argparse.ArgumentParser(
        description="Cache lizard metrics for source files to avoid re-parsing."
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        required=True,
        help="Directory containing source files to analyze."
    )
    parser.add_argument(
        "--cache-path",
        type=str,
        default="data/cache/lizard_metrics_cache.json",
        help="Path to the cache JSON file."
    )
    parser.add_argument(
        "--extensions",
        type=str,
        nargs="+",
        default=[".java"],
        help="File extensions to include (e.g., .java .py)."
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching (force re-parsing)."
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="data/processed/metrics_cache_output.csv",
        help="Path to save the resulting CSV of metrics."
    )

    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    if not source_dir.exists():
        logger.error(f"Source directory does not exist: {source_dir}")
        sys.exit(1)

    cache_path = Path(args.cache_path)
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    extensions = args.extensions
    cache_enabled = not args.no_cache

    df = cache_metrics_for_directory(
        source_dir=source_dir,
        cache_path=cache_path,
        extensions=extensions,
        cache_enabled=cache_enabled
    )

    if not df.empty:
        df.to_csv(output_csv, index=False)
        logger.info(f"Metrics saved to {output_csv}")
    else:
        logger.warning("No metrics were extracted. No CSV saved.")


if __name__ == "__main__":
    main()
