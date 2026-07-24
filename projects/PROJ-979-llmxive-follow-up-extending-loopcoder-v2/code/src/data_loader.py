import hashlib
import json
import os
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import csv

# Ensure compatibility with existing API surface
# The following imports are assumed to be available in the environment
# based on the provided API surface list.
try:
    from datasets import load_dataset
except ImportError:
    # Fallback for environments where datasets might not be installed yet,
    # though T002 should have installed it.
    load_dataset = None

def ensure_directories(base_path: str = "data") -> None:
    """Create necessary directory structure for data processing."""
    dirs = [
        Path(base_path),
        Path(base_path) / "raw",
        Path(base_path) / "processed",
        Path(base_path) / "figures",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_dataset(dataset_name: str, split: str = "test") -> List[Dict[str, Any]]:
    """Fetch a dataset using the HuggingFace datasets library."""
    if load_dataset is None:
        raise ImportError("datasets library is required to fetch datasets.")
    
    # Attempt to load the dataset
    # Handling different dataset structures (HumanEval vs MBPP)
    try:
        ds = load_dataset(dataset_name, split=split)
        # Convert to list of dicts
        data = []
        for item in ds:
            # Normalize keys to expected format
            normalized = {}
            for k, v in item.items():
                if isinstance(v, dict) and 'task_id' in v:
                    # Some datasets have nested task_id
                    normalized['task_id'] = v['task_id']
                elif k == 'task_id':
                    normalized['task_id'] = v
                elif k == 'prompt':
                    normalized['prompt'] = v
                elif k == 'canonical_solution':
                    normalized['canonical_solution'] = v
                elif k == 'test':
                    normalized['test'] = v
                elif k == 'entry_point':
                    normalized['entry_point'] = v
                elif k == 'difficulty':
                    normalized['difficulty'] = v
                elif k == 'code':
                    normalized['code'] = v
                else:
                    # Keep other fields as is
                    normalized[k] = v
            data.append(normalized)
        return data
    except Exception as e:
        raise RuntimeError(f"Failed to fetch dataset {dataset_name}: {e}")

def save_raw_dataset(data: List[Dict[str, Any]], filename: str, base_path: str = "data") -> str:
    """Save raw dataset to JSON."""
    ensure_directories(base_path)
    output_path = Path(base_path) / "raw" / filename
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return str(output_path)

def determine_strata(data: List[Dict[str, Any]], strata_key: str = "difficulty") -> Dict[str, List[int]]:
    """
    Determine strata based on a key. If key missing, use task_id hashing.
    Returns a dict mapping stratum_name -> list of indices.
    """
    strata = {}
    for idx, item in enumerate(data):
        if strata_key in item and item[strata_key]:
            stratum_name = str(item[strata_key])
        else:
            # Fallback: hash task_id to create pseudo-strata
            task_id = item.get('task_id', str(idx))
            # Create 4 buckets based on hash
            h = int(hashlib.md5(str(task_id).encode()).hexdigest(), 16) % 4
            stratum_name = f"bucket_{h}"
        
        if stratum_name not in strata:
            strata[stratum_name] = []
        strata[stratum_name].append(idx)
    return strata

def stratified_sample(data: List[Dict[str, Any]], strata: Dict[str, List[int]], target_size: Optional[int] = None) -> List[int]:
    """
    Perform stratified sampling.
    If target_size is None, returns all indices.
    If a stratum has < 50 samples, it is flagged as 'underpowered' in the log.
    """
    sampled_indices = []
    underpowered_strata = []
    
    for stratum_name, indices in strata.items():
        if len(indices) < 50:
            underpowered_strata.append(stratum_name)
            # Include all samples from underpowered strata for now, 
            # they will be filtered in T004e
            sampled_indices.extend(indices)
        else:
            # Sample proportionally or fixed if target_size is specified
            if target_size:
                # Simple proportional sampling logic
                # This is a placeholder logic; actual implementation might vary
                sample_count = max(1, int((len(indices) / len(data)) * target_size))
                sampled_indices.extend(random.sample(indices, min(sample_count, len(indices))))
            else:
                sampled_indices.extend(indices)
    
    return sampled_indices, underpowered_strata

def save_strata_log(strata: Dict[str, List[int]], underpowered: List[str], log_path: str = "data/processed/strata_log.json"):
    """Save strata information and underpowered flags to JSON."""
    ensure_directories("data")
    log_data = {
        "strata": {k: len(v) for k, v in strata.items()},
        "underpowered_strata": underpowered,
        "total_samples": sum(len(v) for v in strata.values())
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)

def save_processed_split(data: List[Dict[str, Any]], indices: List[int], filename: str, base_path: str = "data"):
    """Save the processed split (subset of data) to JSON."""
    ensure_directories(base_path)
    output_path = Path(base_path) / "processed" / filename
    subset = [data[i] for i in indices]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(subset, f, indent=2)
    return str(output_path)

def save_checksums(checksums: Dict[str, str], path: str = "data/checksums.txt"):
    """Save checksums to a text file."""
    with open(path, "w", encoding="utf-8") as f:
        for filename, checksum in checksums.items():
            f.write(f"{checksum}  {filename}\n")

def save_splits(data: List[Dict[str, Any]], train_indices: List[int], test_indices: List[int], base_path: str = "data"):
    """Save train and test splits."""
    ensure_directories(base_path)
    train_path = Path(base_path) / "processed" / "train_split.json"
    test_path = Path(base_path) / "processed" / "test_split.json"
    
    with open(train_path, "w", encoding="utf-8") as f:
        json.dump([data[i] for i in train_indices], f, indent=2)
    with open(test_path, "w", encoding="utf-8") as f:
        json.dump([data[i] for i in test_indices], f, indent=2)

def filter_underpowered(strata_log_path: str = "data/processed/strata_log.json", 
                        input_dataset_path: str = "data/processed/split_dataset.json",
                        output_dataset_path: str = "data/processed/filtered_dataset.json") -> str:
    """
    Read strata_log.json, identify underpowered strata, and exclude samples belonging to them.
    Save the filtered dataset to output_dataset_path.
    """
    # Load strata log
    try:
        with open(strata_log_path, "r", encoding="utf-8") as f:
            strata_log = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Strata log not found at {strata_log_path}. Run T004c first.")
    
    underpowered_strata = strata_log.get("underpowered_strata", [])
    strata_map = strata_log.get("strata", {}) # This is {name: count}, we need to know which indices belong to which stratum
    
    # We need to reconstruct which indices belong to which stratum.
    # The strata_log from T004c only stored counts. We need to re-read the original split
    # or the log must have been more detailed. 
    # However, T004c's logic (as implied by the task description) flags strata.
    # To filter correctly, we need to know the stratum assignment for each item in the input dataset.
    # Since the input dataset (split_dataset.json) doesn't inherently have stratum info unless added,
    # we must re-calculate strata or rely on the log having stored the mapping.
    # Given the constraint "Read strata_log.json", we assume the log might need to be more detailed
    # OR we re-calculate strata on the input dataset to match the original logic.
    
    # Let's assume the input dataset has a 'difficulty' or 'task_id' that can be used to re-determine strata.
    # We will re-run the strata determination logic on the input dataset to identify underpowered ones.
    
    try:
        with open(input_dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Input dataset not found at {input_dataset_path}.")
    
    # Re-determine strata to map indices to stratum names
    # Using the same logic as determine_strata in T004c
    current_strata = determine_strata(data, strata_key="difficulty")
    
    # Identify which strata are underpowered based on the log's list
    # We compare the stratum names from the log with the ones we just computed.
    # Note: If the original T004c used a different random seed or logic for stratification,
    # the indices might differ. But since we are filtering the *output* of T004c (the split),
    # we assume the strata definitions (names) are consistent.
    
    underpowered_set = set(underpowered_strata)
    indices_to_keep = []
    excluded_count = 0
    excluded_reasons = []

    for idx, item in enumerate(data):
        # Determine stratum for this item
        if "difficulty" in item and item["difficulty"]:
            stratum_name = str(item["difficulty"])
        else:
            task_id = item.get('task_id', str(idx))
            h = int(hashlib.md5(str(task_id).encode()).hexdigest(), 16) % 4
            stratum_name = f"bucket_{h}"
        
        if stratum_name in underpowered_set:
            excluded_count += 1
            excluded_reasons.append({"task_id": item.get("task_id", idx), "stratum": stratum_name})
        else:
            indices_to_keep.append(idx)
    
    # Filter data
    filtered_data = [data[i] for i in indices_to_keep]
    
    # Save filtered dataset
    ensure_directories("data")
    with open(output_dataset_path, "w", encoding="utf-8") as f:
        json.dump(filtered_data, f, indent=2)
    
    # Log exclusion details (optional but good practice)
    exclusion_log_path = output_dataset_path.replace("filtered_dataset.json", "filter_exclusion_log.json")
    with open(exclusion_log_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_excluded": excluded_count,
            "underpowered_strata": list(underpowered_set),
            "excluded_items": excluded_reasons[:10] # Limit log size
        }, f, indent=2)
    
    return output_dataset_path

def main():
    """Main entry point for data loader script."""
    print("Data Loader Module Loaded.")
    # Example usage if run as script
    # This is typically called by other scripts
    pass

# Ensure the function is available for import as per API surface
# The function 'filter_underpowered' is now implemented.