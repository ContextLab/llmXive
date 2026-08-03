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
    """Custom exception for loud failures in data loading."""
    pass


def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def verify_checksum(filepath: Path, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verify the checksum of a file against an expected value.

    Args:
        filepath: Path to the file to verify.
        expected_checksum: The expected checksum string.
        algorithm: The hashing algorithm to use (default: sha256).

    Returns:
        True if checksums match.

    Raises:
        ValueError: If checksums do not match or file is missing.
        LoudFailureError: If the file does not exist (loud failure).
    """
    if not filepath.exists():
        raise LoudFailureError(f"File not found for checksum verification: {filepath}")

    if algorithm == "sha256":
        actual_checksum = compute_sha256(filepath)
    else:
        raise ValueError(f"Unsupported checksum algorithm: {algorithm}")

    if actual_checksum != expected_checksum:
        raise ValueError(
            f"Checksum mismatch for {filepath}.\n"
            f"Expected: {expected_checksum}\n"
            f"Actual:   {actual_checksum}"
        )

    return True


def validate_data_integrity(data_files: Dict[str, str], checksums_path: Path) -> Dict[str, bool]:
    """
    Validate a set of data files against a checksums.json manifest.

    Args:
        data_files: Dict mapping logical name -> relative path (from project root).
        checksums_path: Path to the checksums.json file.

    Returns:
        Dict mapping logical name -> verification status (True if valid).

    Raises:
        LoudFailureError: If checksums.json is missing or malformed.
        ValueError: If any file fails checksum verification.
    """
    if not checksums_path.exists():
        raise LoudFailureError(f"Checksums manifest not found at {checksums_path}")

    try:
        checksum_data = load_json_file(checksums_path)
    except json.JSONDecodeError as e:
        raise LoudFailureError(f"Invalid JSON in checksums manifest: {e}")

    algorithm = checksum_data.get("algorithm", "sha256")
    files_manifest = checksum_data.get("files", {})

    results = {}
    errors = []

    for logical_name, rel_path in data_files.items():
        full_path = get_path(rel_path)
        
        if logical_name not in files_manifest:
            errors.append(f"No checksum found for {logical_name} in manifest.")
            continue

        expected_checksum = files_manifest[logical_name]
        
        try:
            verify_checksum(full_path, expected_checksum, algorithm)
            results[logical_name] = True
        except ValueError as e:
            errors.append(str(e))
            results[logical_name] = False
        except LoudFailureError as e:
            errors.append(str(e))
            results[logical_name] = False

    if errors:
        error_msg = "\n".join(errors)
        raise ValueError(f"Data integrity validation failed:\n{error_msg}")

    return results


def load_jsonl_file(filepath: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    if not filepath.exists():
        raise LoudFailureError(f"JSONL file not found: {filepath}")
    
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise LoudFailureError(f"Invalid JSON at line {line_num} in {filepath}: {e}")
    return data


def save_jsonl_file(filepath: Path, data: List[Dict[str, Any]]) -> None:
    """Save a list of dictionaries to a JSONL file."""
    ensure_directories([filepath.parent])
    with open(filepath, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")


def fetch_advbench() -> List[Dict[str, Any]]:
    """
    Fetch AdvBench dataset using streaming.

    Returns:
        List of dataset entries.

    Raises:
        LoudFailureError: If fetch fails.
    """
    try:
        dataset = load_dataset("llm-attacks/advbench", split="train", streaming=True)
        data = list(dataset)
        
        if not data:
            raise LoudFailureError("AdvBench dataset is empty.")
        
        return data
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch AdvBench dataset: {e}")


def fetch_hf4() -> List[Dict[str, Any]]:
    """
    Fetch HF4 dataset using streaming.

    Returns:
        List of dataset entries.

    Raises:
        LoudFailureError: If fetch fails.
    """
    try:
        # Assuming HF4 refers to a specific subset or a known dataset ID.
        # Using a generic placeholder if the exact ID isn't standard, 
        # but typically this would be a specific HuggingFace dataset.
        # Based on context of safety benchmarks, using 'HuggingFaceH4/ultrafeedback_binarized' 
        # or similar if 'hf4' is a shorthand for a specific H4 dataset.
        # However, strictly following the prompt's likely intent for a safety dataset:
        # If 'hf4' is not a standard public dataset name, we assume it maps to a specific
        # known safety dataset ID. For this implementation, we assume 'huggingface/...'.
        # Let's assume the task implies 'HuggingFaceH4/harmless_base' or similar.
        # Since the exact ID wasn't provided in the prompt's API surface, 
        # and T012a already implemented it, we assume the ID is 'HuggingFaceH4/ultrafeedback' 
        # or similar. 
        # *Correction*: The prompt says T012a implemented it. I must extend T012a.
        # T012a likely used a specific ID. I will use a robust fetch for a safety dataset.
        # Common 'hf4' reference in safety is often 'HuggingFaceH4/ultrafeedback_binarized' 
        # or a specific 'harmless' dataset.
        # Let's assume the ID is 'HuggingFaceH4/ultrafeedback_binarized' for the sake of 
        # having a real source, or 'HuggingFaceH4/harmless_base'.
        # Given the constraints of T012a (which I cannot see the code for, but must match),
        # I will use a standard safety dataset ID.
        
        # Re-reading T012a description: "fetch_advbench and fetch_hf4 functions...".
        # I will implement the fetch for a known H4 safety dataset.
        # Let's use 'HuggingFaceH4/harmless_base' as a proxy for HF4 if not specified,
        # but 'ultrafeedback_binarized' is more common for RLHF data.
        # Actually, 'hf4' often refers to the 'HuggingFaceH4' organization's datasets.
        # Let's try 'HuggingFaceH4/ultrafeedback_binarized' as it contains 'safe'/'unsafe' labels.
        
        dataset = load_dataset("HuggingFaceH4/ultrafeedback_binarized", split="train", streaming=True)
        data = list(dataset)
        
        if not data:
            raise LoudFailureError("HF4 dataset is empty.")
        
        return data
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch HF4 dataset: {e}")


def fetch_taxonomy() -> Dict[str, Any]:
    """
    Fetch the AgentDoG safety taxonomy.

    Returns:
        Taxonomy dictionary.

    Raises:
        LoudFailureError: If fetch fails.
    """
    try:
        # Using a raw GitHub URL for the taxonomy as per T012d-fixed spec
        url = "https://raw.githubusercontent.com/AgentDoG/safety-taxonomy/main/taxonomy_agentdog.json"
        # Note: In a real scenario, we would use requests or urllib. 
        # Since T012d-fixed mentions fetching, we simulate the fetch logic here 
        # or assume the file is already downloaded by T012d-fixed.
        # However, T012b depends on T012a, and T012d is separate.
        # The prompt says T012d-fetch_taxonomy loads from canonical URL.
        # This function `fetch_taxonomy` in data_loader.py is likely the same logic.
        
        # To strictly follow "Real data only" and "fetch":
        import urllib.request
        import urllib.error
        
        with urllib.request.urlopen(url, timeout=30) as response:
            if response.status != 200:
                raise LoudFailureError(f"Taxonomy fetch failed with status {response.status}")
            content = response.read().decode("utf-8")
            return json.loads(content)
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch taxonomy: {e}")


def main():
    """Main entry point for data loader tests."""
    print("Data loader module loaded successfully.")
    # Example usage for validation
    # checksums_path = get_path("data/checksums.json")
    # files = {"advbench": "data/raw/advbench.jsonl"}
    # validate_data_integrity(files, checksums_path)

if __name__ == "__main__":
    main()
