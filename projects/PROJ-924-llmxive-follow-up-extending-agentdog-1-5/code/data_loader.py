"""
data_loader.py

Implements data fetching functions for AdvBench and HF4 datasets using
streaming to minimize memory footprint. Enforces strict failure on data
fetch errors without synthetic fallbacks.
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
    """Exception raised when a data fetch fails. Does not allow silent fallback."""
    pass


def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verify the checksum of a file against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected checksum string.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        True if checksum matches, False otherwise.
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest() == expected_checksum


def validate_data_integrity(data_dir: Path, checksums_file: Path) -> bool:
    """
    Validate all raw data files against their stored checksums.
    
    Args:
        data_dir: Directory containing raw data files.
        checksums_file: Path to the JSON file containing checksums.
        
    Returns:
        True if all files are valid, raises LoudFailureError otherwise.
    """
    if not checksums_file.exists():
        raise LoudFailureError(f"Checksums file not found: {checksums_file}")
        
    checksums = load_json_file(checksums_file)
    all_valid = True
    
    for filename, expected in checksums.items():
        file_path = data_dir / filename
        if not file_path.exists():
            raise LoudFailureError(f"Missing raw data file: {file_path}")
            
        if not verify_checksum(str(file_path), expected):
            raise LoudFailureError(f"Checksum mismatch for {filename}")
            
    return True


def load_jsonl_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load a JSONL file into a list of dictionaries.
    
    Args:
        file_path: Path to the JSONL file.
        
    Returns:
        List of dictionaries.
    """
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def save_jsonl_file(data: List[Dict[str, Any]], file_path: Path) -> None:
    """
    Save a list of dictionaries to a JSONL file.
    
    Args:
        data: List of dictionaries to save.
        file_path: Path to the output JSONL file.
    """
    ensure_directories(file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")


def fetch_advbench(output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Fetch the AdvBench dataset using streaming.
    
    This function loads the AdvBench dataset from Hugging Face Hub.
    It uses streaming to avoid loading the entire dataset into memory.
    The data is then saved to a local JSONL file for subsequent processing.
    
    Args:
        output_path: Optional path to save the fetched data. If None, uses
                    the default path from config.
                    
    Returns:
        List of dictionaries containing the AdvBench data.
        
    Raises:
        LoudFailureError: If the dataset cannot be fetched or processed.
    """
    try:
        # Load dataset with streaming to minimize memory usage
        # AdvBench is typically small enough, but streaming is safer
        dataset = load_dataset("llm-attacks/advbench", split="train", streaming=True)
        
        # Convert to list (AdvBench is small, ~500 entries)
        data = list(dataset)
        
        if not data:
            raise LoudFailureError("AdvBench dataset is empty")
            
        # Ensure output path
        if output_path is None:
            output_path = get_path("raw") / "advbench.jsonl"
        else:
            output_path = Path(output_path)
            
        ensure_directories(output_path)
        
        # Save to JSONL
        save_jsonl_file(data, output_path)
        
        return data
        
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch AdvBench dataset: {str(e)}")


def fetch_hf4(output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Fetch the HF4 (Harmful4) dataset using streaming.
    
    This function loads the HF4 dataset from Hugging Face Hub.
    It uses streaming to avoid loading the entire dataset into memory.
    The data is then saved to a local JSONL file for subsequent processing.
    
    Args:
        output_path: Optional path to save the fetched data. If None, uses
                    the default path from config.
                    
    Returns:
        List of dictionaries containing the HF4 data.
        
    Raises:
        LoudFailureError: If the dataset cannot be fetched or processed.
    """
    try:
        # Load dataset with streaming
        # Using a known safe dataset ID for benign logs
        # Note: Adjust dataset name based on actual availability
        dataset = load_dataset("AgentDoG/harmless_logs_hf4", split="train", streaming=True)
        
        # Convert to list
        data = list(dataset)
        
        if not data:
            raise LoudFailureError("HF4 dataset is empty")
            
        # Ensure output path
        if output_path is None:
            output_path = get_path("raw") / "hf4.jsonl"
        else:
            output_path = Path(output_path)
            
        ensure_directories(output_path)
        
        # Save to JSONL
        save_jsonl_file(data, output_path)
        
        return data
        
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch HF4 dataset: {str(e)}")


def fetch_taxonomy(output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Fetch the AgentDoG safety taxonomy dataset.
    
    This function loads the safety taxonomy from Hugging Face Hub.
    
    Args:
        output_path: Optional path to save the fetched taxonomy.
                    
    Returns:
        List of dictionaries containing the taxonomy data.
        
    Raises:
        LoudFailureError: If the taxonomy cannot be fetched.
    """
    try:
        # Load taxonomy dataset
        dataset = load_dataset("AgentDoG/safety-taxonomy-v1.5", split="train", streaming=True)
        data = list(dataset)
        
        if not data:
            raise LoudFailureError("Taxonomy dataset is empty")
            
        if output_path is None:
            output_path = get_path("raw") / "taxonomy_agentdog.json"
        else:
            output_path = Path(output_path)
            
        ensure_directories(output_path)
        
        # Save as JSON (not JSONL) since it's a taxonomy structure
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        return data
        
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch taxonomy: {str(e)}")


def handle_taxonomy_failure(error: LoudFailureError) -> None:
    """
    Handle taxonomy fetch failure by logging and raising.
    
    Args:
        error: The LoudFailureError instance.
    """
    # Log the error
    sys.stderr.write(f"Taxonomy fetch failed: {str(error)}\n")
    # Re-raise to ensure pipeline fails loudly
    raise error


def main() -> None:
    """
    Main function to run data loading for testing.
    """
    print("Starting data loader...")
    
    # Fetch AdvBench
    try:
        advbench_data = fetch_advbench()
        print(f"Successfully fetched {len(advbench_data)} AdvBench entries")
    except LoudFailureError as e:
        print(f"AdvBench fetch failed: {e}")
        sys.exit(1)
        
    # Fetch HF4
    try:
        hf4_data = fetch_hf4()
        print(f"Successfully fetched {len(hf4_data)} HF4 entries")
    except LoudFailureError as e:
        print(f"HF4 fetch failed: {e}")
        sys.exit(1)
        
    print("Data loading complete.")


if __name__ == "__main__":
    main()
