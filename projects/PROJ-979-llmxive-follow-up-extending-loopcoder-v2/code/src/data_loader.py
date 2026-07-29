"""
Data loading and preprocessing utilities.

This module handles:
- Fetching datasets from HuggingFace
- Computing checksums
- Stratified sampling
- Filtering underpowered strata
"""

import hashlib
import json
import os
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from datasets import load_dataset
import yaml

# Configure logging
import logging
logger = logging.getLogger(__name__)

CONFIG_PATH = "code/config.yaml"
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not os.path.exists(CONFIG_PATH):
        logger.warning(f"Config file not found: {CONFIG_PATH}, using defaults")
        return {
            "strata_threshold": 50,
            "non_inferiority_delta": 0.05,
            "entropy_n_samples": 10,
            "convergence_k_range": [1, 2, 3]
        }
    
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [RAW_DATA_DIR, PROCESSED_DATA_DIR, "data/raw", "data/processed"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_datasets() -> Tuple[Any, Any]:
    """
    Fetch HumanEval and MBPP datasets from HuggingFace.
    
    Returns:
        Tuple of (humaneval_dataset, mbpp_dataset)
    """
    ensure_directories()
    
    logger.info("Fetching HumanEval dataset...")
    humaneval = load_dataset("openai_humaneval", trust_remote_code=True)
    
    logger.info("Fetching MBPP dataset...")
    mbpp = load_dataset("mbpp", trust_remote_code=True)
    
    # Save raw copies
    humaneeval_path = os.path.join(RAW_DATA_DIR, "humaneval.json")
    mbpp_path = os.path.join(RAW_DATA_DIR, "mbpp.json")
    
    with open(humaneval_path, 'w') as f:
        json.dump(humaneval['test'].to_list(), f)
    
    with open(mbpp_path, 'w') as f:
        json.dump(mbpp['train'].to_list(), f)
    
    logger.info(f"Datasets saved to {RAW_DATA_DIR}")
    return humaneval, mbpp

def checksum_datasets() -> str:
    """
    Compute SHA256 checksums for all files in data/raw/.
    
    Returns:
        Path to checksums file
    """
    checksums = []
    
    for root, _, files in os.walk(RAW_DATA_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            checksum = compute_sha256(file_path)
            rel_path = os.path.relpath(file_path, RAW_DATA_DIR)
            checksums.append(f"{checksum}  {rel_path}")
    
    checksum_path = os.path.join(PROCESSED_DATA_DIR, "checksums.txt")
    with open(checksum_path, 'w') as f:
        f.write('\n'.join(checksums))
    
    logger.info(f"Checksums saved to {checksum_path}")
    return checksum_path

def determine_strata(task: Dict[str, Any]) -> str:
    """
    Determine stratum for a task based on difficulty or task_id hash.
    
    Args:
        task: Task dictionary
        
    Returns:
        Stratum name
    """
    if 'difficulty' in task:
        return task['difficulty']
    elif 'task_id' in task:
        # Hash-based stratum if difficulty not available
        task_id = task['task_id']
        hash_val = int(hashlib.md5(task_id.encode()).hexdigest(), 16)
        return f"stratum_{hash_val % 5}"
    else:
        return "unknown"

def stratified_sample(
    data: List[Dict[str, Any]],
    strata_key: str = "difficulty",
    sample_size: int = 100,
    threshold: int = 50
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Perform stratified sampling on dataset.
    
    Args:
        data: List of task dictionaries
        strata_key: Key to use for stratification
        sample_size: Target sample size
        threshold: Minimum samples per stratum
        
    Returns:
        Tuple of (sampled_data, strata_log)
    """
    # Group by strata
    strata_groups: Dict[str, List[Dict]] = {}
    for task in data:
        stratum = determine_strata(task)
        if stratum not in strata_groups:
            strata_groups[stratum] = []
        strata_groups[stratum].append(task)
    
    # Log strata info
    strata_log = {
        "strata": [],
        "total_samples": len(data),
        "threshold": threshold
    }
    
    sampled = []
    underpowered_strata = []
    
    for stratum, tasks in strata_groups.items():
        count = len(tasks)
        underpowered = count < threshold
        
        strata_log["strata"].append({
            "name": stratum,
            "count": count,
            "underpowered": underpowered
        })
        
        if underpowered:
            underpowered_strata.append(stratum)
        else:
            # Sample from this stratum
            n = min(count, sample_size // len(strata_groups))
            sampled.extend(random.sample(tasks, n))
    
    return sampled, strata_log

def stratify_data(
    humaneval: Any,
    mbpp: Any,
    output_path: str = os.path.join(PROCESSED_DATA_DIR, "strata_log.json"),
    threshold: int = 50
) -> None:
    """
    Apply stratified sampling and save strata log.
    
    Args:
        humaneval: HumanEval dataset
        mbpp: MBPP dataset
        output_path: Output path for strata log
        threshold: Minimum samples per stratum
    """
    # Combine datasets
    all_data = []
    
    # Process HumanEval
    for item in humaneval['test']:
        all_data.append({
            "task_id": item.get('task_id', 'humaneval_' + str(len(all_data))),
            "prompt": item.get('prompt', ''),
            "test": item.get('test', ''),
            "difficulty": "medium"  # Default difficulty
        })
    
    # Process MBPP
    for item in mbpp['train']:
        all_data.append({
            "task_id": item.get('task_id', 'mbpp_' + str(len(all_data))),
            "prompt": item.get('prompt', ''),
            "test": item.get('test', ''),
            "difficulty": "easy"  # Default difficulty
        })
    
    # Stratify
    sampled, strata_log = stratified_sample(all_data, threshold=threshold)
    
    # Save strata log
    with open(output_path, 'w') as f:
        json.dump(strata_log, f, indent=2)
    
    logger.info(f"Strata log saved to {output_path}")

def save_splits(
    data: List[Dict[str, Any]],
    output_path: str = os.path.join(PROCESSED_DATA_DIR, "splits.json")
) -> None:
    """
    Save processed splits to JSON.
    
    Args:
        data: List of task dictionaries
        output_path: Output path
    """
    # Split into train/test (80/20)
    random.shuffle(data)
    split_idx = int(len(data) * 0.8)
    
    splits = {
        "train": data[:split_idx],
        "test": data[split_idx:]
    }
    
    with open(output_path, 'w') as f:
        json.dump(splits, f, indent=2)
    
    logger.info(f"Splits saved to {output_path}")

def filter_strata(
    strata_log_path: str = os.path.join(PROCESSED_DATA_DIR, "strata_log.json"),
    splits_path: str = os.path.join(PROCESSED_DATA_DIR, "splits.json"),
    output_path: str = os.path.join(PROCESSED_DATA_DIR, "filtered_splits.json")
) -> None:
    """
    Filter out samples from underpowered strata.
    
    Args:
        strata_log_path: Path to strata log
        splits_path: Path to splits file
        output_path: Output path for filtered splits
    """
    # Pre-check: verify files exist
    if not os.path.exists(strata_log_path):
        raise FileNotFoundError(f"Strata log not found: {strata_log_path}")
    if not os.path.exists(splits_path):
        raise FileNotFoundError(f"Splits file not found: {splits_path}")
    
    # Load strata log
    with open(strata_log_path, 'r') as f:
        strata_log = json.load(f)
    
    # Identify underpowered strata
    underpowered_names = {
        s['name'] for s in strata_log['strata'] if s.get('underpowered', False)
    }
    
    logger.info(f"Filtering out {len(underpowered_names)} underpowered strata")
    
    # Load splits
    with open(splits_path, 'r') as f:
        splits = json.load(f)
    
    # Determine stratum for each task and filter
    def get_stratum(task: Dict) -> str:
        if 'difficulty' in task:
            return task['difficulty']
        elif 'task_id' in task:
            hash_val = int(hashlib.md5(task['task_id'].encode()).hexdigest(), 16)
            return f"stratum_{hash_val % 5}"
        return "unknown"
    
    filtered_train = []
    filtered_test = []
    
    for task in splits.get('train', []):
        stratum = get_stratum(task)
        if stratum not in underpowered_names:
            filtered_train.append(task)
    
    for task in splits.get('test', []):
        stratum = get_stratum(task)
        if stratum not in underpowered_names:
            filtered_test.append(task)
    
    filtered_splits = {
        "train": filtered_train,
        "test": filtered_test
    }
    
    with open(output_path, 'w') as f:
        json.dump(filtered_splits, f, indent=2)
    
    logger.info(f"Filtered splits saved to {output_path}")
    logger.info(f"Original: {len(splits.get('train', [])) + len(splits.get('test', []))} -> Filtered: {len(filtered_train) + len(filtered_test)}")

def main():
    """Main entry point for data loader."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Data loading and preprocessing")
    parser.add_argument("--fetch", action="store_true", help="Fetch datasets")
    parser.add_argument("--checksum", action="store_true", help="Compute checksums")
    parser.add_argument("--stratify", action="store_true", help="Stratify data")
    parser.add_argument("--filter", action="store_true", help="Filter underpowered strata")
    
    args = parser.parse_args()
    
    ensure_directories()
    
    if args.fetch:
        humaneval, mbpp = fetch_datasets()
        if args.stratify:
            stratify_data(humaneval, mbpp)
        if args.checksum:
            checksum_datasets()
    
    if args.filter:
        filter_strata()

if __name__ == "__main__":
    main()