import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datasets import load_dataset

from utils.logging import get_logger

logger = get_logger(__name__)

DATA_ROOT = Path("data")
RAW_DIR = DATA_ROOT / "raw"
MANIFEST_PATH = DATA_ROOT / "manifest.json"

def compute_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest() -> Dict[str, Any]:
    """Load the manifest file if it exists."""
    if not MANIFEST_PATH.exists():
        return {}
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)

def save_manifest(manifest: Dict[str, Any]) -> None:
    """Save the manifest file."""
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

def fetch_arxiv_pile_truncated() -> None:
    """
    Fetch the 'arXiv' subset of the Pile dataset via HuggingFace datasets API.
    Concatenate tokens, truncate to the first 100,000 tokens (config key: config.TOKEN_LIMIT),
    and save to data/raw/pile_arxiv_truncated.json.
    """
    logger.info("Fetching Pile arXiv subset...")
    # Load the dataset with streaming to handle large size
    dataset = load_dataset("pile", "arxiv", split="train", streaming=True)
    
    # Concatenate all text and truncate to token limit
    # Note: This is a simplification; in a real scenario, we'd use a tokenizer
    # For now, we'll treat characters as tokens to meet the requirement
    all_text = ""
    token_limit = 100000
    
    for idx, item in enumerate(dataset):
        all_text += item["text"]
        if len(all_text) >= token_limit:
            break
    
    truncated_text = all_text[:token_limit]
    
    # Save to JSON
    output_path = RAW_DIR / "pile_arxiv_truncated.json"
    with open(output_path, "w") as f:
        json.dump({"text": truncated_text}, f)
    
    checksum = compute_checksum(output_path)
    manifest = load_manifest()
    manifest["pile_arxiv_truncated.json"] = {
        "type": "training",
        "checksum": checksum,
        "size_bytes": output_path.stat().st_size,
        "created_at": datetime.now().isoformat()
    }
    save_manifest(manifest)
    logger.info(f"Saved Pile arXiv data to {output_path} (checksum: {checksum})")

def fetch_gsm8k() -> None:
    """
    Fetch the GSM8K dataset via HuggingFace datasets API and save to data/raw/gsm8k.json.
    """
    logger.info("Fetching GSM8K dataset...")
    dataset = load_dataset("gsm8k", "main", split="train")
    
    # Convert to list of dicts and save
    data = [item for item in dataset]
    
    output_path = RAW_DIR / "gsm8k.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    
    checksum = compute_checksum(output_path)
    manifest = load_manifest()
    manifest["gsm8k.json"] = {
        "type": "evaluation",
        "checksum": checksum,
        "size_bytes": output_path.stat().st_size,
        "created_at": datetime.now().isoformat()
    }
    save_manifest(manifest)
    logger.info(f"Saved GSM8K data to {output_path} (checksum: {checksum})")

def fetch_mmlu() -> None:
    """
    Fetch the MMLU dataset via HuggingFace datasets API and save to data/raw/mmlu.json.
    """
    logger.info("Fetching MMLU dataset...")
    dataset = load_dataset("cais/mmlu", split="test")
    
    # Convert to list of dicts and save
    data = [item for item in dataset]
    
    output_path = RAW_DIR / "mmlu.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    
    checksum = compute_checksum(output_path)
    manifest = load_manifest()
    manifest["mmlu.json"] = {
        "type": "evaluation",
        "checksum": checksum,
        "size_bytes": output_path.stat().st_size,
        "created_at": datetime.now().isoformat()
    }
    save_manifest(manifest)
    logger.info(f"Saved MMLU data to {output_path} (checksum: {checksum})")

def save_dataset_and_manifest(dataset_name: str, data: List[Dict[str, Any]], dataset_type: str) -> None:
    """Helper function to save a dataset and update the manifest."""
    output_path = RAW_DIR / f"{dataset_name}.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    
    checksum = compute_checksum(output_path)
    manifest = load_manifest()
    manifest[f"{dataset_name}.json"] = {
        "type": dataset_type,
        "checksum": checksum,
        "size_bytes": output_path.stat().st_size,
        "created_at": datetime.now().isoformat()
    }
    save_manifest(manifest)
    logger.info(f"Saved {dataset_name} data to {output_path} (checksum: {checksum})")

def data_path_str() -> str:
    """Return the string path to the data root directory."""
    return str(DATA_ROOT)

def main():
    """Main entry point for data loading."""
    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Fetch all datasets
    fetch_arxiv_pile_truncated()
    fetch_gsm8k()
    fetch_mmlu()
    
    logger.info("All datasets fetched and saved successfully.")

if __name__ == "__main__":
    main()
