import hashlib
import json
import os
from pathlib import Path
from datasets import load_dataset

# Ensure config is imported correctly if needed, though T004b focuses on data fetching
# The task requires fetching GSM8K and MMLU via HuggingFace datasets API

def compute_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_gsm8k(output_path: str) -> str:
    """
    Fetch the GSM8K dataset from HuggingFace and save it to the specified path.
    Returns the checksum of the saved file.
    """
    print("Fetching GSM8K dataset...")
    dataset = load_dataset("gsm8k", "main")
    
    # Convert to a list of dicts for JSON serialization
    # GSM8K has 'train' and 'test' splits
    data = {
        "train": list(dataset["train"]),
        "test": list(dataset["test"])
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    checksum = compute_checksum(output_path)
    print(f"GSM8K saved to {output_path} with checksum: {checksum}")
    return checksum

def fetch_mmlu(output_path: str) -> str:
    """
    Fetch the MMLU dataset from HuggingFace and save it to the specified path.
    Returns the checksum of the saved file.
    """
    print("Fetching MMLU dataset...")
    # MMLU is a large dataset, we fetch the 'auxiliary_train' or 'dev'/'test' splits.
    # The standard way is to load the dataset and select the 'test' split for evaluation.
    # We will load the full dataset and save the 'test' split as per evaluation needs.
    dataset = load_dataset("cais/mmlu")
    
    # MMLU has many categories. We aggregate them into a single list for simplicity in this context,
    # or save the structure as is. The task asks for saving to a single JSON file.
    # We'll flatten the test split across all subjects.
    test_data = []
    for subject in dataset["test"].features.keys():
        # Actually, the dataset structure is usually a dict of splits, each split has multiple subjects.
        # Let's inspect the structure: load_dataset("cais/mmlu") returns a DatasetDict.
        # The 'test' key contains a dataset with columns: question, choices, answer, subject.
        # We iterate over the 'test' split.
        pass
    
    # Re-loading with specific split handling for MMLU
    # The dataset "cais/mmlu" has splits: ['auxiliary_train', 'dev', 'test', 'validation']
    # We want the 'test' split for evaluation.
    mmlu_dataset = load_dataset("cais/mmlu")
    test_split = mmlu_dataset["test"]
    
    # Convert to list of dicts
    data = list(test_split)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    checksum = compute_checksum(output_path)
    print(f"MMLU saved to {output_path} with checksum: {checksum}")
    return checksum

def save_dataset_and_manifest(gsm8k_path: str, mmlu_path: str, manifest_path: str, gsm8k_checksum: str, mmlu_checksum: str):
    """
    Update the manifest.json file with checksums for the new datasets.
    """
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    
    manifest["gsm8k"] = {
        "path": gsm8k_path,
        "checksum": gsm8k_checksum,
        "purpose": "evaluation"
    }
    manifest["mmlu"] = {
        "path": mmlu_path,
        "checksum": mmlu_checksum,
        "purpose": "evaluation"
    }
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest updated at {manifest_path}")

def main():
    """
    Main function to fetch GSM8K and MMLU datasets and update the manifest.
    """
    base_dir = Path(__file__).parent.parent
    data_raw_dir = base_dir / "data" / "raw"
    manifest_path = base_dir / "data" / "manifest.json"
    
    gsm8k_output = str(data_raw_dir / "gsm8k.json")
    mmlu_output = str(data_raw_dir / "mmlu.json")
    
    # Fetch datasets
    gsm8k_checksum = fetch_gsm8k(gsm8k_output)
    mmlu_checksum = fetch_mmlu(mmlu_output)
    
    # Update manifest
    save_dataset_and_manifest(gsm8k_output, mmlu_output, str(manifest_path), gsm8k_checksum, mmlu_checksum)

if __name__ == "__main__":
    main()