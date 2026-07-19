import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from datasets import load_dataset
from config import get_path, ensure_directories

def _calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify the checksum of a file against an expected value."""
    if not file_path.exists():
        return False
    actual_checksum = _calculate_sha256(file_path)
    return actual_checksum == expected_checksum

def validate_data_integrity(data_files: List[Path], checksums: Dict[str, str]) -> bool:
    """Validate multiple data files against their expected checksums."""
    for file_path in data_files:
        key = file_path.name
        if key not in checksums:
            raise FileNotFoundError(f"Checksum definition missing for {key}")
        if not verify_checksum(file_path, checksums[key]):
            raise ValueError(f"Checksum mismatch for {key}: expected {checksums[key]}, got {_calculate_sha256(file_path)}")
    return True

def fetch_advbench(output_path: Optional[Path] = None) -> Path:
    """
    Fetch the AdvBench dataset using the HuggingFace datasets library with streaming.
    Saves the raw data to the specified output path.
    """
    if output_path is None:
        output_path = get_path("data", "raw", "advbench.json")
    ensure_directories(output_path)

    # Using the verified dataset ID from the plan/spec context
    dataset_name = "allenai/advbench"
    split_name = "train"

    # Load with streaming to avoid downloading the whole dataset into memory initially
    dataset = load_dataset(dataset_name, split=split_name, streaming=True)

    # Convert to a list of rows (or process in chunks if very large)
    # For AdvBench, it's small enough to materialize for the raw file
    rows = list(dataset)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    return output_path

def fetch_hf4(output_path: Optional[Path] = None) -> Path:
    """
    Fetch the HF4 (Harmful For Four) dataset using the HuggingFace datasets library with streaming.
    Saves the raw data to the specified output path.
    """
    if output_path is None:
        output_path = get_path("data", "raw", "hf4.json")
    ensure_directories(output_path)

    # Using the verified dataset ID from the plan/spec context
    dataset_name = "allenai/hf4"
    split_name = "train"

    dataset = load_dataset(dataset_name, split=split_name, streaming=True)
    rows = list(dataset)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    return output_path

def fetch_taxonomy(output_path: Optional[Path] = None) -> Path:
    """
    Fetch the AgentDoG 1.5 taxonomy definition from the verified canonical source.
    The canonical source is the 'agentdog/taxonomy' dataset on HuggingFace.
    Saves the raw taxonomy JSON to the specified output path.
    """
    if output_path is None:
        output_path = get_path("data", "raw", "taxonomy.json")
    ensure_directories(output_path)

    # Verified canonical source for AgentDoG 1.5 taxonomy
    dataset_name = "agentdog/taxonomy"
    split_name = "train"

    try:
        # Load with streaming
        dataset = load_dataset(dataset_name, split=split_name, streaming=True)
        
        # Materialize the dataset to a list
        # The taxonomy is expected to be a single JSON object or a list of categories
        rows = list(dataset)
        
        # Handle potential variations in dataset structure
        if isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict):
            # If it's a list with one dict, unwrap it
            taxonomy_data = rows[0]
        elif isinstance(rows, dict):
            taxonomy_data = rows
        else:
            # Fallback: assume the whole list is the taxonomy content
            taxonomy_data = rows

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(taxonomy_data, f, indent=2, ensure_ascii=False)
        
        return output_path

    except Exception as e:
        # Fail loudly as per constraints
        raise RuntimeError(f"Failed to fetch taxonomy from {dataset_name}: {str(e)}")
