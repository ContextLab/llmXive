"""
Preprocessing module for CodeSearchNet data.

Loads raw data from T006 output, strips non-ASCII characters,
truncates to fixed token limits, and saves processed JSONL/CSV files.
"""
import os
import json
import csv
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator

# Import utility functions from the shared lib if they exist,
# otherwise define minimal versions here to ensure independence.
try:
    from src.lib.utils import set_seed, setup_logging
except ImportError:
    # Fallback if src/lib/utils.py is not yet fully implemented or importable
    def set_seed(seed: int = 42) -> None:
        import random
        import numpy as np
        random.seed(seed)
        np.random.seed(seed)

    def setup_logging(level: int = logging.INFO) -> logging.Logger:
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

# Constants
DEFAULT_TOKEN_LIMIT = 512
RAW_DATA_ROOT = Path("data/raw")
PROCESSED_DATA_ROOT = Path("data/processed")

logger = setup_logging()

def strip_non_ascii(text: str) -> str:
    """
    Remove non-ASCII characters from a string.
    Preserves standard whitespace (space, tab, newline).
    """
    if not isinstance(text, str):
        return ""
    # Keep printable ASCII (32-126) plus common whitespace
    return ''.join(char for char in text if ord(char) < 128 or char in '\n\r\t ')

def tokenize_and_truncate(text: str, max_tokens: int = DEFAULT_TOKEN_LIMIT) -> str:
    """
    Simple whitespace-based tokenization and truncation.
    Returns the text truncated to `max_tokens`.
    """
    if not text:
        return ""
    tokens = text.split()
    if len(tokens) <= max_tokens:
        return text
    return ' '.join(tokens[:max_tokens])

def process_snippet(snippet: Dict[str, Any], max_tokens: int = DEFAULT_TOKEN_LIMIT) -> Dict[str, Any]:
    """
    Process a single code snippet or query record.
    - Strips non-ASCII from 'code' and 'documentation' (if present).
    - Truncates 'code' and 'documentation' to max_tokens.
    - Preserves metadata (repo, path, etc.).
    """
    processed = snippet.copy()

    # Process code
    raw_code = snippet.get('code', '')
    if raw_code:
        clean_code = strip_non_ascii(raw_code)
        processed['code'] = tokenize_and_truncate(clean_code, max_tokens)
        processed['code_original_length'] = len(raw_code.split())
        processed['code_processed_length'] = len(processed['code'].split())
    else:
        processed['code'] = ""
        processed['code_original_length'] = 0
        processed['code_processed_length'] = 0

    # Process documentation (if exists)
    if 'documentation' in snippet and snippet['documentation']:
        raw_doc = snippet['documentation']
        clean_doc = strip_non_ascii(raw_doc)
        processed['documentation'] = tokenize_and_truncate(clean_doc, max_tokens)
        processed['doc_original_length'] = len(raw_doc.split())
        processed['doc_processed_length'] = len(processed['documentation'].split())
    else:
        processed['documentation'] = ""
        processed['doc_original_length'] = 0
        processed['doc_processed_length'] = 0

    return processed

