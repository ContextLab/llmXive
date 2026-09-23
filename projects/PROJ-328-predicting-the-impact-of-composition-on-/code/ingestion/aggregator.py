"""
Aggregator module for T012g: Write Raw Data to Immutable Store.

This module implements the logic to write ALL fetched/scraped data 
to data/raw/ as immutable files and generate SHA256 checksums.
"""
import os
import sys
import logging
import json
import csv
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Import config to get data directories
try:
    from config import get_data_raw_dir, get_data_processed_dir
except ImportError:
    # Fallback for direct execution context if config is not in path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_data_raw_dir, get_data_processed_dir

logger = logging.getLogger(__name__)

class LiteratureAggregator:
    """
    Aggregates data from various sources (API, literature scraping) 
    and writes them to the immutable raw data store.
    """
    
    def __init__(self):
        self.raw_dir = get_data_raw_dir()
        self.checksum_file = Path("data/checksums.txt")
        self.sources_data: Dict[str, List[Dict[str, Any]]] = {}
        
        # Ensure raw directory exists
        if not self.raw_dir.exists():
            self.raw_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created raw data directory: {self.raw_dir}")

    def add_source_data(self, source_name: str, data: List[Dict[str, Any]]) -> None:
        """
        Add data from a specific source to the internal buffer.
        
        Args:
            source_name: Name identifier for the source (e.g., 'mp', 'lit')
            data: List of records from the source
        """
        if source_name in self.sources_data:
            logger.warning(f"Overwriting existing data for source: {source_name}")
        self.sources_data[source_name] = data
        logger.info(f"Added {len(data)} records from source: {source_name}")

    def _calculate_sha256(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hexadecimal string of the SHA256 hash
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            raise

    def _save_json(self, source_name: str, data: List[Dict[str, Any]]) -> Path:
        """
        Save data to a JSON file in the raw directory.
        
        Args:
            source_name: Name identifier for the source
            data: List of records
            
        Returns:
            Path to the saved file
        """
        filename = f"raw_{source_name}.json"
        file_path = self.raw_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved JSON data to: {file_path}")
        return file_path

    def _save_csv(self, source_name: str, data: List[Dict[str, Any]]) -> Path:
        """
        Save data to a CSV file in the raw directory.
        
        Args:
            source_name: Name identifier for the source
            data: List of records
            
        Returns:
            Path to the saved file
        """
        if not data:
            logger.warning(f"No data to save for source: {source_name}")
            return None
        
        filename = f"raw_{source_name}.csv"
        file_path = self.raw_dir / filename
        
        # Determine headers from the first record
        headers = list(data[0].keys())
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Saved CSV data to: {file_path}")
        return file_path

    def _append_checksum(self, file_path: Path, checksum: str) -> None:
        """
        Append a checksum entry to the checksums file.
        
        Args:
            file_path: Path to the data file
            checksum: SHA256 checksum string
        """
        timestamp = datetime.now().isoformat()
        entry = f"{timestamp} | {file_path.name} | {checksum}\n"
        
        # Ensure checksum file directory exists
        checksum_file_dir = self.checksum_file.parent
        if not checksum_file_dir.exists():
            checksum_file_dir.mkdir(parents=True, exist_ok=True)
            
        # Append to file
        with open(self.checksum_file, 'a', encoding='utf-8') as f:
            f.write(entry)
            
        logger.info(f"Appended checksum for {file_path.name} to {self.checksum_file}")

    def aggregate(self) -> Dict[str, Path]:
        """
        Main aggregation method: saves all buffered data and generates checksums.
        
        Returns:
            Dictionary mapping source names to their saved file paths
        """
        if not self.sources_data:
            logger.warning("No data sources provided. Nothing to aggregate.")
            return {}

        saved_files = {}
        
        for source_name, data in self.sources_data.items():
            if not data:
                logger.warning(f"Skipping empty data for source: {source_name}")
                continue
              
            # Determine file extension based on source name or data structure
            # For simplicity, we'll use JSON for all unless it's explicitly a literature CSV
            if 'lit' in source_name or 'slr' in source_name:
                file_path = self._save_csv(source_name, data)
            else:
                file_path = self._save_json(source_name, data)
            
            if file_path:
                checksum = self._calculate_sha256(file_path)
                self._append_checksum(file_path, checksum)
                saved_files[source_name] = file_path
                logger.info(f"Aggregated and checksummed source: {source_name}")
            
        logger.info(f"Aggregation complete. Saved {len(saved_files)} files.")
        return saved_files

def main():
    """
    Main entry point for the aggregator script.
    
    This script is intended to be run after T012a (API Fetcher) and 
    T012d-Execute (Literature Scraper) have populated the data.
    It loads the raw data from the respective fetchers/scrapers 
    (or assumes they have already saved intermediate files) and 
    writes them to the immutable store with checksums.
    
    NOTE: In a real pipeline, the data from T012a and T012d-Execute 
    would be passed to this aggregator. For this implementation, 
    we simulate the ingestion of data that would have been fetched 
    by those tasks.
    
    IMPORTANT: This implementation assumes that the data fetchers 
    (T012a, T012d-Execute) have either:
    1. Returned the data directly to this aggregator, OR
    2. Saved temporary files that this aggregator reads.
    
    Since T012a and T012d-Execute are separate tasks, this aggregator
    will attempt to load data from the expected output locations of 
    those tasks if they exist, or use placeholder data if they don't.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    aggregator = LiteratureAggregator()
    
    # Attempt to load data from T012a (API Fetcher) output
    # Assuming T012a saves to data/raw/raw_mp.json and data/raw/raw_openalloy.json
    mp_file = Path("data/raw/raw_mp.json")
    if mp_file.exists():
        with open(mp_file, 'r', encoding='utf-8') as f:
            mp_data = json.load(f)
        aggregator.add_source_data('mp', mp_data)
    else:
        logger.warning(f"API Fetcher output not found at {mp_file}. Skipping MP data.")
        
    openalloy_file = Path("data/raw/raw_openalloy.json")
    if openalloy_file.exists():
        with open(openalloy_file, 'r', encoding='utf-8') as f:
            openalloy_data = json.load(f)
        aggregator.add_source_data('openalloy', openalloy_data)
    else:
        logger.warning(f"API Fetcher output not found at {openalloy_file}. Skipping OpenAlloy data.")
        
    # Attempt to load data from T012d-Execute (Literature Scraper) output
    # Assuming T012d-Execute saves to data/raw/raw_lit.csv and data/raw/raw_slr.csv
    lit_file = Path("data/raw/raw_lit.csv")
    if lit_file.exists():
        with open(lit_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            lit_data = list(reader)
        aggregator.add_source_data('lit', lit_data)
    else:
        logger.warning(f"Literature Scraper output not found at {lit_file}. Skipping lit data.")
        
    slr_file = Path("data/raw/raw_slr.csv")
    if slr_file.exists():
        with open(slr_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            slr_data = list(reader)
        aggregator.add_source_data('slr', slr_data)
    else:
        logger.warning(f"Systematic Literature Review output not found at {slr_file}. Skipping slr data.")
        
    # If no data was found, log a warning but proceed (pipeline should handle empty state)
    if not aggregator.sources_data:
        logger.warning("No data sources found. Creating empty checksum file.")
        # Ensure checksum file exists even if empty
        if not aggregator.checksum_file.exists():
            aggregator.checksum_file.touch()
        return
    
    # Perform aggregation
    saved_files = aggregator.aggregate()
    
    if saved_files:
        logger.info(f"Successfully aggregated {len(saved_files)} sources:")
        for name, path in saved_files.items():
            logger.info(f"  - {name}: {path}")
    else:
        logger.warning("Aggregation completed but no files were saved.")

if __name__ == "__main__":
    main()