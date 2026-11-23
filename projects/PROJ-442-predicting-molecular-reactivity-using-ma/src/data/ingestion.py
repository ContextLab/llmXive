"""
Data Ingestion Module for USPTO-MIT Reaction Dataset.

This module handles downloading, parsing, and filtering the USPTO-MIT subset
of reaction data from Zenodo. It classifies reactions into SN1, SN2, and
Diels-Alder categories based on SMARTS patterns.
"""

import csv
import gzip
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import requests
from tqdm import tqdm

# Local imports
from src.modeling.config import load_config
from src.utils.chemistry import classify_batch, get_templates
from src.utils.logging import get_logger, setup_logger
from src.utils.state_manager import register_artifact, update_stage_status

# Setup logger for this module
logger = get_logger(__name__)

def download_uspto_data(output_dir: str, url: str, filename: str) -> str:
    """
    Download the USPTO-MIT dataset from Zenodo.

    Args:
        output_dir: Directory to save the downloaded file.
        url: URL to download the file from.
        filename: Name of the file to save.

    Returns:
        Path to the downloaded file.

    Raises:
        RuntimeError: If download fails or file is not found.
    """
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)

    if os.path.exists(file_path):
        logger.info(f"File already exists at {file_path}, skipping download.")
        return file_path

    logger.info(f"Downloading USPTO-MIT dataset from {url}...")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte

        with open(file_path, 'wb') as f, tqdm(
            desc=filename,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

        logger.info(f"Download complete: {file_path}")
        return file_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download dataset: {e}")
        raise RuntimeError(f"Download failed: {e}")

def stream_jsonl_gz(file_path: str) -> Generator[Dict[str, Any], None, None]:
    """
    Stream and parse a gzipped JSONL file line by line.

    Args:
        file_path: Path to the gzipped JSONL file.

    Yields:
        Parsed JSON dictionaries.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Streaming {file_path}...")
    try:
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
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
        logger.error(f"Error reading {file_path}: {e}")
        raise

def parse_jsonl_line(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse a single JSON record from the USPTO dataset.

    Extracts relevant fields and validates basic structure.

    Args:
        record: Raw JSON record from the dataset.

    Returns:
        Parsed record with extracted fields, or None if invalid.
    """
    try:
        # Expected fields based on USPTO-MIT dataset structure
        required_fields = ['reaction_smiles', 'reagents']
        for field in required_fields:
            if field not in record:
                logger.debug(f"Missing required field '{field}' in record")
                return None

        # Extract yield or success flag if available
        yield_val = record.get('yield_pct')
        success_val = record.get('success_flag')

        parsed = {
            'reaction_smiles': record['reaction_smiles'],
            'reagents': record.get('reagents', ''),
            'yield_pct': float(yield_val) if yield_val is not None else None,
            'success_flag': int(success_val) if success_val is not None else None,
            'raw_record': record,
            'source_line': json.dumps(record)
        }

        return parsed
    except (ValueError, TypeError, KeyError) as e:
        logger.debug(f"Failed to parse record: {e}")
        return None

def process_chunk(
    records: List[Dict[str, Any]],
    templates: Dict[str, str]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Process a chunk of records by classifying reactions.

    Args:
        records: List of parsed records.
        templates: SMARTS patterns for classification.

    Returns:
        Tuple of (classified_records, error_records).
    """
    if not records:
        return [], []

    # Extract SMILES for batch classification
    smiles_list = [r['reaction_smiles'] for r in records]

    # Classify reactions using chemistry module
    classifications = classify_batch(smiles_list, templates)

    classified = []
    errors = []

    for i, record in enumerate(records):
        reaction_type = classifications[i]
        if reaction_type:
            record['reaction_type'] = reaction_type
            classified.append(record)
        else:
            record['error_reason'] = 'No matching template'
            errors.append(record)

    return classified, errors

def filter_by_class_sample_size(
    df: List[Dict[str, Any]],
    min_samples: int = 1000
) -> List[Dict[str, Any]]:
    """
    Filter out reaction classes with fewer than min_samples.

    Args:
        df: List of classified records.
        min_samples: Minimum number of samples required per class.

    Returns:
        Filtered list of records.
    """
    from collections import Counter
    class_counts = Counter(r['reaction_type'] for r in df if 'reaction_type' in r)

    valid_classes = {cls for cls, count in class_counts.items() if count >= min_samples}

    if len(valid_classes) < len(class_counts):
        removed_classes = set(class_counts.keys()) - valid_classes
        logger.warning(f"Removing classes with < {min_samples} samples: {removed_classes}")

    return [r for r in df if r.get('reaction_type') in valid_classes]

def ingest_and_filter(
    input_file: str,
    output_file: str,
    error_file: str,
    templates: Dict[str, str],
    min_samples: int = 1000,
    chunk_size: int = 10000
) -> Dict[str, Any]:
    """
    Main ingestion pipeline: download, parse, classify, filter, and save.

    Args:
        input_file: Path to input JSONL.GZ file.
        output_file: Path to output CSV file.
        error_file: Path to error log file.
        templates: SMARTS patterns for classification.
        min_samples: Minimum samples per class.
        chunk_size: Number of records to process at once.

    Returns:
        Dictionary with ingestion statistics.
    """
    stats = {
        'total_records': 0,
        'parsed_records': 0,
        'classified_records': 0,
        'filtered_records': 0,
        'error_records': 0,
        'classes': {},
        'start_time': datetime.now().isoformat(),
        'end_time': None
    }

    all_classified = []
    all_errors = []

    # Stream and process in chunks
    chunk = []
    for record in stream_jsonl_gz(input_file):
        stats['total_records'] += 1
        parsed = parse_jsonl_line(record)
        if parsed:
            stats['parsed_records'] += 1
            chunk.append(parsed)

        if len(chunk) >= chunk_size:
            classified, errors = process_chunk(chunk, templates)
            all_classified.extend(classified)
            all_errors.extend(errors)
            chunk = []

    # Process remaining chunk
    if chunk:
        classified, errors = process_chunk(chunk, templates)
        all_classified.extend(classified)
        all_errors.extend(errors)

    stats['classified_records'] = len(all_classified)
    stats['error_records'] = len(all_errors)

    # Apply sample size filter
    filtered_data = filter_by_class_sample_size(all_classified, min_samples)
    stats['filtered_records'] = len(filtered_data)

    # Calculate class distribution
    from collections import Counter
    class_counts = Counter(r['reaction_type'] for r in filtered_data)
    stats['classes'] = dict(class_counts)

    # Write output CSV
    if filtered_data:
        fieldnames = ['reaction_smiles', 'reaction_type', 'yield_pct', 'success_flag']
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in filtered_data:
                writer.writerow({
                    'reaction_smiles': record['reaction_smiles'],
                    'reaction_type': record['reaction_type'],
                    'yield_pct': record['yield_pct'],
                    'success_flag': record['success_flag']
                })
        logger.info(f"Wrote {len(filtered_data)} records to {output_file}")

    # Write error log
    if all_errors:
        with open(error_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['reaction_smiles', 'error_reason'])
            writer.writeheader()
            for record in all_errors:
                writer.writerow({
                    'reaction_smiles': record['reaction_smiles'],
                    'error_reason': record.get('error_reason', 'Unknown')
                })
        logger.info(f"Wrote {len(all_errors)} error records to {error_file}")

    stats['end_time'] = datetime.now().isoformat()
    return stats

def main():
    """
    Main entry point for the ingestion script.
    """
    # Load configuration
    config = load_config()

    # Setup paths
    raw_dir = config['data']['raw_dir']
    processed_dir = config['data']['processed_dir']
    output_filename = config['data']['output_filename']
    input_filename = config['data']['input_filename']
    url = config['data']['uspto_url']

    input_path = os.path.join(raw_dir, input_filename)
    output_path = os.path.join(processed_dir, output_filename)
    error_path = os.path.join(processed_dir, 'ingestion_errors.csv')

    # Ensure directories exist
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    # Download data
    logger.info("Starting USPTO-MIT data ingestion pipeline...")
    try:
        downloaded_file = download_uspto_data(raw_dir, url, input_filename)
    except RuntimeError as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

    # Load templates
    templates = get_templates()

    # Run ingestion
    try:
        stats = ingest_and_filter(
            input_file=downloaded_file,
            output_file=output_path,
            error_file=error_path,
            templates=templates,
            min_samples=config['model']['min_samples_per_class'],
            chunk_size=config['model'].get('chunk_size', 10000)
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

    # Log results
    logger.info(f"Ingestion complete. Statistics: {stats}")

    # Update state
    try:
        update_stage_status('T012', 'completed', stats)
        register_artifact('data/processed/filtered_reactions.csv', output_path)
        register_artifact('data/processed/ingestion_errors.csv', error_path)
    except Exception as e:
        logger.warning(f"Failed to update state: {e}")

    return 0

if __name__ == '__main__':
    setup_logger()
    sys.exit(main())
