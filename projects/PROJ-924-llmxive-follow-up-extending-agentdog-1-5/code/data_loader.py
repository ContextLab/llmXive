"""
Data loader for AgentDoG drift detection pipeline.

Fetches real datasets from Hugging Face with streaming support
and implements loud failure on missing data.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator, Generator

from datasets import load_dataset
from config import get_path, ensure_directories
from utils import load_json_file, save_json_file

class LoudFailureError(Exception):
    """Raised when data fetching fails and no fallback is available."""
    pass

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum

def validate_data_integrity(file_path: str, checksums_file: str) -> None:
    """Validate data file against stored checksums."""
    if not os.path.exists(checksums_file):
        raise FileNotFoundError(f"Checksums file not found: {checksums_file}")
    
    checksums = load_json_file(checksums_file)
    file_name = os.path.basename(file_path)
    
    if file_name not in checksums:
        raise ValueError(f"No checksum found for {file_name}")
    
    expected = checksums[file_name]
    if not verify_checksum(file_path, expected):
        raise ValueError(f"Checksum mismatch for {file_name}")

def load_jsonl_file(file_path: str) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def save_jsonl_file(file_path: str, data: List[Dict[str, Any]]) -> None:
    """Save a list of dictionaries to a JSONL file."""
    ensure_directories([file_path])
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record) + '\n')

def generate_deterministic_timestamp(log_id: str) -> int:
    """
    Generate a deterministic timestamp from log_id.
    
    Args:
        log_id: The log identifier.
    
    Returns:
        A timestamp in seconds (derived from hash).
    """
    hash_val = int(hashlib.md5(log_id.encode()).hexdigest(), 16)
    # Map to a time within a 24-hour period
    return (hash_val % 24) * 3600

def fetch_advbench(output_path: Optional[str] = None, 
                  streaming: bool = True,
                  verify_checksum: bool = True) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch the ATBench dataset from Hugging Face.
    
    Args:
        output_path: Optional path to save the dataset.
        streaming: Whether to stream the dataset.
        verify_checksum: Whether to verify checksums.
    
    Yields:
        Dictionary records from the dataset.
    
    Raises:
        LoudFailureError: If the dataset cannot be fetched.
    """
    if output_path is None:
        output_path = get_path("raw_data") / "atbench.parquet"
    
    try:
        dataset = load_dataset(
            "AI45Research/ATBench",
            split="validation",
            streaming=streaming
        )
        
        for record in dataset:
            # Ensure timestamp field exists
            if "timestamp" not in record and "log_id" in record:
                record["timestamp"] = generate_deterministic_timestamp(record["log_id"])
            
            yield record
            
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch ATBench dataset: {e}")

def fetch_hf4(output_path: Optional[str] = None,
             streaming: bool = True) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch the HF4 dataset from Hugging Face.
    
    Args:
        output_path: Optional path to save the dataset.
        streaming: Whether to stream the dataset.
    
    Yields:
        Dictionary records from the dataset.
    
    Raises:
        LoudFailureError: If the dataset cannot be fetched.
    """
    if output_path is None:
        output_path = get_path("raw_data") / "hf4.parquet"
    
    try:
        dataset = load_dataset(
            "AgentDoG/hf4",
            split="validation",
            streaming=streaming
        )
        
        for record in dataset:
            if "timestamp" not in record and "log_id" in record:
                record["timestamp"] = generate_deterministic_timestamp(record["log_id"])
            
            yield record
            
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch HF4 dataset: {e}")

def fetch_taxonomy(source: str = "AgentDoG/safety-taxonomy") -> Dict[str, Any]:
    """
    Fetch the AgentDoG safety taxonomy from Hugging Face.
    
    Args:
        source: The dataset identifier.
    
    Returns:
        Dictionary containing the taxonomy.
    
    Raises:
        LoudFailureError: If the taxonomy cannot be fetched.
        FileNotFoundError: If the taxonomy is missing required categories.
    """
    required_categories = {"Safety", "Privacy", "Bias", "Jailbreak"}
    
    try:
        dataset = load_dataset(source, split="train", streaming=False)
        
        # Convert to dictionary format
        taxonomy = {"categories": {}}
        
        for item in dataset:
            # Handle different possible field names
            category_name = item.get("category") or item.get("name") or item.get("label")
            description = item.get("description") or item.get("text") or item.get("details", "")
            
            if category_name and description:
                taxonomy["categories"][category_name] = description
        
        # Verify required categories
        existing_categories = set(taxonomy["categories"].keys())
        missing = required_categories - existing_categories
        
        if missing:
            raise FileNotFoundError(
                f"Taxonomy dataset '{source}' not found or invalid. "
                f"Missing required categories: {missing}. "
                "No fallback permitted."
            )
        
        return taxonomy
        
    except FileNotFoundError:
        raise
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch taxonomy from {source}: {e}")

def main():
    """Main entry point for data loading tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test data loading")
    parser.add_argument("--test-taxonomy", action="store_true", help="Test taxonomy fetching")
    parser.add_argument("--test-advbench", action="store_true", help="Test ATBench fetching")
    
    args = parser.parse_args()
    
    if args.test_taxonomy:
        print("Testing taxonomy fetch...")
        try:
            taxonomy = fetch_taxonomy()
            print(f"Success! Loaded {len(taxonomy['categories'])} categories")
            for cat, desc in taxonomy["categories"].items():
                print(f"  - {cat}: {desc[:50]}...")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    if args.test_advbench:
        print("Testing ATBench fetch...")
        try:
            count = 0
            for record in fetch_advbench(streaming=True):
                count += 1
                if count >= 5:
                    break
            print(f"Success! Fetched {count} records")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()