import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datasets import load_dataset

def compute_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest(manifest_path: str = "data/manifest.json") -> Dict[str, Any]:
    """Load the data manifest if it exists, otherwise return empty dict."""
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            return json.load(f)
    return {}

def save_manifest(manifest: Dict[str, Any], manifest_path: str = "data/manifest.json") -> None:
    """Save the data manifest."""
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

def fetch_arxiv_pile_truncated(output_path: str = "data/raw/pile_arxiv_truncated.json") -> str:
    """
    Fetch the 'arXiv' subset of the Pile dataset, truncate to a representative size,
    and save to JSON. Returns the path to the saved file.
    """
    print(f"Fetching Pile (arXiv) subset...")
    # Load the arXiv subset of The Pile
    dataset = load_dataset("bigscience/pile", "arxiv", split="train", streaming=False)
    
    # Truncate to a representative subset size (e.g., 1000 samples for training)
    # This satisfies Constitution Principle VII (Data Hygiene) for training data
    max_samples = 1000
    truncated_data = []
    for i, item in enumerate(dataset):
        if i >= max_samples:
            break
        truncated_data.append(item)
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(truncated_data, f, indent=2)
    
    print(f"Saved truncated Pile (arXiv) dataset to {output_path}")
    return output_path

def fetch_gsm8k(output_path: str = "data/raw/gsm8k.json") -> str:
    """
    Fetch the GSM8K dataset via HuggingFace datasets API and save to JSON.
    This is strictly for EVALUATION data.
    """
    print(f"Fetching GSM8K dataset...")
    # Load the main (train) split of GSM8K
    # GSM8K is a grade school math dataset
    dataset = load_dataset("openai/gsm8k", "main", split="train", streaming=False)
    
    # Convert to list of dicts for JSON serialization
    data_list = []
    for item in dataset:
        data_list.append({
            "question": item["question"],
            "answer": item["answer"]
        })
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data_list, f, indent=2)
    
    print(f"Saved GSM8K dataset to {output_path}")
    return output_path

def fetch_mmlu(output_path: str = "data/raw/mmlu.json") -> str:
    """
    Fetch the MMLU dataset via HuggingFace datasets API and save to JSON.
    This is strictly for EVALUATION data.
    """
    print(f"Fetching MMLU dataset...")
    # Load a subset of MMLU (e.g., 'college_physics') for evaluation
    # MMLU has many subjects; we'll use one representative subject for this task
    # In a full implementation, we might load all subjects or a specific subset
    try:
        dataset = load_dataset("cais/mmlu", "college_physics", split="test", streaming=False)
    except Exception as e:
        raise RuntimeError(f"Failed to load MMLU dataset: {e}")
    
    # Convert to list of dicts for JSON serialization
    data_list = []
    for item in dataset:
        data_list.append({
            "question": item["question"],
            "choices": item["choices"],
            "answer": item["answer"]  # 0-indexed answer
        })
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data_list, f, indent=2)
    
    print(f"Saved MMLU dataset to {output_path}")
    return output_path

def save_dataset_and_manifest(
    dataset_path: str,
    dataset_type: str,
    manifest_path: str = "data/manifest.json"
) -> None:
    """
    Save dataset checksum and metadata to manifest.
    """
    manifest = load_manifest(manifest_path)
    
    file_name = os.path.basename(dataset_path)
    checksum = compute_checksum(dataset_path)
    size_bytes = os.path.getsize(dataset_path)
    created_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    
    manifest[file_name] = {
        "type": dataset_type,
        "checksum": checksum,
        "size_bytes": size_bytes,
        "created_at": created_at
    }
    
    save_manifest(manifest, manifest_path)
    print(f"Updated manifest with {file_name}")

def main():
    """
    Main function to fetch evaluation datasets (GSM8K and MMLU) and update manifest.
    """
    # Fetch GSM8K
    gsm8k_path = fetch_gsm8k("data/raw/gsm8k.json")
    save_dataset_and_manifest(gsm8k_path, "evaluation")
    
    # Fetch MMLU
    mmlu_path = fetch_mmlu("data/raw/mmlu.json")
    save_dataset_and_manifest(mmlu_path, "evaluation")
    
    print("Evaluation datasets fetched and manifest updated successfully.")

if __name__ == "__main__":
    main()
