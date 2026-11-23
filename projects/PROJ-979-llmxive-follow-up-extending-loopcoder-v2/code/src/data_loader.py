import hashlib
import json
import os
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
from datasets import load_dataset

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    """
    import yaml
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def ensure_directories():
    """
    Ensure required directories exist.
    """
    dirs = [
        "data/raw",
        "data/processed",
        "code/src",
        "code/tests",
        "code/notebooks"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_datasets():
    """
    Fetch HumanEval and MBPP datasets.
    """
    ensure_directories()
    
    # Fetch HumanEval
    try:
        human_eval = load_dataset("openai_humaneval")
        human_eval.save_to_disk("data/raw/human_eval")
        logger.info("HumanEval dataset fetched and saved.")
    except Exception as e:
        logger.error(f"Failed to fetch HumanEval: {e}")
        raise
    
    # Fetch MBPP
    try:
        mbpp = load_dataset("mbpp")
        mbpp.save_to_disk("data/raw/mbpp")
        logger.info("MBPP dataset fetched and saved.")
    except Exception as e:
        logger.error(f"Failed to fetch MBPP: {e}")
        raise

def checksum_datasets():
    """
    Compute checksums for all files in data/raw and data/processed.
    """
    checksums = []
    
    for root, dirs, files in os.walk("data/raw"):
        for file in files:
            file_path = os.path.join(root, file)
            checksum = compute_sha256(file_path)
            checksums.append(f"{checksum}  {file_path}")
    
    for root, dirs, files in os.walk("data/processed"):
        for file in files:
            file_path = os.path.join(root, file)
            checksum = compute_sha256(file_path)
            checksums.append(f"{checksum}  {file_path}")
    
    with open("data/checksums.txt", "w") as f:
        f.write("\n".join(checksums))
    
    logger.info("Checksums computed and saved to data/checksums.txt")

def determine_strata(data: List[Dict]) -> Dict[str, int]:
    """
    Determine strata based on difficulty column or task_id hashing.
    """
    strata = {}
    for item in data:
        difficulty = item.get("difficulty", "unknown")
        if difficulty not in strata:
            strata[difficulty] = 0
        strata[difficulty] += 1
    return strata

def stratified_sample(data: List[Dict], strata: Dict[str, int], sample_size: int) -> List[Dict]:
    """
    Perform stratified sampling.
    """
    sampled = []
    for stratum, count in strata.items():
        stratum_data = [item for item in data if item.get("difficulty", "unknown") == stratum]
        sample_count = min(int(count * sample_size / len(data)), len(stratum_data))
        sampled.extend(random.sample(stratum_data, sample_count))
    return sampled

def stratify_data():
    """
    Apply stratified sampling by difficulty.
    """
    cfg = load_config()
    threshold = cfg.get("strata_threshold", 50)
    
    # Load data
    data_path = "data/raw/human_eval"
    if not os.path.exists(data_path):
        fetch_datasets()
    
    human_eval = load_dataset("data/raw/human_eval")
    data = list(human_eval["train"])
    
    # Determine strata
    strata = determine_strata(data)
    
    # Log strata
    strata_log = {
        "strata": [
            {
                "name": name,
                "count": count,
                "underpowered": count < threshold
            }
            for name, count in strata.items()
        ]
    }
    
    with open("data/processed/strata_log.json", "w") as f:
        json.dump(strata_log, f, indent=2)
    
    logger.info("Strata log saved to data/processed/strata_log.json")
    
    # Save splits
    save_splits(data)
    filter_strata()

def save_splits(data: List[Dict]):
    """
    Save processed splits to JSON.
    """
    # Split into train and test
    random.shuffle(data)
    split_idx = int(len(data) * 0.8)
    train = data[:split_idx]
    test = data[split_idx:]
    
    splits = {
        "train": train,
        "test": test
    }
    
    with open("data/processed/splits.json", "w") as f:
        json.dump(splits, f, indent=2)
    
    logger.info("Splits saved to data/processed/splits.json")

def filter_strata():
    """
    Filter out underpowered strata.
    """
    # Load strata log
    with open("data/processed/strata_log.json", "r") as f:
        strata_log = json.load(f)
    
    # Load splits
    with open("data/processed/splits.json", "r") as f:
        splits = json.load(f)
    
    # Identify underpowered strata
    underpowered = [s["name"] for s in strata_log["strata"] if s["underpowered"]]
    
    # Filter data
    filtered_train = [item for item in splits["train"] if item.get("difficulty", "unknown") not in underpowered]
    filtered_test = [item for item in splits["test"] if item.get("difficulty", "unknown") not in underpowered]
    
    # Save filtered splits
    filtered_splits = {
        "train": filtered_train,
        "test": filtered_test
    }
    
    with open("data/processed/filtered_splits.json", "w") as f:
        json.dump(filtered_splits, f, indent=2)
    
    # Save exclusion report
    exclusion_report = {
        "underpowered_strata": underpowered,
        "excluded_count": len(splits["train"]) - len(filtered_train) + len(splits["test"]) - len(filtered_test),
        "total_count": len(splits["train"]) + len(splits["test"])
    }
    
    with open("data/processed/exclusion_rate_report.json", "w") as f:
        json.dump(exclusion_report, f, indent=2)
    
    logger.info("Filtered splits saved to data/processed/filtered_splits.json")

def generate_unseen_set():
    """
    Generate unseen validation set.
    """
    # Load splits
    with open("data/processed/splits.json", "r") as f:
        splits = json.load(f)
    
    test_set = splits["test"]
    
    # Split test set into held_out_test and unseen_validation
    random.shuffle(test_set)
    split_idx = int(len(test_set) * 0.5)
    held_out_test = test_set[:split_idx]
    unseen_validation = test_set[split_idx:]
    
    # Save unseen validation set
    unseen_df = pd.DataFrame(unseen_validation)
    unseen_df.to_csv("data/processed/unseen_validation_set.csv", index=False)
    
    # Update checksums
    checksum_datasets()
    
    logger.info("Unseen validation set saved to data/processed/unseen_validation_set.csv")

def verify_disjoint_sets():
    """
    Verify that held_out_test and unseen_validation are disjoint.
    """
    # Load splits
    with open("data/processed/splits.json", "r") as f:
        splits = json.load(f)
    
    # Load unseen validation set
    unseen_df = pd.read_csv("data/processed/unseen_validation_set.csv")
    unseen_ids = set(unseen_df["task_id"].tolist())
    
    # Get held_out_test task_ids
    held_out_ids = set([item["task_id"] for item in splits["test"]])
    
    # Check intersection
    intersection = held_out_ids & unseen_ids
    
    if len(intersection) > 0:
        raise ValueError(f"Intersection found: {intersection}")
    
    # Log result
    result = {
        "intersection_size": len(intersection),
        "status": "disjoint"
    }
    
    with open("data/processed/disjoint_verification.json", "w") as f:
        json.dump(result, f, indent=2)
    
    logger.info("Disjoint sets verified")

def load_filtered_splits(input_path: str = "data/processed/filtered_splits.json") -> List[Dict]:
    """
    Load filtered splits from JSON.
    """
    with open(input_path, "r") as f:
        data = json.load(f)
    # Return combined train and test for inference
    return data["train"] + data["test"]

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Loader")
    parser.add_argument("--action", type=str, required=True, help="Action to perform: fetch, stratify, filter, generate_unseen, verify_disjoint")
    
    args = parser.parse_args()
    
    if args.action == "fetch":
        fetch_datasets()
    elif args.action == "stratify":
        stratify_data()
    elif args.action == "filter":
        filter_strata()
    elif args.action == "generate_unseen":
        generate_unseen_set()
    elif args.action == "verify_disjoint":
        verify_disjoint_sets()
    else:
        raise ValueError(f"Unknown action: {args.action}")

if __name__ == "__main__":
    main()