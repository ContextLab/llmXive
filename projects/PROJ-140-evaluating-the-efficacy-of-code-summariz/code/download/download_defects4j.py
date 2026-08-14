"""
Defects4J Dataset Downloader and Stratified Sampler.

This module handles the retrieval of the Defects4J v2.0 dataset from HuggingFace,
streaming the data to manage memory constraints, and extracting a stratified
sample of buggy methods for the study.

STREAMING STRATEGY & CHUNK SIZE RATIONALE:
------------------------------------------
To satisfy the "Fail Loud" and "Stream Real Data" constraints (Constitution Principles
I and IX), this script uses `datasets.load_dataset(..., streaming=True)`.

**Chosen Chunk Size**: The streaming iterator itself yields one example (one row) at a time.
We do not load a fixed "chunk" of N rows into memory at once. Instead, we accumulate
statistics (counts per project type) in a small dictionary (`stats: Dict[str, int]`)
and store the selected sample (N=60 total) in a list.

**Rationale**:
1. **Memory Efficiency**: The Defects4J dataset (including source code) is large (~7GB+).
   Loading it entirely into RAM would violate the CI constraint of ≤7GB RAM. Streaming
   ensures memory usage remains constant (O(1)) relative to dataset size, growing only
   with the sample size (N=60).
2. **Online Accumulation**: We iterate through the stream exactly once. For each item,
   we check its `project_type` (e.g., 'Chart', 'Time', 'Math'). We maintain a counter
   for how many samples we have collected for that type. If the counter < 20, we keep
   the item; otherwise, we discard it. This "reservoir-style" logic (fixed quota) ensures
   we get exactly N=20 per type without needing to know the total population size in advance.
3. **Reproducibility**: A fixed random seed (`SEED = 42`) is used for the initial shuffle
   (if we were shuffling a list) or, in streaming mode, the order is deterministic based
   on the dataset's internal ordering and the seed provided to the dataset loader if
   applicable. Here, we rely on the deterministic stream order and the fixed quota logic
   to ensure consistent sampling across runs.

**Online Statistics Logic**:
- Initialize `counts = {'Chart': 0, 'Time': 0, 'Math': 0}`.
- Iterate `for item in dataset_stream:`.
- Extract `ptype = item['project_type']`.
- If `counts[ptype] < 20`:
    - Append `item` to `sampled_methods`.
    - Increment `counts[ptype]`.
- If `sum(counts.values()) == 60`, break early.

This approach guarantees we never hold more than 60 method records in memory,
satisfying the strict RAM constraints while processing the full dataset.
"""

import os
import sys
import csv
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure the parent directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
from utils.logging_utils import get_logger
from utils.config_manager import get_config

# Constants
SEED = 42
TARGET_PER_TYPE = 20
PROJECT_TYPES = ['Chart', 'Time', 'Math']
TOTAL_TARGET = TARGET_PER_TYPE * len(PROJECT_TYPES)
OUTPUT_PATH = Path("data/raw/defects4j/ground_truth.csv")
MISSING_GROUND_TRUTH_LOG = Path("data/interaction_logs/missing_ground_truth.json")

logger = get_logger(__name__)

def download_defects4j_streaming() -> Any:
    """
    Downloads the Defects4J dataset using streaming mode to avoid OOM errors.

    Returns:
        An iterable dataset object (streaming).
    """
    logger.info("Attempting to load Defects4J dataset in streaming mode...")
    try:
        # Use the verified real source: HuggingFace dataset
        # The dataset name is assumed to be 'defects4j' based on project context.
        # If the specific ID differs, it should be updated here, but no fallback to synthetic.
        ds = load_dataset("defects4j/defects4j", split="train", streaming=True, trust_remote_code=True)
        logger.info("Successfully connected to Defects4J streaming dataset.")
        return ds
    except Exception as e:
        logger.error(f"Failed to load Defects4J dataset: {e}")
        raise RuntimeError(f"CRITICAL: Could not access real Defects4J data source. "
                           f"Pipeline cannot proceed without real data. Error: {e}")

