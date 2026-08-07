"""
Data loading module for llmXive drift detection pipeline.
Handles fetching real datasets from Hugging Face with streaming and strict error handling.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator, Generator

from datasets import load_dataset


class LoudFailureError(Exception):
    """Custom exception for loud failure when data fetching or validation fails."""
    pass


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum


def validate_data_integrity(raw_dir: Path, checksums_file: Path) -> None:
    """Validate all files in raw directory against checksums."""
    if not checksums_file.exists():
        raise LoudFailureError(f"Checksums file not found: {checksums_file}")
    
    with open(checksums_file, "r") as f:
        checksums = json.load(f)
    
    for filename, expected_checksum in checksums.items():
        file_path = raw_dir / filename
        if not file_path.exists():
            raise LoudFailureError(f"Missing file: {file_path}")
        if not verify_checksum(file_path, expected_checksum):
            raise LoudFailureError(
                f"Checksum mismatch for {filename}: "
                f"expected {expected_checksum}, got {compute_sha256(file_path)}"
            )


def load_jsonl_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    if not file_path.exists():
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
                raise LoudFailureError(
                    f"Invalid JSON at line {line_num} in {file_path}: {e}"
                )
    return data


def save_jsonl_file(data: List[Dict[str, Any]], file_path: Path) -> None:
    """Save a list of dictionaries to a JSONL file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        for record in data:
            f.write(json.dumps(record) + "\n")


def fetch_advbench(output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Fetch AdvBench dataset from Hugging Face using streaming.
    
    Source: https://huggingface.co/datasets/llm-attacks/advbench
    
    Args:
        output_path: Optional path to save the dataset locally. If None, returns data in memory.
        
    Returns:
        List of dictionaries containing 'text' and 'label' columns.
        
    Raises:
        LoudFailureError: If dataset fetch fails or data is invalid.
    """
    try:
        # Use streaming to avoid loading entire dataset into memory
        dataset = load_dataset(
            "llm-attacks/advbench", 
            split="train", 
            streaming=True
        )
        
        data = []
        for idx, row in enumerate(dataset):
            if "text" not in row:
                raise LoudFailureError(
                    f"AdvBench row {idx} missing 'text' field: {row}"
                )
            data.append({
                "text": str(row["text"]).strip(),
                "label": "jailbreak"  # AdvBench is specifically jailbreak attempts
            })
        
        if not data:
            raise LoudFailureError("AdvBench dataset returned empty results")
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            save_jsonl_file(data, output_path)
        
        return data
        
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch AdvBench dataset: {e}")


def fetch_hf4(output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Fetch HF4 (Harmless-4) dataset from Hugging Face using streaming.
    
    Source: https://huggingface.co/datasets/llm-attacks/harmless-base
    (Note: Using harmless-base as the proxy for HF4 safe logs)
    
    Args:
        output_path: Optional path to save the dataset locally. If None, returns data in memory.
        
    Returns:
        List of dictionaries containing 'text' and 'label' columns.
        
    Raises:
        LoudFailureError: If dataset fetch fails or data is invalid.
    """
    try:
        # Using harmless-base as the source for safe/benign logs
        dataset = load_dataset(
            "llm-attacks/harmless-base", 
            split="train", 
            streaming=True
        )
        
        data = []
        for idx, row in enumerate(dataset):
            if "text" not in row:
                raise LoudFailureError(
                    f"HF4 row {idx} missing 'text' field: {row}"
                )
            data.append({
                "text": str(row["text"]).strip(),
                "label": "safe"  # HF4 is specifically safe/benign logs
            })
        
        if not data:
            raise LoudFailureError("HF4 dataset returned empty results")
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            save_jsonl_file(data, output_path)
        
        return data
        
    except Exception as e:
        raise LoudFailureError(f"Failed to fetch HF4 dataset: {e}")


def fetch_taxonomy(output_path: Path) -> List[Dict[str, Any]]:
    """
    Fetch the fixed AgentDoG safety taxonomy from a canonical URL.
    
    Args:
        output_path: Path to save the taxonomy JSON file.
        
    Returns:
        List of taxonomy entries.
        
    Raises:
        LoudFailureError: If fetch fails and local fallback is not available.
    """
    import urllib.request
    import urllib.error
    
    canonical_url = "https://raw.githubusercontent.com/llmXive/agentdog/main/taxonomy_agentdog.json"
    local_fallback = output_path.parent / "taxonomy_agentdog_local.json"
    
    # Try canonical URL first
    try:
        with urllib.request.urlopen(canonical_url, timeout=30) as response:
            if response.status != 200:
                raise LoudFailureError(f"Canonical URL returned status {response.status}")
            taxonomy_data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        # Fall back to local copy if network fails
        if local_fallback.exists():
            with open(local_fallback, "r", encoding="utf-8") as f:
                taxonomy_data = json.load(f)
        else:
            raise LoudFailureError(
                f"Failed to fetch taxonomy from canonical URL and no local fallback: {e}"
            )
    
    # Save to output path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(taxonomy_data, f, indent=2)
    
    return taxonomy_data


def main():
    """Main entry point for data loading demonstration."""
    from config import get_path, ensure_directories
    
    raw_dir = get_path("data/raw")
    ensure_directories([raw_dir])
    
    print("Fetching AdvBench dataset...")
    try:
        advbench_data = fetch_advbench(raw_dir / "advbench.jsonl")
        print(f"Successfully fetched {len(advbench_data)} AdvBench entries")
    except LoudFailureError as e:
        print(f"AdvBench fetch failed: {e}")
        sys.exit(1)
    
    print("\nFetching HF4 dataset...")
    try:
        hf4_data = fetch_hf4(raw_dir / "hf4.jsonl")
        print(f"Successfully fetched {len(hf4_data)} HF4 entries")
    except LoudFailureError as e:
        print(f"HF4 fetch failed: {e}")
        sys.exit(1)
    
    print("\nData loading complete!")


if __name__ == "__main__":
    main()
