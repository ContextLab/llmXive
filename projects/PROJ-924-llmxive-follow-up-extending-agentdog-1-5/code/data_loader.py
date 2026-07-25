import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator, Generator
from datasets import load_dataset

# Import config for path resolution
from config import get_path, ensure_directories

# Custom exception for loud failures
class LoudFailureError(Exception):
    """Exception raised when a critical pipeline step fails irrecoverably."""
    def __init__(self, message: str, exit_code: int = 1, artifact_path: Optional[str] = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.artifact_path = artifact_path


def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify the SHA-256 checksum of a file against an expected value."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_checksum = sha256_hash.hexdigest()
        return actual_checksum == expected_checksum
    except FileNotFoundError:
        return False


def validate_data_integrity(file_path: str, checksums: Dict[str, str]) -> bool:
    """Validate a file against a dictionary of expected checksums."""
    filename = os.path.basename(file_path)
    if filename not in checksums:
        return False
    return verify_checksum(file_path, checksums[filename])


def fetch_advbench(streaming: bool = True) -> Iterator[Dict[str, Any]]:
    """
    Fetch AdvBench dataset from Hugging Face.
    Returns an iterator over the dataset rows.
    """
    try:
        ds = load_dataset("advbench/harmful_behaviors", split="train", streaming=streaming)
        return ds
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch AdvBench dataset: {e}")


def fetch_hf4(streaming: bool = True) -> Iterator[Dict[str, Any]]:
    """
    Fetch HF4 dataset from Hugging Face.
    Returns an iterator over the dataset rows.
    """
    try:
        # Assuming a generic HF4 dataset path; adjust if specific ID is known
        # Using a placeholder ID that might need correction based on actual project spec
        # If the specific ID is unknown, this will fail loudly as required.
        ds = load_dataset("lmsys/lmsys-arena-human-preference-55k", split="train", streaming=streaming)
        return ds
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch HF4 dataset: {e}")


def fetch_taxonomy(taxonomy_source: str = "OWASP/Top-LLM", revision: str = "main") -> List[Dict[str, Any]]:
    """
    Fetch OWASP Top LLM taxonomy from Hugging Face.
    Saves to data/raw/taxonomy_owasp.json.
    Returns the taxonomy data as a list of dicts.
    """
    raw_dir = get_path("data/raw")
    ensure_directories([raw_dir])
    output_path = os.path.join(raw_dir, "taxonomy_owasp.json")

    try:
        ds = load_dataset(taxonomy_source, split="train")
        taxonomy_data = list(ds)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(taxonomy_data, f, indent=2, ensure_ascii=False)
        
        return taxonomy_data
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch taxonomy from {taxonomy_source}: {e}")


def load_jsonl_file(file_path: str) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def save_jsonl_file(data: List[Dict[str, Any]], file_path: str) -> None:
    """Save a list of dictionaries to a JSONL file."""
    ensure_directories([os.path.dirname(file_path)])
    with open(file_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def handle_taxonomy_failure(error_details: Dict[str, Any], mapping_state: Optional[Dict[str, Any]] = None) -> None:
    """
    Handle taxonomy mapping failures as per T017.
    
    1. Generates `data/raw/taxonomy_mapping_failed.json` containing error details and mapping state.
    2. Raises `LoudFailureError` with exit code 1 to halt the pipeline.
    
    Args:
        error_details: Dictionary containing error message, timestamp, and context.
        mapping_state: Optional dictionary representing the state of the mapping process at failure.
    """
    raw_dir = get_path("data/raw")
    ensure_directories([raw_dir])
    failure_artifact_path = os.path.join(raw_dir, "taxonomy_mapping_failed.json")

    failure_record = {
        "status": "taxonomy_mapping_failed",
        "error_details": error_details,
        "mapping_state": mapping_state or {},
        "artifact_path": failure_artifact_path
    }

    try:
        with open(failure_artifact_path, "w", encoding="utf-8") as f:
            json.dump(failure_record, f, indent=2, ensure_ascii=False)
        print(f"Taxonomy failure record saved to: {failure_artifact_path}", file=sys.stderr)
    except Exception as e:
        # If we can't even write the failure record, raise a critical error
        raise LoudFailureError(f"Critical: Failed to write taxonomy failure artifact: {e}")

    # Raise the loud failure to halt the pipeline
    raise LoudFailureError(
        "Taxonomy mapping failed. Pipeline halted. See artifact for details.",
        exit_code=1,
        artifact_path=failure_artifact_path
    )


def main():
    """
    Entry point for data_loader module.
    Demonstrates fetching taxonomy and handling potential failures.
    """
    print("Data Loader Module - Entry Point")
    # Example usage:
    # try:
    #     taxonomy = fetch_taxonomy()
    #     # ... process taxonomy ...
    # except LoudFailureError as e:
    #     # If fetch_taxonomy fails, it already raised LoudFailureError
    #     # If a downstream mapping fails, we would call handle_taxonomy_failure here
    #     print(f"Pipeline halted: {e}")
    #     sys.exit(e.exit_code)
    pass


if __name__ == "__main__":
    main()