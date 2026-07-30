"""
Data loading module for AdvBench and HF4 datasets.
Implements streaming fetch with loud failure on errors.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator, Generator

from datasets import load_dataset
from config import get_path, get_output_path, ensure_directories


class LoudFailureError(Exception):
    """Custom exception for loud failure when data fetch fails."""
    pass


def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify the SHA-256 checksum of a file against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected SHA-256 hex digest.
        
    Returns:
        True if checksum matches, False otherwise.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_checksum = sha256_hash.hexdigest()
        return actual_checksum == expected_checksum
    except FileNotFoundError:
        return False
    except Exception as e:
        raise LoudFailureError(f"Error verifying checksum for {file_path}: {e}")


def validate_data_integrity(file_path: str, checksums_file: str) -> bool:
    """
    Validate a file's checksum against a checksums JSON file.
    
    Args:
        file_path: Path to the file to validate.
        checksums_file: Path to the checksums JSON file.
        
    Returns:
        True if validation passes, False otherwise.
    """
    if not os.path.exists(checksums_file):
        raise LoudFailureError(f"Checksums file not found: {checksums_file}")
    
    with open(checksums_file, 'r') as f:
        checksums = json.load(f)
    
    file_name = os.path.basename(file_path)
    if file_name not in checksums:
        raise LoudFailureError(f"No checksum found for {file_name} in {checksums_file}")
    
    expected = checksums[file_name]
    return verify_checksum(file_path, expected)


def load_jsonl_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load a JSONL file into a list of dictionaries.
    
    Args:
        file_path: Path to the JSONL file.
        
    Returns:
        List of dictionaries representing each line.
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise LoudFailureError(f"Invalid JSON at line {line_num} in {file_path}: {e}")
    return data


def save_jsonl_file(data: List[Dict[str, Any]], file_path: str) -> None:
    """
    Save a list of dictionaries to a JSONL file.
    
    Args:
        data: List of dictionaries to save.
        file_path: Path to the output JSONL file.
    """
    ensure_directories(file_path)
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')


def fetch_advbench() -> Generator[Dict[str, Any], None, None]:
    """
    Fetch AdvBench dataset using HuggingFace datasets with streaming.
    
    Returns:
        Generator yielding dictionaries with 'text' and 'label' keys.
        
    Raises:
        LoudFailureError: If the dataset cannot be fetched.
    """
    try:
        # AdvBench is available via the 'llm-attacks/advbench' dataset on HuggingFace
        # We stream it to avoid loading entire dataset into memory
        dataset = load_dataset(
            "llm-attacks/advbench",
            split="train",
            streaming=True
        )
        
        for item in dataset:
            # Normalize the item to expected schema
            # AdvBench typically has 'prompt' or 'text' and 'label'
            text = item.get('prompt') or item.get('text') or ""
            label = item.get('label', 'attack')  # AdvBench is attack data
            
            yield {
                "text": text,
                "label": label,
                "source": "advbench"
            }
            
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch AdvBench dataset: {e}")


def fetch_hf4() -> Generator[Dict[str, Any], None, None]:
    """
    Fetch HF4 dataset using HuggingFace datasets with streaming.
    
    Returns:
        Generator yielding dictionaries with 'text' and 'label' keys.
        
    Raises:
        LoudFailureError: If the dataset cannot be fetched.
    """
    try:
        # HF4 is available via 'AgentDoG/hf4' dataset on HuggingFace
        # This dataset contains benign/safe logs
        dataset = load_dataset(
            "AgentDoG/hf4",
            split="train",
            streaming=True
        )
        
        for item in dataset:
            # Normalize the item to expected schema
            text = item.get('text') or item.get('prompt') or ""
            label = item.get('label', 'safe')  # HF4 is safe/benign data
            
            yield {
                "text": text,
                "label": label,
                "source": "hf4"
            }
            
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch HF4 dataset: {e}")


def fetch_taxonomy() -> Dict[str, Any]:
    """
    Fetch the safety taxonomy from HuggingFace.
    
    Returns:
        Dictionary containing taxonomy data.
        
    Raises:
        LoudFailureError: If the taxonomy cannot be fetched.
    """
    try:
        # The taxonomy is stored as a JSON file in the AgentDoG/safety-taxonomy-v1.5 dataset
        dataset = load_dataset(
            "AgentDoG/safety-taxonomy-v1.5",
            split="train",
            streaming=True
        )
        
        taxonomy_data = []
        for item in dataset:
            taxonomy_data.append(item)
        
        if not taxonomy_data:
            raise LoudFailureError("Taxonomy dataset is empty")
        
        return {
            "categories": taxonomy_data,
            "source": "AgentDoG/safety-taxonomy-v1.5"
        }
        
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch taxonomy: {e}")


def main():
    """
    Main function to demonstrate data loading.
    Fetches a small sample of each dataset and prints statistics.
    """
    print("Testing AdvBench fetch...")
    try:
        advbench_count = 0
        for item in fetch_advbench():
            advbench_count += 1
            if advbench_count >= 5:  # Just sample first 5
                break
        print(f"  Successfully fetched {advbench_count} AdvBench samples")
    except LoudFailureError as e:
        print(f"  ERROR: {e}")
        sys.exit(1)
    
    print("Testing HF4 fetch...")
    try:
        hf4_count = 0
        for item in fetch_hf4():
            hf4_count += 1
            if hf4_count >= 5:  # Just sample first 5
                break
        print(f"  Successfully fetched {hf4_count} HF4 samples")
    except LoudFailureError as e:
        print(f"  ERROR: {e}")
        sys.exit(1)
    
    print("All data fetch tests passed!")


if __name__ == "__main__":
    main()
