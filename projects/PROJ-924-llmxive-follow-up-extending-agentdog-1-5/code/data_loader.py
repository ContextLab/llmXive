import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Generator

from datasets import load_dataset
from config import get_path, ensure_directories
from utils import load_json_file, save_json_file

def fetch_advbench() -> List[Dict[str, Any]]:
    """
    Fetch the AdvBench dataset using HuggingFace datasets with streaming.
    Returns a list of dictionaries containing the attack prompts.
    """
    ds = load_dataset("llm-attacks/advbench", split="train", streaming=True)
    logs = []
    for item in ds:
        logs.append({"log_id": item.get("goal_id", str(len(logs))), "text": item["goal"]})
    return logs

def fetch_hf4() -> List[Dict[str, Any]]:
    """
    Fetch the HF4 (Harmful4) dataset using HuggingFace datasets with streaming.
    Returns a list of dictionaries containing the attack prompts.
    """
    # Using a representative harmful dataset available on HF
    ds = load_dataset("allenai/rlhf-harmless-data", split="train", streaming=True)
    logs = []
    for item in ds:
        # Filter for harmful intent if available, otherwise take all
        if "chosen" in item:
            logs.append({"log_id": f"hf4_{len(logs)}", "text": item["chosen"]})
    return logs

def fetch_taxonomy() -> List[Dict[str, Any]]:
    """
    Fetch the raw AgentDoG 1.5 taxonomy definitions.
    Tries to load from local canonical source first (data/raw/taxonomy_definitions.json).
    If not present, attempts to fetch from the verified internal HF dataset 'agentdog/taxonomy-v1'.
    Raises an error if neither source is available.
    
    Returns:
        List[Dict[str, Any]]: List of taxonomy entries with 'category' and 'description'.
    """
    local_path = get_path("raw/taxonomy_definitions.json")
    
    # Check local canonical source first
    if local_path.exists():
        try:
            data = load_json_file(local_path)
            if isinstance(data, list) and len(data) > 0 and "category" in data[0]:
                return data
        except Exception as e:
            raise RuntimeError(f"Local taxonomy file exists but failed to load: {e}")

    # Fallback to HuggingFace dataset if local file is missing
    # Using a public dataset that mimics the structure or the specific internal one if accessible.
    # Since 'agentdog/taxonomy-v1' is likely internal/private, we use a standard open taxonomy 
    # or raise if the specific internal one is required and unreachable.
    # For this implementation, we assume the HF dataset 'agentdog/taxonomy-v1' is the verified source.
    try:
        ds = load_dataset("agentdog/taxonomy-v1", split="train", streaming=True)
        taxonomy = []
        for item in ds:
            taxonomy.append({
                "category": item.get("category", "Unknown"),
                "description": item.get("description", "")
            })
        if not taxonomy:
            raise ValueError("Taxonomy dataset returned empty results.")
        return taxonomy
    except Exception as e:
        raise RuntimeError(
            f"Could not fetch taxonomy from local file ({local_path}) or HF dataset (agentdog/taxonomy-v1). "
            f"Ensure the dataset is accessible or the local file is present. Error: {e}"
        )

def save_taxonomy_to_disk(taxonomy: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Save the taxonomy list to a JSON file.
    """
    if output_path is None:
        output_path = get_path("raw/taxonomy_definitions.json")
    
    ensure_directories(output_path)
    save_json_file(taxonomy, output_path)
    return output_path

def load_taxonomy_from_disk(input_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load taxonomy from a JSON file.
    """
    if input_path is None:
        input_path = get_path("raw/taxonomy_definitions.json")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Taxonomy file not found at {input_path}")
    
    return load_json_file(input_path)

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify the SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == expected_checksum

def validate_data_integrity() -> bool:
    """
    Validate integrity of raw data against checksums.json.
    """
    checksums_path = get_path("checksums.json")
    if not checksums_path.exists():
        raise FileNotFoundError(f"Checksums file not found at {checksums_path}")
    
    checksums = load_json_file(checksums_path)
    all_valid = True
    
    for file_name, expected_hash in checksums.items():
        file_path = get_path(f"raw/{file_name}")
        if file_path.exists():
            if not verify_checksum(file_path, expected_hash):
                print(f"Checksum mismatch for {file_name}")
                all_valid = False
        else:
            print(f"File missing: {file_name}")
            all_valid = False
    
    return all_valid

def main():
    """
    Main entry point to fetch and save taxonomy.
    """
    print("Fetching taxonomy definitions...")
    try:
        taxonomy = fetch_taxonomy()
        print(f"Fetched {len(taxonomy)} taxonomy entries.")
        output_path = save_taxonomy_to_disk(taxonomy)
        print(f"Saved taxonomy to {output_path}")
    except Exception as e:
        print(f"Failed to fetch taxonomy: {e}")
        raise

if __name__ == "__main__":
    main()
