import os
import json
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, List

from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def stream_dataset_to_file(dataset_id: str, size_label: str, output_path: Path):
    """
    Streams a dataset from HuggingFace and writes it to a local file.
    Fails loudly if the dataset cannot be loaded.
    """
    # The registry might contain short names; we ensure they are full HF paths.
    # Based on quickstart.md, the namespace is 'THZERAOFC'.
    full_id = dataset_id if "/" in dataset_id else f"THZERAOFC/{dataset_id}"
    
    log.info(f"Streaming dataset {full_id} for {size_label} into {output_path}...")
    
    try:
        # Streaming=True ensures we don't load the whole thing into RAM
        ds = load_dataset(full_id, streaming=True, split='train')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            count = 0
            for record in ds:
                f.write(json.dumps(record) + '\n')
                count += 1
        
        if count == 0:
            raise RuntimeError(f"Dataset {full_id} was streamed but contained no records.")
        
        log.info(f"Successfully streamed {count} records for {size_label}.")
    except Exception as e:
        # Abort loudly as per requirement (no synthetic fallback)
        raise RuntimeError(f"Failed to stream dataset {full_id}: {str(e)}") from e

def main():
    """
    T010: Stream verified datasets into data/raw/ and record checksums.
    """
    registry_path = paths.data("metadata", "dataset_registry.json")
    checksums_path = paths.data("metadata", "checksums.txt")
    
    if not registry_path.exists():
        raise RuntimeError(f"Dataset registry not found at {registry_path}. Run T008 first.")

    with open(registry_path, 'r') as f:
        registry = json.load(f)

    # We expect N1000, N2000, N4000
    required_sizes = ["N1000", "N2000", "N4000"]
    checksums = []

    for size in required_sizes:
        if size not in registry:
            raise RuntimeError(f"System size {size} missing from registry.")
        
        # Use the first verified ID for this size
        dataset_id = registry[size][0]
        output_file = paths.data("raw", f"{size}.jsonl")
        
        # Stream real data to disk
        stream_dataset_to_file(dataset_id, size, output_file)
        
        # Compute checksum of the resulting file
        file_hash = compute_sha256(output_file)
        checksums.append(f"{output_file.name}: {file_hash}")
        log.info(f"Checksum for {size}: {file_hash}")

    # Write checksums to metadata
    with open(checksums_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(checksums) + "\n")
    
    log.info(f"T010 completed. Checksums written to {checksums_path}")

if __name__ == "__main__":
    main()