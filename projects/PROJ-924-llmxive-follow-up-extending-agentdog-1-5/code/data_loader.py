import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator, Generator

from datasets import load_dataset
from config import get_path, ensure_directories

class LoudFailureError(Exception):
    """Custom exception for loud failures in data loading."""
    pass

def compute_sha256(file_path: str) -> str:
    """Compute the SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verify the checksum of a file against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected checksum string.
        algorithm: The hashing algorithm to use (default: sha256).
        
    Returns:
        True if checksum matches, False otherwise.
        
    Raises:
        LoudFailureError: If the file does not exist or checksum mismatch occurs.
    """
    if not os.path.exists(file_path):
        raise LoudFailureError(f"File not found for checksum verification: {file_path}")
    
    if algorithm == "sha256":
        actual_checksum = compute_sha256(file_path)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    if actual_checksum != expected_checksum:
        raise LoudFailureError(
            f"Checksum mismatch for {file_path}:\n"
            f"  Expected: {expected_checksum}\n"
            f"  Actual:   {actual_checksum}"
        )
    
    return True

def validate_data_integrity(file_paths: List[str], checksum_file: Optional[str] = None) -> Dict[str, bool]:
    """
    Validate the integrity of multiple files against a checksums JSON file.
    
    Args:
        file_paths: List of file paths to validate.
        checksum_file: Path to the checksums.json file. Defaults to data/checksums.json.
        
    Returns:
        Dictionary mapping file paths to validation status (True/False).
        
    Raises:
        LoudFailureError: If any file fails validation or checksum file is missing.
    """
    if checksum_file is None:
        checksum_file = str(get_path("data", "checksums.json"))
    
    if not os.path.exists(checksum_file):
        raise LoudFailureError(f"Checksum file not found: {checksum_file}")
    
    with open(checksum_file, "r", encoding="utf-8") as f:
        checksum_data = json.load(f)
    
    algorithm = checksum_data.get("algorithm", "sha256")
    files_checksums = checksum_data.get("files", {})
    
    validation_results = {}
    
    for file_path in file_paths:
        if file_path not in files_checksums:
            raise LoudFailureError(f"No checksum registered for: {file_path}")
        
        expected_checksum = files_checksums[file_path]
        
        try:
            verify_checksum(file_path, expected_checksum, algorithm)
            validation_results[file_path] = True
        except LoudFailureError as e:
            # Re-raise immediately on failure to ensure loud failure
            raise e
    
    return validation_results

def load_jsonl_file(file_path: str) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    if not os.path.exists(file_path):
        raise LoudFailureError(f"JSONL file not found: {file_path}")
    
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise LoudFailureError(f"Invalid JSON on line {line_num} in {file_path}: {e}")
    
    return data

def save_jsonl_file(data: List[Dict[str, Any]], file_path: str) -> None:
    """Save a list of dictionaries to a JSONL file."""
    ensure_directories(file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        for record in data:
            f.write(json.dumps(record) + "\n")

def generate_deterministic_timestamp(log_id: str) -> str:
    """
    Generate a deterministic timestamp based on log_id.
    Uses hash of log_id to create a varied timestamp within a year range.
    
    Args:
        log_id: The unique identifier for the log record.
        
    Returns:
        ISO format timestamp string.
    """
    import hashlib
    import datetime
    
    # Hash the log_id to get a deterministic integer
    hash_obj = hashlib.sha256(log_id.encode('utf-8'))
    hash_int = int(hash_obj.hexdigest(), 16)
    
    # Use a base date (e.g., 2023-01-01) and add a deterministic number of days
    base_date = datetime.datetime(2023, 1, 1)
    # Use modulo to get days within a year range (365 days)
    days_offset = hash_int % 365
    
    # Generate the timestamp
    timestamp = base_date + datetime.timedelta(days=days_offset)
    
    return timestamp.isoformat()

def fetch_advbench() -> Generator[Dict[str, Any], None, None]:
    """
    Fetch AdvBench dataset using streaming.
    
    Yields:
        Dictionary records from the AdvBench dataset.
        
    Raises:
        LoudFailureError: If dataset fetch fails.
    """
    try:
        dataset = load_dataset("llm-attacks/advbench", split="train", streaming=True)
        for record in dataset:
            yield record
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch AdvBench dataset: {e}")

def fetch_hf4() -> Generator[Dict[str, Any], None, None]:
    """
    Fetch HF4 dataset using streaming.
    
    Yields:
        Dictionary records from the HF4 dataset.
        
    Raises:
        LoudFailureError: If dataset fetch fails.
    """
    try:
        # Assuming HF4 is available as a dataset; adjust dataset name if different
        dataset = load_dataset("llm-attacks/hf4", split="train", streaming=True)
        for record in dataset:
            yield record
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch HF4 dataset: {e}")

def fetch_taxonomy() -> List[Dict[str, Any]]:
    """
    Fetch the fixed AgentDoG safety taxonomy.
    
    Returns:
        List of taxonomy entries.
        
    Raises:
        LoudFailureError: If taxonomy fetch fails.
    """
    try:
        # Placeholder for taxonomy fetch; adjust based on actual source
        # This could be a URL or a specific dataset
        raise LoudFailureError("Taxonomy fetch not yet implemented for this task")
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch taxonomy: {e}")

def main():
    """Main entry point for data loader module."""
    print("Data loader module loaded successfully.")
    print("Available functions: compute_sha256, verify_checksum, validate_data_integrity, load_jsonl_file, save_jsonl_file")

if __name__ == "__main__":
    main()
