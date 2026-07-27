"""
Data loading and preprocessing module.
Implements T004: Dataset fetching, stratification, and filtering.
"""
import hashlib
import json
import os
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from datasets import load_dataset

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    """
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def ensure_directories() -> None:
    """
    Ensure all required directories exist.
    """
    dirs = [
        "data/raw",
        "data/processed",
        "code/src",
        "code/tests",
        "code/notebooks"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_datasets() -> Dict[str, Any]:
    """
    Fetch HumanEval and MBPP datasets from HuggingFace.
    Save raw copies to data/raw/.
    
    Returns:
        Dict with dataset names and paths.
    """
    ensure_directories()
    
    datasets = {}
    
    # Fetch HumanEval
    try:
        human_eval = load_dataset("openai_humaneval", split="test")
        datasets["humaneval"] = human_eval
        # Save to raw
        raw_path = "data/raw/humaneval.json"
        with open(raw_path, 'w') as f:
            json.dump(human_eval.to_list(), f)
        print(f"Saved HumanEval to {raw_path}")
    except Exception as e:
        print(f"Failed to fetch HumanEval: {e}")
        raise
    
    # Fetch MBPP
    try:
        mbpp = load_dataset("mbpp", split="test")
        datasets["mbpp"] = mbpp
        # Save to raw
        raw_path = "data/raw/mbpp.json"
        with open(raw_path, 'w') as f:
            json.dump(mbpp.to_list(), f)
        print(f"Saved MBPP to {raw_path}")
    except Exception as e:
        print(f"Failed to fetch MBPP: {e}")
        raise
    
    return datasets

def checksum_datasets() -> str:
    """
    Compute SHA256 checksums for all files in data/raw/.
    Write to data/checksums.txt.
    
    Returns:
        Path to checksums file.
    """
    checksums = []
    raw_dir = Path("data/raw")
    
    for file_path in raw_dir.glob("*"):
        if file_path.is_file():
            hash_val = compute_sha256(str(file_path))
            checksums.append(f"{hash_val} {file_path.name}")
    
    checksum_path = "data/checksums.txt"
    with open(checksum_path, 'w') as f:
        f.write("\n".join(checksums))
    
    print(f"Checksums written to {checksum_path}")
    return checksum_path

def determine_strata(
    data: List[Dict[str, Any]],
    threshold: int = 50
) -> List[Dict[str, Any]]:
    """
    Determine strata based on difficulty or task_id hashing.
    
    Args:
        data: List of data items.
        threshold: Minimum samples per stratum.
        
    Returns:
        List of strata with counts and underpowered flags.
    """
    strata_counts: Dict[str, int] = {}
    
    for item in data:
        # Use difficulty if available, else hash task_id
        if 'difficulty' in item:
            stratum = item['difficulty']
        else:
            task_id = item.get('task_id', str(item))
            stratum = hashlib.md5(task_id.encode()).hexdigest()[:2]
        
        strata_counts[stratum] = strata_counts.get(stratum, 0) + 1
    
    strata_log = []
    for stratum, count in strata_counts.items():
        underpowered = count < threshold
        strata_log.append({
            "name": stratum,
            "count": count,
            "underpowered": underpowered
        })
    
    return strata_log

def stratified_sample(
    data: List[Dict[str, Any]],
    strata_log: List[Dict[str, Any]],
    threshold: int = 50
) -> List[Dict[str, Any]]:
    """
    Perform stratified sampling, keeping all strata above threshold.
    
    Args:
        data: Full dataset.
        strata_log: Strata information.
        threshold: Minimum samples per stratum.
        
    Returns:
        Stratified sample.
    """
    # Filter underpowered strata
    valid_strata = [s['name'] for s in strata_log if not s['underpowered']]
    
    # Map item to stratum
    def get_stratum(item):
        if 'difficulty' in item:
            return item['difficulty']
        task_id = item.get('task_id', str(item))
        return hashlib.md5(task_id.encode()).hexdigest()[:2]
    
    # Filter data
    sampled_data = [item for item in data if get_stratum(item) in valid_strata]
    
    return sampled_data

def save_strata_log(strata_log: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save strata log to JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({"strata": strata_log}, f, indent=2)

def stratify_data(
    input_path: str,
    output_path: str,
    threshold: int = 50
) -> List[Dict[str, Any]]:
    """
    Apply stratified sampling by difficulty.
    
    Args:
        input_path: Path to input data.
        output_path: Path to output strata log.
        threshold: Minimum samples per stratum.
        
    Returns:
        Stratified data.
    """
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    strata_log = determine_strata(data, threshold)
    save_strata_log(strata_log, output_path)
    
    sampled_data = stratified_sample(data, strata_log, threshold)
    
    print(f"Stratified data: {len(sampled_data)} samples from {len(data)}")
    return sampled_data

def save_splits(
    data: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Save processed splits to JSON file.
    
    Args:
        data: Data to save.
        output_path: Output path.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    splits = {
        "train": data[:len(data)//2],
        "test": data[len(data)//2:]
    }
    
    with open(output_path, 'w') as f:
        json.dump(splits, f, indent=2)

def filter_strata(
    strata_log_path: str,
    splits_path: str,
    output_path: str
) -> List[Dict[str, Any]]:
    """
    Filter out samples belonging to underpowered strata.
    
    Args:
        strata_log_path: Path to strata log.
        splits_path: Path to splits file.
        output_path: Path to output filtered splits.
        
    Returns:
        Filtered data.
    """
    # Load strata log
    with open(strata_log_path, 'r') as f:
        strata_data = json.load(f)
    
    valid_strata = [s['name'] for s in strata_data['strata'] if not s['underpowered']]
    
    # Load splits
    with open(splits_path, 'r') as f:
        splits = json.load(f)
    
    # Map item to stratum
    def get_stratum(item):
        if 'difficulty' in item:
            return item['difficulty']
        task_id = item.get('task_id', str(item))
        return hashlib.md5(task_id.encode()).hexdigest()[:2]
    
    # Filter both train and test
    filtered_train = [item for item in splits['train'] if get_stratum(item) in valid_strata]
    filtered_test = [item for item in splits['test'] if get_stratum(item) in valid_strata]
    
    filtered_data = filtered_train + filtered_test
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(filtered_data, f, indent=2)
    
    print(f"Filtered data: {len(filtered_data)} samples (removed underpowered strata)")
    return filtered_data

def main():
    """
    Main entry point for data loading pipeline.
    Usage: python code/src/data_loader.py
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Data loading and preprocessing.")
    parser.add_argument('--config', type=str, default='code/config.yaml',
                        help='Path to config file')
    parser.add_argument('--threshold', type=int, default=50,
                        help='Strata threshold')
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    threshold = config.get('strata_threshold', args.threshold)
    
    # Fetch datasets
    print("Fetching datasets...")
    fetch_datasets()
    
    # Checksums
    print("Computing checksums...")
    checksum_datasets()
    
    # Load raw data (combine humaneval and mbpp)
    with open("data/raw/humaneval.json", 'r') as f:
        humaneval_data = json.load(f)
    with open("data/raw/mbpp.json", 'r') as f:
        mbpp_data = json.load(f)
    
    combined_data = humaneval_data + mbpp_data
    
    # Stratify
    print("Stratifying data...")
    strata_log_path = "data/processed/strata_log.json"
    stratify_data("data/raw/combined.json", strata_log_path, threshold)
    
    # Save splits
    splits_path = "data/processed/splits.json"
    save_splits(combined_data, splits_path)
    
    # Filter
    filtered_path = "data/processed/filtered_splits.json"
    filter_strata(strata_log_path, splits_path, filtered_path)
    
    print("Data loading complete.")

if __name__ == "__main__":
    main()