def load_and_process_subset(
    split_name: str,
    raw_root: Path = RAW_DATA_ROOT,
    processed_root: Path = PROCESSED_DATA_ROOT,
    max_tokens: int = DEFAULT_TOKEN_LIMIT
) -> Iterator[Dict[str, Any]]:
    """
    Load raw JSONL data for a specific split, process it, and yield records.

    Args:
        split_name: 'train' or 'test'
        raw_root: Root directory containing raw data subdirectories
        processed_root: Root directory for processed output
        max_tokens: Maximum tokens per field

    Yields:
        Processed dictionaries.
    """
    raw_dir = raw_root / split_name
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    processed_dir = processed_root / split_name
    processed_dir.mkdir(parents=True, exist_ok=True)

    jsonl_files = list(raw_dir.glob("*.jsonl"))
    if not jsonl_files:
        # Fallback for potential different naming convention from T006
        jsonl_files = list(raw_dir.glob("*"))
        jsonl_files = [f for f in jsonl_files if f.is_file() and f.suffix in ['.jsonl', '.json']]

    if not jsonl_files:
        raise FileNotFoundError(f"No JSONL files found in {raw_dir}")

    logger.info(f"Processing split '{split_name}' from {raw_dir}")
    logger.info(f"Found {len(jsonl_files)} input files")

    total_processed = 0

    for jsonl_file in jsonl_files:
        logger.info(f"Processing file: {jsonl_file.name}")
        with open(jsonl_file, 'r', encoding='utf-8', errors='ignore') as f_in:
            for line_num, line in enumerate(f_in, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    processed_record = process_snippet(record, max_tokens)
                    processed_record['source_file'] = jsonl_file.name
                    processed_record['source_line'] = line_num
                    yield processed_record
                    total_processed += 1
                except json.JSONDecodeError:
                    logger.warning(f"Skipping invalid JSON at {jsonl_file}:{line_num}")
                    continue

    logger.info(f"Finished processing split '{split_name}'. Total records: {total_processed}")

def save_to_jsonl(
    records: Iterator[Dict[str, Any]],
    output_path: Path
) -> int:
    """
    Save processed records to a JSONL file.
    Returns the count of saved records.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            count += 1
    return count

def save_to_csv(
    records: Iterator[Dict[str, Any]],
    output_path: Path,
    fieldnames: Optional[List[str]] = None
) -> int:
    """
    Save processed records to a CSV file.
    Returns the count of saved records.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    first_batch = []
    for record in records:
        first_batch.append(record)
        if fieldnames is None and count == 0:
            fieldnames = list(record.keys())

    if not first_batch:
        logger.warning("No records to save in CSV.")
        return 0

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for record in first_batch:
            writer.writerow(record)
            count += 1
        # Continue with the rest if the iterator wasn't exhausted
        # Note: Since we consumed the iterator to get fieldnames and first batch,
        # we need to re-iterate or handle differently.
        # For simplicity in this streaming context, we'll assume the caller
        # handles the iterator or we re-generate if possible.
        # However, since 'records' is an iterator passed in, we can't re-consume it easily
        # unless we buffer. Given the task is to save, we will assume the iterator
        # is consumed once. To fix the logic for a single-pass stream:

    # Re-implementation for true single-pass streaming if we didn't know headers
    # But since we already consumed, let's just return the count of what we wrote.
    # Actually, the above logic is flawed for a single-pass stream if we want to write ALL.
    # Let's rewrite save_to_csv to be robust.
    return count

def save_to_csv_streaming(
    records: Iterator[Dict[str, Any]],
    output_path: Path,
    fieldnames: Optional[List[str]] = None
) -> int:
    """
    Save processed records to a CSV file in a single pass.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    first_record = None

    # We need to peek or buffer first to get headers if not provided
    # But for large datasets, buffering is bad.
    # Strategy: If fieldnames provided, write immediately.
    # If not, read first record to get headers, write it, then continue.

    for record in records:
        if count == 0 and fieldnames is None:
            fieldnames = list(record.keys())

        if count == 0:
            first_record = record

        if count == 0 and first_record is not None:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerow(first_record)
            count += 1
        else:
            with open(output_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writerow(record)
            count += 1

    return count

def main() -> None:
    """
    Main entry point for preprocessing.
    Processes both 'train' and 'test' splits.
    """
    set_seed(42)
    logger.info("Starting preprocessing pipeline...")

    splits = ['train', 'test']

    for split in splits:
        logger.info(f"--- Processing {split} split ---")
        try:
            # Load and process
            processed_records = load_and_process_subset(split)

            # Save to JSONL
            jsonl_path = PROCESSED_DATA_ROOT / split / f"{split}_processed.jsonl"
            count_jsonl = save_to_jsonl(processed_records, jsonl_path)
            logger.info(f"Saved {count_jsonl} records to {jsonl_path}")

            # Save to CSV (re-load logic would be needed if we want to avoid re-processing,
            # but for this task, we assume the iterator can be regenerated or we accept
            # the overhead of re-reading if we wanted to save both formats from one pass.
            # To keep it simple and robust: we will re-call the generator if we need CSV,
            # OR we can save both in one pass.
            # Let's re-generate for CSV to ensure data consistency and simplicity.
            # In a real production system, we'd use a tee or buffer.
            csv_path = PROCESSED_DATA_ROOT / split / f"{split}_processed.csv"
            # Re-generate for CSV
            processed_records_csv = load_and_process_subset(split)
            count_csv = save_to_csv_streaming(processed_records_csv, csv_path)
            logger.info(f"Saved {count_csv} records to {csv_path}")

        except FileNotFoundError as e:
            logger.error(f"Failed to process {split}: {e}")
            # Do not fail the whole script if one split is missing, just log
            continue
        except Exception as e:
            logger.error(f"Error processing {split}: {e}", exc_info=True)
            raise

    logger.info("Preprocessing pipeline completed.")

if __name__ == "__main__":
    main()
