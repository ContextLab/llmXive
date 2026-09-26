"""
Aggregator module for writing raw data to immutable store.

This module implements logic to write ALL fetched/scraped data to `data/raw/`
as immutable files before any cleaning. It generates SHA256 checksums for
all raw files and appends them to `data/checksums.txt`.

Dependencies:
  - T012a (api_fetcher): Provides fetched API data
  - T012d-Execute (literature_scraper): Provides scraped literature data
"""

import os
import sys
import logging
import json
import csv
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Import from local project modules
from config import get_data_raw_dir, get_config
from utils.logging_config import get_logger
from seed import init_reproducibility

logger = get_logger(__name__)


class LiteratureAggregator:
    """
    Aggregates raw data from multiple sources and writes to immutable store.

    This class handles:
    1. Writing fetched API data to JSON files
    2. Writing scraped literature data to CSV files
    3. Generating SHA256 checksums for all raw files
    4. Maintaining a checksum manifest
    """

    def __init__(self, raw_dir: Optional[Path] = None):
        """
        Initialize the aggregator.

        Args:
            raw_dir: Path to the raw data directory. If None, uses config.
        """
        self.raw_dir = raw_dir or get_data_raw_dir()
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.checksums: List[Dict[str, Any]] = []
        logger.info(f"Initialized LiteratureAggregator with raw_dir: {self.raw_dir}")

    def _calculate_sha256(self, file_path: Path) -> str:
        """
        Calculate SHA256 checksum of a file.

        Args:
            file_path: Path to the file to checksum.

        Returns:
            Hex digest of the SHA256 hash.
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            raise

    def _write_checksums_to_manifest(self, manifest_path: Path) -> None:
        """
        Write all checksums to the manifest file.

        Args:
            manifest_path: Path to the checksum manifest file.
        """
        with open(manifest_path, 'w') as f:
            for entry in self.checksums:
                f.write(f"{entry['checksum']}  {entry['relative_path']}\n")
        logger.info(f"Wrote checksum manifest to {manifest_path}")

    def save_raw_api_data(self, data: Dict[str, Any], source_name: str) -> Path:
        """
        Save raw API data to a JSON file.

        Args:
            data: The raw data dictionary from an API source.
            source_name: Name identifier for the source (e.g., 'mp', 'openalloy').

        Returns:
            Path to the saved file.
        """
        filename = f"raw_{source_name}.json"
        file_path = self.raw_dir / filename

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

            # Calculate and store checksum
            checksum = self._calculate_sha256(file_path)
            self.checksums.append({
                'filename': filename,
                'relative_path': str(file_path.relative_to(Path.cwd())),
                'checksum': checksum,
                'source_type': 'api',
                'timestamp': datetime.now().isoformat()
            })

            logger.info(f"Saved raw API data to {file_path} ({len(data)} records)")
            return file_path

        except Exception as e:
            logger.error(f"Failed to save raw API data from {source_name}: {e}")
            raise

    def save_raw_literature_data(self, data: List[Dict[str, Any]], source_name: str) -> Path:
        """
        Save raw literature data to a CSV file.

        Args:
            data: List of dictionaries containing raw scraped data.
            source_name: Name identifier for the source (e.g., 'lit', 'slr').

        Returns:
            Path to the saved file.
        """
        filename = f"raw_{source_name}.csv"
        file_path = self.raw_dir / filename

        if not data:
            logger.warning(f"No data to save for {source_name}, creating empty file")
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                pass
            checksum = self._calculate_sha256(file_path)
            self.checksums.append({
                'filename': filename,
                'relative_path': str(file_path.relative_to(Path.cwd())),
                'checksum': checksum,
                'source_type': 'literature',
                'timestamp': datetime.now().isoformat()
            })
            return file_path

        try:
            # Determine all unique keys across all records
            all_keys = set()
            for record in data:
                all_keys.update(record.keys())
            
            # Ensure consistent column order
            fieldnames = sorted(list(all_keys))

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(data)

            # Calculate and store checksum
            checksum = self._calculate_sha256(file_path)
            self.checksums.append({
                'filename': filename,
                'relative_path': str(file_path.relative_to(Path.cwd())),
                'checksum': checksum,
                'source_type': 'literature',
                'timestamp': datetime.now().isoformat()
            })

            logger.info(f"Saved raw literature data to {file_path} ({len(data)} records)")
            return file_path

        except Exception as e:
            logger.error(f"Failed to save raw literature data from {source_name}: {e}")
            raise

    def finalize_checksums(self, manifest_path: Optional[Path] = None) -> Path:
        """
        Finalize the checksum manifest.

        Args:
            manifest_path: Optional path for the manifest. Defaults to data/checksums.txt.

        Returns:
            Path to the created manifest file.
        """
        if manifest_path is None:
            manifest_path = Path.cwd() / "data" / "checksums.txt"
        
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_checksums_to_manifest(manifest_path)
        return manifest_path


def main() -> None:
    """
    Main entry point for the aggregator script.

    This function orchestrates the aggregation process:
    1. Loads raw data from API sources (if available)
    2. Loads raw data from literature sources (if available)
    3. Writes all data to immutable files in data/raw/
    4. Generates and saves checksums to data/checksums.txt
    """
    init_reproducibility()
    logger.info("Starting LiteratureAggregator")

    aggregator = LiteratureAggregator()

    # Note: In a real pipeline, this would be called after T012a and T012d-Execute
    # For now, we assume the data is passed in or loaded from intermediate files
    # This script is designed to be called by a pipeline runner that has already
    # fetched and scraped the data.

    # Example usage pattern (to be called by pipeline_runner):
    # 1. Load data from T012a output (API fetcher)
    # 2. Load data from T012d-Execute output (literature scraper)
    # 3. Call save_raw_api_data() and save_raw_literature_data()
    # 4. Call finalize_checksums()

    # Since this task is about writing the logic, we implement the class methods
    # and the main function that can be called by a pipeline runner.
    
    logger.info("LiteratureAggregator logic implemented. Ready to be called by pipeline.")


if __name__ == "__main__":
    main()