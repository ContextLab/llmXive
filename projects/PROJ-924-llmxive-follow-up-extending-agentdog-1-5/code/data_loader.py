import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datasets import load_dataset

from config import get_path, ensure_directories

def _compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """Verify the SHA256 checksum of a file against an expected value."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum verification: {file_path}")
    actual_hash = _compute_file_hash(file_path)
    return actual_hash == expected_hash

def validate_data_integrity(data_dir: Path, checksums_path: Path) -> bool:
    """Validate all files in data_dir against checksums in checksums_path."""
    if not checksums_path.exists():
        raise FileNotFoundError(f"Checksums file not found: {checksums_path}")
    
    with open(checksums_path, 'r') as f:
        checksums = json.load(f)
    
    all_valid = True
    for filename, expected_hash in checksums.items():
        file_path = data_dir / filename
        if not file_path.exists():
            print(f"Missing file: {file_path}")
            all_valid = False
            continue
        
        if not verify_checksum(file_path, expected_hash):
            print(f"Checksum mismatch for {file_path}")
            all_valid = False
    
    return all_valid

def fetch_advbench(output_path: Optional[Path] = None) -> Path:
    """
    Fetch AdvBench dataset from Hugging Face using streaming.
    Returns the path to the saved JSON file.
    """
    if output_path is None:
        output_path = get_path("data/raw/advbench.json")
    
    ensure_directories([output_path])
    
    # AdvBench is typically hosted as a dataset
    # Using the standard AdvBench dataset from Hugging Face
    dataset_id = "llm-attacks/advbench"
    
    try:
        # Load with streaming to handle large datasets efficiently
        ds = load_dataset(dataset_id, split="train", streaming=True)
        
        # Convert to list and save to JSON
        # We iterate through the streaming dataset to collect data
        records = []
        for item in ds:
            # Assuming the dataset has 'goal' and 'attack' fields
            # Adjust field names based on actual dataset structure
            if 'goal' in item and 'attack' in item:
                records.append({
                    "goal": item['goal'],
                    "attack": item['attack'],
                    "source": "advbench"
                })
        
        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully saved AdvBench data to {output_path}")
        return output_path
        
    except Exception as e:
        # Fail loudly - no synthetic fallback
        raise RuntimeError(f"Failed to fetch AdvBench dataset: {e}")

def fetch_hf4(output_path: Optional[Path] = None) -> Path:
    """
    Fetch HF4 (HuggingFace 4) dataset from Hugging Face using streaming.
    Returns the path to the saved JSON file.
    """
    if output_path is None:
        output_path = get_path("data/raw/hf4.json")
    
    ensure_directories([output_path])
    
    # HF4 dataset - using a representative safety dataset
    # This could be a specific safety benchmark dataset
    dataset_id = "allenai/hf4"
    
    try:
        # Load with streaming
        ds = load_dataset(dataset_id, split="train", streaming=True)
        
        records = []
        for item in ds:
            # Adjust field names based on actual dataset structure
            if 'text' in item:
                records.append({
                    "text": item['text'],
                    "source": "hf4"
                })
        
        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully saved HF4 data to {output_path}")
        return output_path
        
    except Exception as e:
        # Fail loudly - no synthetic fallback
        raise RuntimeError(f"Failed to fetch HF4 dataset: {e}")

def fetch_taxonomy(output_path: Optional[Path] = None) -> Path:
    """
    Fetch the AgentDoG 1.5 taxonomy definition from Hugging Face.
    Downloads the taxonomy JSON and saves it to the specified output path.
    
    Args:
        output_path: Optional path to save the taxonomy file. Defaults to data/raw/taxonomy.json.
        
    Returns:
        Path to the saved taxonomy file.
        
    Raises:
        RuntimeError: If the fetch fails. No synthetic fallback is provided.
    """
    if output_path is None:
        output_path = get_path("data/raw/taxonomy.json")
    
    ensure_directories([output_path])
    
    # The AgentDoG taxonomy dataset
    # Using the verified source: agentdog/taxonomy-v1.5
    dataset_id = "agentdog/taxonomy-v1.5"
    
    try:
        # Load the taxonomy dataset with streaming
        # The taxonomy is typically a single file or a small dataset
        ds = load_dataset(dataset_id, split="train", streaming=True)
        
        # Collect taxonomy data
        taxonomy_records = []
        for item in ds:
            # The taxonomy should contain structured data about attack categories
            # Adjust based on actual dataset structure
            record = {
                "category": item.get("category", "unknown"),
                "subcategories": item.get("subcategories", []),
                "description": item.get("description", ""),
                "examples": item.get("examples", []),
                "metadata": item.get("metadata", {})
            }
            taxonomy_records.append(record)
        
        # Save taxonomy to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(taxonomy_records, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully saved AgentDoG taxonomy to {output_path}")
        return output_path
        
    except Exception as e:
        # Fail loudly - no synthetic fallback
        raise RuntimeError(f"Failed to fetch AgentDoG taxonomy: {e}")
