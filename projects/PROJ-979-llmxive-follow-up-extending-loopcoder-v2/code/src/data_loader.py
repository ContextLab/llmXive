import hashlib
import json
import os
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import logging

from datasets import load_dataset

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Project root relative to code/src
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CHECKSUMS_FILE = PROJECT_ROOT / "data" / "checksums.txt"
STRATA_LOG_FILE = DATA_PROCESSED_DIR / "strata_log.json"

# Configuration
DATASETS_CONFIG = {
    "humaneval": {
        "name": "openai_humaneval",
        "split": "test",
        "output_file": "humaneval_raw.jsonl"
    },
    "mbpp": {
        "name": "mbpp",
        "split": "test",
        "output_file": "mbpp_raw.jsonl"
    }
}

DEFAULT_RATIO = 0.5  # 50% sampling ratio
MIN_STRATA_SIZE = 50  # Threshold for 'underpowered' flag

def ensure_directories():
    """Create necessary directories for raw and processed data."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directories ensured: {DATA_RAW_DIR}, {DATA_PROCESSED_DIR}")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_dataset(dataset_name: str) -> Any:
    """Fetch dataset using the datasets library."""
    config = DATASETS_CONFIG.get(dataset_name)
    if not config:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    logger.info(f"Fetching dataset: {config['name']} (split: {config['split']})")
    try:
        dataset = load_dataset(config["name"], split=config["split"])
        return dataset
    except Exception as e:
        logger.error(f"Failed to fetch dataset {dataset_name}: {e}")
        raise

def save_raw_dataset(dataset: Any, dataset_name: str) -> Path:
    """Save raw dataset to data/raw/ and return the path."""
    config = DATASETS_CONFIG[dataset_name]
    output_file = DATA_RAW_DIR / config["output_file"]
    
    logger.info(f"Saving raw dataset to {output_file}")
    # Convert to list of dicts to ensure JSON serialization
    data_list = dataset.to_pandas().to_dict(orient='records')
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in data_list:
            json.dump(item, f)
            f.write('\n')
    
    return output_file

def determine_strata(dataset: Any, strata_column: Optional[str] = None) -> Dict[str, List[int]]:
    """
    Determine strata based on a column or hash of task_id.
    Returns a dict mapping stratum_name -> list of row indices.
    """
    strata = {}
    total_rows = len(dataset)
    
    # Check if 'difficulty' column exists
    if strata_column and strata_column in dataset.column_names:
        logger.info(f"Stratifying by column: {strata_column}")
        for idx, item in enumerate(dataset):
            key = str(item.get(strata_column, "unknown"))
            if key not in strata:
                strata[key] = []
            strata[key].append(idx)
    else:
        # Fallback: hash task_id or index
        logger.info("No difficulty column found. Using task_id hash for strata.")
        for idx, item in enumerate(dataset):
            task_id = item.get("task_id", str(idx))
            # Create bins based on hash
            hash_val = int(hashlib.md5(str(task_id).encode()).hexdigest(), 16)
            # Create 10 bins
            bin_id = str(hash_val % 10)
            if bin_id not in strata:
                strata[bin_id] = []
            strata[bin_id].append(idx)
    
    return strata

def stratified_sample(dataset: Any, strata: Dict[str, List[int]], ratio: float = DEFAULT_RATIO) -> List[int]:
    """
    Perform stratified sampling.
    Returns a list of sampled indices.
    """
    sampled_indices = []
    for stratum_name, indices in strata.items():
        n_sample = max(1, int(len(indices) * ratio))
        sampled = random.sample(indices, min(n_sample, len(indices)))
        sampled_indices.extend(sampled)
    
    logger.info(f"Stratified sampling completed. Total samples: {len(sampled_indices)}")
    return sampled_indices

def save_strata_log(strata: Dict[str, List[int]], underpowered_threshold: int = MIN_STRATA_SIZE):
    """
    Save strata information and flag underpowered strata.
    """
    log_data = {
        "strata": {},
        "underpowered_strata": [],
        "total_strata": len(strata),
        "threshold": underpowered_threshold
    }
    
    for stratum_name, indices in strata.items():
        size = len(indices)
        is_underpowered = size < underpowered_threshold
        log_data["strata"][stratum_name] = {
            "size": size,
            "underpowered": is_underpowered
        }
        if is_underpowered:
            log_data["underpowered_strata"].append(stratum_name)
    
    with open(STRATA_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Strata log saved to {STRATA_LOG_FILE}. Underpowered strata: {log_data['underpowered_strata']}")

def save_processed_split(dataset: Any, indices: List[int], output_filename: str):
    """Save the processed split to data/processed/."""
    output_path = DATA_PROCESSED_DIR / output_filename
    
    sampled_data = [dataset[int(i)] for i in indices]
    
    logger.info(f"Saving processed split to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in sampled_data:
            json.dump(item, f)
            f.write('\n')

def save_checksums(file_path: Path, checksum: str):
    """Append checksum to the checksums file."""
    with open(CHECKSUMS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{file_path.name}: {checksum}\n")

def main():
    """Main execution function for data loading and processing."""
    ensure_directories()
    
    # Clear checksums file for fresh run
    if CHECKSUMS_FILE.exists():
        CHECKSUMS_FILE.unlink()
    
    all_strata = {}
    
    for dataset_name in DATASETS_CONFIG.keys():
        logger.info(f"Processing dataset: {dataset_name}")
        
        # Fetch
        dataset = fetch_dataset(dataset_name)
        
        # Save raw
        raw_file = save_raw_dataset(dataset, dataset_name)
        
        # Compute checksum
        checksum = compute_sha256(raw_file)
        save_checksums(raw_file, checksum)
        
        # Determine strata
        strata = determine_strata(dataset)
        
        # Merge strata for global logging (optional, or keep separate)
        # For this task, we log per dataset but combine for the log file if needed.
        # Let's save strata log per dataset or combine? The task says "flag strata".
        # We will save a combined log or per dataset. Let's save per dataset in the log file structure.
        # Actually, the task says "save processed splits" and "flag strata".
        # We'll create a combined strata log for the project run.
        # Renaming keys to include dataset name to avoid collision
        prefixed_strata = {f"{dataset_name}_{k}": v for k, v in strata.items()}
        all_strata.update(prefixed_strata)
        
        # Stratified sample
        sampled_indices = stratified_sample(dataset, strata)
        
        # Save processed split
        output_filename = f"{dataset_name}_processed.jsonl"
        save_processed_split(dataset, sampled_indices, output_filename)
    
    # Save final strata log
    save_strata_log(all_strata)
    
    logger.info("Data loading and processing completed successfully.")

if __name__ == "__main__":
    main()
