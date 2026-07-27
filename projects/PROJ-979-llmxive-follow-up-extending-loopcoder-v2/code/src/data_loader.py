import hashlib
import json
import os
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from datasets import load_dataset

# --- Configuration ---
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml.
    
    Returns:
        Dictionary containing configuration values.
    """
    if not CONFIG_PATH.exists():
        # Default config if file doesn't exist
        return {"min_strata_size": 50}
    
    import yaml
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    
    # Ensure required keys exist with defaults
    if 'min_strata_size' not in config:
        config['min_strata_size'] = 50
        
    return config

def ensure_directories():
    """Create necessary directories for data storage."""
    dirs = [
        Path(__file__).parent.parent.parent / "data" / "raw",
        Path(__file__).parent.parent.parent / "data" / "processed",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        SHA256 hash string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_datasets() -> None:
    """Fetch HumanEval and MBPP datasets via datasets.load_dataset.
    
    Saves raw copies to data/raw/.
    """
    ensure_directories()
    data_dir = Path(__file__).parent.parent.parent / "data" / "raw"
    
    # Fetch HumanEval
    print("Fetching HumanEval dataset...")
    human_eval = load_dataset("openai_humaneval")
    # Save to parquet for efficiency
    human_eval_path = data_dir / "humaneval.parquet"
    human_eval.to_parquet(str(human_eval_path))
    print(f"Saved HumanEval to {human_eval_path}")
    
    # Fetch MBPP
    print("Fetching MBPP dataset...")
    mbpp = load_dataset("mbpp")
    # Save to parquet
    mbpp_path = data_dir / "mbpp.parquet"
    mbpp.to_parquet(str(mbpp_path))
    print(f"Saved MBPP to {mbpp_path}")

def save_raw_dataset(dataset, name: str, split: str = "test") -> Path:
    """Save a dataset split to a raw file.
    
    Args:
        dataset: The dataset object.
        name: Name of the dataset.
        split: The split to save.
        
    Returns:
        Path to the saved file.
    """
    ensure_directories()
    data_dir = Path(__file__).parent.parent.parent / "data" / "raw"
    file_path = data_dir / f"{name}_{split}.parquet"
    dataset[split].to_parquet(str(file_path))
    return file_path

def checksum_datasets() -> None:
    """Compute SHA256 checksums for ALL files in data/raw/ and write to data/checksums.txt.
    
    Format: <sha256_hash> <filename>
    """
    data_dir = Path(__file__).parent.parent.parent / "data" / "raw"
    checksum_file = Path(__file__).parent.parent.parent / "data" / "checksums.txt"
    
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory {data_dir} does not exist. Run fetch_datasets() first.")
    
    checksums = []
    for file_path in data_dir.iterdir():
        if file_path.is_file():
            hash_val = compute_sha256(str(file_path))
            checksums.append(f"{hash_val} {file_path.name}")
    
    with open(checksum_file, 'w') as f:
        f.write('\n'.join(checksums))
    
    print(f"Checksums written to {checksum_file}")

def determine_strata(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """Determine strata counts based on difficulty or task_id hashing.
    
    Args:
        data: List of data samples.
        
    Returns:
        Dictionary mapping stratum name to count.
    """
    strata_counts = {}
    
    for item in data:
        # Try to use 'difficulty' column if available
        if 'difficulty' in item and item['difficulty']:
            stratum = item['difficulty']
        else:
            # Fallback: hash task_id to create strata
            task_id = item.get('task_id', str(random.random()))
            # Hash to get a bucket (0-9)
            hash_val = int(hashlib.md5(task_id.encode()).hexdigest(), 16) % 10
            stratum = f"difficulty_bucket_{hash_val}"
        
        strata_counts[stratum] = strata_counts.get(stratum, 0) + 1
        
    return strata_counts

def stratified_sample(data: List[Dict[str, Any]], strata: Dict[str, int], target_size: int) -> List[Dict[str, Any]]:
    """Apply stratified sampling.
    
    Args:
        data: Full dataset.
        strata: Strata definitions.
        target_size: Target sample size.
        
    Returns:
        Stratified sample.
    """
    # Group data by stratum
    strata_data = {name: [] for name in strata.keys()}
    for item in data:
        if 'difficulty' in item and item['difficulty']:
            stratum = item['difficulty']
        else:
            task_id = item.get('task_id', str(random.random()))
            hash_val = int(hashlib.md5(task_id.encode()).hexdigest(), 16) % 10
            stratum = f"difficulty_bucket_{hash_val}"
        
        if stratum in strata_data:
            strata_data[stratum].append(item)
    
    # Sample proportionally
    sample = []
    total_count = sum(strata.values())
    for stratum_name, count in strata.items():
        proportion = count / total_count
        sample_size = max(1, int(target_size * proportion))
        stratum_samples = strata_data[stratum_name]
        
        # Ensure we don't sample more than available
        sample_size = min(sample_size, len(stratum_samples))
        if sample_size > 0:
            sampled = random.sample(stratum_samples, sample_size)
            sample.extend(sampled)
            
    return sample

def save_strata_log(strata_info: List[Dict[str, Any]], output_path: Path) -> None:
    """Save strata information to a JSON log file.
    
    Args:
        strata_info: List of strata dictionaries with name, count, underpowered.
        output_path: Path to save the log.
    """
    log_data = {"strata": strata_info}
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    print(f"Strata log saved to {output_path}")

def stratify_data() -> None:
    """Apply stratified sampling by difficulty and flag underpowered strata.
    
    Reads from data/raw/ (must exist), uses threshold from config.yaml.
    Outputs:
        - data/processed/strata_log.json: Strata information with underpowered flags.
        - data/processed/splits.json: Train/test splits with stratification.
    """
    config = load_config()
    min_strata_size = config.get('min_strata_size', 50)
    
    ensure_directories()
    data_dir = Path(__file__).parent.parent.parent / "data" / "raw"
    processed_dir = Path(__file__).parent.parent.parent / "data" / "processed"
    
    # Load HumanEval
    humaneval_path = data_dir / "humaneval.parquet"
    if not humaneval_path.exists():
        raise FileNotFoundError(f"HumanEval not found at {humaneval_path}. Run fetch_datasets() first.")
    
    import pandas as pd
    humaneval_df = pd.read_parquet(humaneval_path)
    humaneval_data = humaneval_df.to_dict('records')
    
    # Load MBPP
    mbpp_path = data_dir / "mbpp.parquet"
    if not mbpp_path.exists():
        raise FileNotFoundError(f"MBPP not found at {mbpp_path}. Run fetch_datasets() first.")
    
    mbpp_df = pd.read_parquet(mbpp_path)
    mbpp_data = mbpp_df.to_dict('records')
    
    # Combine datasets
    # Add dataset source
    for item in humaneval_data:
        item['dataset_source'] = 'humaneval'
        if 'task_id' not in item:
            item['task_id'] = f"HE_{hashlib.md5(str(item).encode()).hexdigest()[:8]}"
        if 'prompt' not in item:
            item['prompt'] = item.get('prompt', item.get('canonical_solution', ''))
        if 'test' not in item:
            item['test'] = item.get('test', '')
        if 'difficulty' not in item:
            item['difficulty'] = 'unknown'
    
    for item in mbpp_data:
        item['dataset_source'] = 'mbpp'
        if 'task_id' not in item:
            item['task_id'] = f"MBPP_{item.get('task_id', hash(item))}"
        if 'prompt' not in item:
            item['prompt'] = item.get('prompt', '')
        if 'test' not in item:
            item['test'] = item.get('test_list', str(item.get('test_list', [])))
        if 'difficulty' not in item:
            item['difficulty'] = 'unknown'
    
    combined_data = humaneval_data + mbpp_data
    
    # Determine strata
    strata_counts = determine_strata(combined_data)
    
    # Flag underpowered strata
    strata_info = []
    for name, count in strata_counts.items():
        underpowered = count < min_strata_size
        strata_info.append({
            "name": name,
            "count": count,
            "underpowered": underpowered
        })
    
    # Save strata log
    strata_log_path = processed_dir / "strata_log.json"
    save_strata_log(strata_info, strata_log_path)
    
    # Split data into train/test (80/20)
    random.shuffle(combined_data)
    split_idx = int(len(combined_data) * 0.8)
    train_data = combined_data[:split_idx]
    test_data = combined_data[split_idx:]
    
    # Save splits
    splits = {
        "train": train_data,
        "test": test_data
    }
    splits_path = processed_dir / "splits.json"
    with open(splits_path, 'w') as f:
        json.dump(splits, f, indent=2)
    
    print(f"Strata log saved to {strata_log_path}")
    print(f"Splits saved to {splits_path}")
    print(f"Total samples: {len(combined_data)}, Train: {len(train_data)}, Test: {len(test_data)}")
    print(f"Strata with <{min_strata_size} samples flagged as underpowered: {sum(1 for s in strata_info if s['underpowered'])}")

def save_splits() -> None:
    """Save processed splits to data/processed/splits.json.
    
    This is a wrapper that calls stratify_data() to ensure splits are generated.
    """
    stratify_data()

def filter_strata() -> None:
    """Read strata_log.json and splits.json, filter out underpowered strata.
    
    Reads:
        - data/processed/strata_log.json: Strata information with underpowered flags.
        - data/processed/splits.json: Full train/test splits.
        
    Writes:
        - data/processed/filtered_splits.json: Splits with underpowered strata removed.
        
    Verification:
        - Row count should be less than original.
        - No samples from underpowered strata should remain.
    """
    config = load_config()
    min_strata_size = config.get('min_strata_size', 50)
    
    ensure_directories()
    processed_dir = Path(__file__).parent.parent.parent / "data" / "processed"
    
    # Load strata log
    strata_log_path = processed_dir / "strata_log.json"
    if not strata_log_path.exists():
        raise FileNotFoundError(f"Strata log not found at {strata_log_path}. Run stratify_data() first.")
    
    with open(strata_log_path, 'r') as f:
        strata_log = json.load(f)
    
    # Identify underpowered strata
    underpowered_strata = set()
    for stratum in strata_log.get('strata', []):
        if stratum.get('underpowered', False):
            underpowered_strata.add(stratum['name'])
    
    if not underpowered_strata:
        print("No underpowered strata found. Copying splits to filtered_splits.json.")
        # Just copy the splits if no filtering needed
        splits_path = processed_dir / "splits.json"
        filtered_path = processed_dir / "filtered_splits.json"
        with open(splits_path, 'r') as f:
            splits = json.load(f)
        with open(filtered_path, 'w') as f:
            json.dump(splits, f, indent=2)
        return
    
    print(f"Filtering out {len(underpowered_strata)} underpowered strata: {underpowered_strata}")
    
    # Load splits
    splits_path = processed_dir / "splits.json"
    if not splits_path.exists():
        raise FileNotFoundError(f"Splits not found at {splits_path}. Run stratify_data() first.")
    
    with open(splits_path, 'r') as f:
        splits = json.load(f)
    
    # Helper function to determine stratum of a sample
    def get_sample_stratum(sample: Dict[str, Any]) -> str:
        if 'difficulty' in sample and sample['difficulty']:
            return sample['difficulty']
        else:
            task_id = sample.get('task_id', str(random.random()))
            hash_val = int(hashlib.md5(task_id.encode()).hexdigest(), 16) % 10
            return f"difficulty_bucket_{hash_val}"
    
    # Filter train and test splits
    filtered_train = []
    filtered_test = []
    removed_train = 0
    removed_test = 0
    
    for sample in splits.get('train', []):
        stratum = get_sample_stratum(sample)
        if stratum not in underpowered_strata:
            filtered_train.append(sample)
        else:
            removed_train += 1
    
    for sample in splits.get('test', []):
        stratum = get_sample_stratum(sample)
        if stratum not in underpowered_strata:
            filtered_test.append(sample)
        else:
            removed_test += 1
    
    # Create filtered splits
    filtered_splits = {
        "train": filtered_train,
        "test": filtered_test
    }
    
    # Save filtered splits
    filtered_path = processed_dir / "filtered_splits.json"
    with open(filtered_path, 'w') as f:
        json.dump(filtered_splits, f, indent=2)
    
    print(f"Filtered splits saved to {filtered_path}")
    print(f"Original train: {len(splits.get('train', []))}, Filtered train: {len(filtered_train)} (removed {removed_train})")
    print(f"Original test: {len(splits.get('test', []))}, Filtered test: {len(filtered_test)} (removed {removed_test})")
    print(f"Total removed: {removed_train + removed_test}")
    
    # Verify no underpowered strata remain
    remaining_strata = set()
    for sample in filtered_train + filtered_test:
        remaining_strata.add(get_sample_stratum(sample))
    
    overlap = remaining_strata & underpowered_strata
    if overlap:
        raise RuntimeError(f"ERROR: Underpowered strata still present in filtered data: {overlap}")
    
    print("Verification passed: No underpowered strata remain in filtered data.")

def main():
    """Main entry point for data_loader module."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python data_loader.py <command>")
        print("Commands: fetch, checksum, stratify, filter, all")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "fetch":
        fetch_datasets()
    elif command == "checksum":
        checksum_datasets()
    elif command == "stratify":
        stratify_data()
    elif command == "filter":
        filter_strata()
    elif command == "all":
        fetch_datasets()
        checksum_datasets()
        stratify_data()
        filter_strata()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()