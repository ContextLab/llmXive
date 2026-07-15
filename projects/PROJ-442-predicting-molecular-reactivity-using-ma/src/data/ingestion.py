"""
Data Ingestion Module for USPTO-MIT Reaction Dataset.

Implements download, parsing, and initial processing of the USPTO-MIT subset
from Zenodo. Handles streaming of large JSONL.GZ files to manage memory constraints.
"""
import csv
import gzip
import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Generator, List, Tuple

import requests
from tqdm import tqdm

# Import local project utilities
from src.utils.logging import setup_logger, get_logger
from src.utils.state_manager import register_artifact
from src.data.schemas import validate_reaction_record

# Constants
USPTO_ZENODO_URL = "https://zenodo.org/record/3969375/files/USPTO_MIT_subset.jsonl.gz"
# Note: The actual filename might vary. We attempt to fetch the record listing
# or rely on the direct file link if known. For this implementation, we assume
# the direct file link provided in tasks.md is valid or use the record root.
# If the direct link fails, we will attempt to find the file in the record.
# However, per instructions, we use the provided URL.

# Fallback to a known working structure if the direct file link is unstable,
# but strictly adhering to the task URL first.
# The Zenodo record 3969375 usually contains 'uspto_mit.jsonl.gz' or similar.
# We will implement a robust download that handles the specific URL provided.

# Output paths
OUTPUT_DIR = Path("data/processed")
RAW_OUTPUT_PATH = OUTPUT_DIR / "raw_reactions.jsonl"
ERROR_LOG_PATH = OUTPUT_DIR / "ingestion_errors.log"

# Initialize logger
logger = get_logger(__name__)

def compute_file_checksum(filepath: Path, algorithm: str = "sha256") -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def download_uspto_data(output_path: Path) -> Path:
    """
    Download the USPTO-MIT dataset from Zenodo.
    
    Args:
        output_path: Local path to save the downloaded file.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        RuntimeError: If download fails.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading USPTO-MIT dataset from {USPTO_ZENODO_URL}")
    
    try:
        # Stream the download to handle large files
        response = requests.get(USPTO_ZENODO_URL, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f, tqdm(
            desc="Downloading",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))
                    
        logger.info(f"Download complete: {output_path}")
        return output_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download data: {e}")
        raise RuntimeError(f"Download failed: {e}")

def stream_jsonl_gz(gz_path: Path) -> Generator[Dict[str, Any], None, None]:
    """
    Stream and parse a gzipped JSONL file line by line.
    
    Args:
        gz_path: Path to the .jsonl.gz file.
        
    Yields:
        Parsed JSON dictionaries.
    """
    if not gz_path.exists():
        raise FileNotFoundError(f"File not found: {gz_path}")
        
    logger.info(f"Streaming JSONL from {gz_path}")
    
    try:
        with gzip.open(gz_path, 'rt', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed JSON at line {line_num}: {e}")
                    continue
    except Exception as e:
        logger.error(f"Error reading compressed file: {e}")
        raise

def parse_jsonl_line(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse and validate a single reaction record from the raw JSON.
    
    Args:
        data: Raw dictionary from JSONL line.
        
    Returns:
        Normalized record or None if invalid.
    """
    # Basic schema validation
    required_fields = ['reactants', 'products', 'reagents']
    for field in required_fields:
        if field not in data:
            logger.debug(f"Missing field '{field}' in record")
            return None
            
    # Normalize SMILES strings (remove spaces, ensure valid format)
    # This is a placeholder for more complex normalization logic
    # that might be expanded in later tasks.
    normalized = data.copy()
    
    # Ensure smiles are strings
    if isinstance(normalized.get('reactants'), str):
        normalized['reactants'] = normalized['reactants'].replace(' ', '')
    if isinstance(normalized.get('products'), str):
        normalized['products'] = normalized['products'].replace(' ', '')
    if isinstance(normalized.get('reagents'), str):
        normalized['reagents'] = normalized['reagents'].replace(' ', '')
        
    return normalized

def process_chunk(
    records: List[Dict[str, Any]],
    error_log: Path,
    target_path: Path
) -> int:
    """
    Process a batch of records, validate, and write to raw output.
    
    Args:
        records: List of parsed reaction records.
        error_log: Path to log invalid records.
        target_path: Path to append valid records.
        
    Returns:
        Number of valid records processed.
    """
    valid_count = 0
    
    with open(target_path, 'a', encoding='utf-8') as out_f, \
         open(error_log, 'a', encoding='utf-8') as err_f:
         
        for rec in records:
            parsed = parse_jsonl_line(rec)
            if parsed:
                # Validate against schema
                # Note: validate_reaction_record expects a dict-like object
                # We pass the dict directly
                if validate_reaction_record(parsed):
                    out_f.write(json.dumps(parsed) + '\n')
                    valid_count += 1
                else:
                    err_f.write(f"Validation failed: {json.dumps(rec)}\n")
            else:
                err_f.write(f"Parse failed: {json.dumps(rec)}\n")
                
    return valid_count

def ingest_and_filter(
    raw_gz_path: Optional[Path] = None,
    force_download: bool = False
) -> Tuple[Path, int]:
    """
    Main orchestration function for data ingestion.
    
    Downloads the dataset if needed, streams it, parses, and saves
    valid records to data/processed/raw_reactions.jsonl.
    
    Args:
        raw_gz_path: Optional path to existing local .jsonl.gz file.
        force_download: If True, re-download even if file exists.
        
    Returns:
        Tuple of (output_path, total_valid_records)
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Determine source
    if raw_gz_path is None:
        raw_gz_path = OUTPUT_DIR / "USPTO_MIT_subset.jsonl.gz"
        
    # Download if missing or forced
    if not raw_gz_path.exists() or force_download:
        download_uspto_data(raw_gz_path)
        
    # Initialize output paths
    raw_output_path = OUTPUT_DIR / "raw_reactions.jsonl"
    error_log_path = OUTPUT_DIR / "ingestion_errors.log"
    
    # Reset output files
    if raw_output_path.exists():
        raw_output_path.unlink()
    if error_log_path.exists():
        error_log_path.unlink()
        
    logger.info("Starting ingestion pipeline...")
    start_time = time.time()
    
    total_valid = 0
    chunk_size = 1000
    current_chunk = []
    
    try:
        for record in stream_jsonl_gz(raw_gz_path):
            current_chunk.append(record)
            
            if len(current_chunk) >= chunk_size:
                count = process_chunk(current_chunk, error_log_path, raw_output_path)
                total_valid += count
                current_chunk = []
                
        # Process remaining
        if current_chunk:
            count = process_chunk(current_chunk, error_log_path, raw_output_path)
            total_valid += count
            
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise
        
    elapsed = time.time() - start_time
    logger.info(f"Ingestion complete. Processed {total_valid} valid records in {elapsed:.2f}s.")
    
    # Register artifact
    checksum = compute_file_checksum(raw_output_path)
    register_artifact(
        stage="ingestion",
        artifact_name="raw_reactions",
        path=str(raw_output_path),
        checksum=checksum
    )
    
    return raw_output_path, total_valid

def main():
    """Entry point for the ingestion script."""
    setup_logger()
    logger.info("Starting USPTO-MIT Data Ingestion (Task T012)")
    
    try:
        output_path, count = ingest_and_filter()
        logger.info(f"Successfully ingested {count} records to {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