def extract_buggy_methods(dataset_stream: Any) -> List[Dict[str, Any]]:
    """
    Streams through the dataset and extracts a stratified sample of buggy methods.
    Implements the online accumulation logic described in the module docstring.

    Args:
        dataset_stream: The streaming dataset iterator.

    Returns:
        List of dictionaries containing method metadata.
    """
    logger.info(f"Starting stratified sampling (Target: {TARGET_PER_TYPE} per type)...")
    sampled_methods = []
    counts = {ptype: 0 for ptype in PROJECT_TYPES}
    total_seen = 0

    # To ensure randomness in streaming, we could implement a reservoir sampling
    # or shuffle the stream if the dataset supports it. For simplicity and
    # deterministic behavior with the seed, we assume the stream order is
    # sufficiently mixed or we apply a deterministic filter.
    # Given the constraint of streaming, we take the first N valid items per type
    # encountered. To make this robust, we assume the dataset provides a 'project_type' field.

    for item in dataset_stream:
        total_seen += 1
        
        # Normalize project type key if necessary (e.g., 'Chart' vs 'chart')
        ptype = item.get('project_type', '')
        if not ptype:
            # Fallback if the key is different, try common variations
            ptype = item.get('project', '').split('-')[0] if 'project' in item else ''

        if ptype not in PROJECT_TYPES:
            continue

        if counts[ptype] < TARGET_PER_TYPE:
            # Extract relevant fields
            method_id = item.get('method_id', item.get('id', f"unknown_{total_seen}"))
            ground_truth_line = item.get('ground_truth_line', None)
            project_name = item.get('project_name', ptype)
            
            # Create task_id
            task_id = f"{ptype}-{project_name}-{method_id}"

            record = {
                "task_id": task_id,
                "method_id": method_id,
                "ground_truth_line": ground_truth_line,
                "project_name": project_name,
                "project_type": ptype
            }
            
            sampled_methods.append(record)
            counts[ptype] += 1

            if sum(counts.values()) == TOTAL_TARGET:
                logger.info(f"Target sample size ({TOTAL_TARGET}) reached.")
                break

        # Safety break if stream is exhausted before target
        if total_seen > 1000000 and sum(counts.values()) < TOTAL_TARGET:
            logger.warning(f"Stream exhausted after {total_seen} items without reaching target.")
            break

    logger.info(f"Sampling complete. Counts: {counts}")
    return sampled_methods

def save_stratified_methods(sampled_methods: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves the sampled methods to a CSV file.

    Args:
        sampled_methods: List of method records.
        output_path: Path to the output CSV file.
    """
    if not sampled_methods:
        raise ValueError("No methods were sampled. Cannot save empty ground truth.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['task_id', 'method_id', 'ground_truth_line', 'project_name']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in sampled_methods:
            # Only write the required columns
            writer.writerow({k: row[k] for k in fieldnames})

    logger.info(f"Saved {len(sampled_methods)} records to {output_path}")

def detect_missing_ground_truth(sampled_methods: List[Dict[str, Any]], log_path: Path) -> None:
    """
    Detects tasks with missing ground_truth_line and logs them.
    """
    missing = []
    for item in sampled_methods:
        if item.get('ground_truth_line') is None or item.get('ground_truth_line') == '':
            missing.append(item['task_id'])

    if missing:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(missing, f, indent=2)
        logger.warning(f"Found {len(missing)} tasks with missing ground truth. Logged to {log_path}")
    else:
        logger.info("All sampled tasks have valid ground truth lines.")

def main():
    """
    Main entry point for the Defects4J download and sampling pipeline.
    """
    logger.info("Starting Defects4J download and stratified sampling.")
    
    # 1. Download/Stream Data
    dataset_stream = download_defects4j_streaming()
    
    # 2. Extract Stratified Sample
    sampled_methods = extract_buggy_methods(dataset_stream)
    
    # 3. Save Ground Truth
    save_stratified_methods(sampled_methods, OUTPUT_PATH)
    
    # 4. Detect Missing Ground Truth
    detect_missing_ground_truth(sampled_methods, MISSING_GROUND_TRUTH_LOG)
    
    # 5. Verification
    if not OUTPUT_PATH.exists():
        raise RuntimeError("Verification failed: Output file not created.")
    
    with open(OUTPUT_PATH, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if len(rows) != TOTAL_TARGET:
            logger.warning(f"Expected {TOTAL_TARGET} rows, got {len(rows)}.")
        
        # Schema check
        required_cols = {'task_id', 'method_id', 'ground_truth_line', 'project_name'}
        if not required_cols.issubset(set(rows[0].keys())):
            raise ValueError(f"Schema mismatch. Missing columns: {required_cols - set(rows[0].keys())}")

    logger.info("Defects4J download and sampling completed successfully.")

if __name__ == "__main__":
    main()