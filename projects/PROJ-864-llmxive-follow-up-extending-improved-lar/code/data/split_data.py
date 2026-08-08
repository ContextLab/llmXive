"""
Split the processed micro-corpus into non-overlapping train and test sets.

This script reads the tokenized corpus from data/processed/micro_corpus.jsonl,
performs a deterministic stratified split (80/20) based on source, and writes
the resulting splits to data/processed/train_split.jsonl and 
data/processed/test_split.jsonl.

Output files are written to disk upon successful execution.
"""
import json
import os
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_processed_dir, get_config, ConfigError
from utils.logging import get_logger, info, error, warning

logger = get_logger(__name__)

# Constants
TRAIN_RATIO = 0.8
SEED = 42
INPUT_FILE = "micro_corpus.jsonl"
TRAIN_OUTPUT = "train_split.jsonl"
TEST_OUTPUT = "test_split.jsonl"

def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load a JSONL file into a list of dictionaries.
    
    Args:
        file_path: Path to the JSONL file.
        
    Returns:
        List of records.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                error(f"Failed to parse JSON at line {line_num}: {e}")
                raise
    
    if not records:
        raise ValueError(f"Input file {file_path} is empty or contains no valid JSON lines.")
        
    return records

def save_jsonl(records: List[Dict[str, Any]], file_path: Path) -> None:
    """
    Save a list of dictionaries to a JSONL file.
    
    Args:
        records: List of records to save.
        file_path: Path to the output file.
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    info(f"Saved {len(records)} records to {file_path}")

def split_data(records: List[Dict[str, Any]], train_ratio: float = TRAIN_RATIO, seed: int = SEED) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split records into train and test sets.
    
    This implementation groups records by 'source' (or a similar identifier if present)
    to ensure no overlap between train and test sets for the same source document.
    If no source identifier is present, it falls back to a random split.
    
    Args:
        records: List of corpus records.
        train_ratio: Fraction of data to use for training.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_records, test_records).
    """
    random.seed(seed)
    
    # Attempt to group by source to prevent leakage
    # We look for common keys that might indicate source grouping
    source_key = None
    if records:
        sample_keys = set(records[0].keys())
        for key in ['source', 'source_id', 'document_id', 'id']:
            if key in sample_keys:
                source_key = key
                break
    
    train_records = []
    test_records = []
    
    if source_key:
        # Group by source
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for record in records:
            if source_key in record:
                src = record[source_key]
                if src not in groups:
                    groups[src] = []
                groups[src].append(record)
            else:
                # Records without a source key go into a 'misc' bucket
                if '__misc__' not in groups:
                    groups['__misc__'] = []
                groups['__misc__'].append(record)
        
        # Shuffle the group keys
        group_keys = list(groups.keys())
        random.shuffle(group_keys)
        
        # Calculate how many groups go to train
        total_groups = len(group_keys)
        train_groups_count = int(total_groups * train_ratio)
        
        train_group_keys = group_keys[:train_groups_count]
        test_group_keys = group_keys[train_groups_count:]
        
        for key in train_group_keys:
            train_records.extend(groups[key])
        
        for key in test_group_keys:
            test_records.extend(groups[key])
        
        info(f"Split by source '{source_key}': {len(train_group_keys)} sources to train, {len(test_group_keys)} to test")
    else:
        # Fallback: Random split
        shuffled = records.copy()
        random.shuffle(shuffled)
        split_idx = int(len(shuffled) * train_ratio)
        train_records = shuffled[:split_idx]
        test_records = shuffled[split_idx:]
        info("No source key found; performed random split.")
    
    return train_records, test_records

def main():
    """
    Main entry point for the split_data script.
    
    Reads data/processed/micro_corpus.jsonl, splits it, and writes
    train and test splits to data/processed/.
    """
    try:
        # Get paths
        processed_dir = get_processed_dir()
        input_path = processed_dir / INPUT_FILE
        train_path = processed_dir / TRAIN_OUTPUT
        test_path = processed_dir / TEST_OUTPUT
        
        info(f"Starting data split process.")
        info(f"Input: {input_path}")
        info(f"Train Output: {train_path}")
        info(f"Test Output: {test_path}")
        
        # Load data
        info(f"Loading {input_path}...")
        records = load_jsonl(input_path)
        info(f"Loaded {len(records)} records.")
        
        # Split data
        info("Splitting data...")
        train_records, test_records = split_data(records)
        
        # Verify non-overlap (simple check based on IDs if available)
        train_ids = set()
        test_ids = set()
        for r in train_records:
            if 'id' in r: train_ids.add(r['id'])
        for r in test_records:
            if 'id' in r: test_ids.add(r['id'])
        
        overlap = train_ids.intersection(test_ids)
        if overlap:
            error(f"ERROR: Found {len(overlap)} overlapping IDs between train and test sets!")
            sys.exit(1)
        else:
            info("Verification passed: No overlapping IDs found between train and test sets.")
        
        # Save outputs
        info(f"Saving train split ({len(train_records)} records)...")
        save_jsonl(train_records, train_path)
        
        info(f"Saving test split ({len(test_records)} records)...")
        save_jsonl(test_records, test_path)
        
        info("Data split completed successfully.")
        
        # Print summary
        total = len(train_records) + len(test_records)
        train_pct = (len(train_records) / total) * 100
        test_pct = (len(test_records) / total) * 100
        info(f"Summary: Train={len(train_records)} ({train_pct:.2f}%), Test={len(test_records)} ({test_pct:.2f}%)")
        
    except FileNotFoundError as e:
        error(f"Data file not found: {e}")
        error("Ensure that T013 (tokenize_and_filter.py) has run successfully to generate micro_corpus.jsonl.")
        sys.exit(1)
    except ConfigError as e:
        error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        error(f"Unexpected error during split: {e}")
        raise

if __name__ == "__main__":
    main()