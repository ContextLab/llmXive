"""
T005: Data Loader for Multi-LCB.
Streams the Multi-LCB dataset from HuggingFace, shards it into parquet files,
and maintains a manifest with SHA-256 checksums.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

CHUNK_SIZE = 1000  # Number of rows per parquet shard

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def stream_and_shard(cache_dir: Path):
    """
    Streams the Multi-LCB dataset and writes it to parquet shards.
    Returns a dictionary mapping filename to checksum.
    """
    log.info("Streaming Multi-LCB dataset from HuggingFace...")
    # As per spec: load_dataset("multilcb", split="train", streaming=True)
    dataset = load_dataset("multilcb", split="train", streaming=True)
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    manifest = {}
    current_chunk = []
    shard_idx = 0
    
    for row in dataset:
        current_chunk.append(row)
        if len(current_chunk) >= CHUNK_SIZE:
            shard_path = cache_dir / f"shard_{shard_idx:04d}.parquet"
            df = pd.DataFrame(current_chunk)
            df.to_parquet(shard_path, index=False)
            
            checksum = compute_sha256(shard_path)
            manifest[shard_path.name] = checksum
            
            log.info(f"Saved shard {shard_idx} to {shard_path} (hash: {checksum[:8]}...)")
            
            current_chunk = []
            shard_idx += 1
    
    # Save remaining rows
    if current_chunk:
        shard_path = cache_dir / f"shard_{shard_idx:04d}.parquet"
        df = pd.DataFrame(current_chunk)
        df.to_parquet(shard_path, index=False)
        checksum = compute_sha256(shard_path)
        manifest[shard_path.name] = checksum
        log.info(f"Saved final shard {shard_idx} to {shard_path}")
    
    return manifest

def verify_shards(cache_dir: Path, manifest_path: Path):
    """
    Verifies that all shards listed in the manifest exist and their checksums match.
    """
    if not manifest_path.exists():
        log.error(f"Manifest not found at {manifest_path}")
        return False
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    all_passed = True
    for filename, expected_hash in manifest.items():
        file_path = cache_dir / filename
        if not file_path.exists():
            log.error(f"Missing shard: {filename}")
            all_passed = False
            continue
        
        actual_hash = compute_sha256(file_path)
        if actual_hash != expected_hash:
            log.error(f"Checksum mismatch for {filename}: expected {expected_hash}, got {actual_hash}")
            all_passed = False
        else:
            log.info(f"Verified {filename}")
    
    return all_passed

def main():
    parser = argparse.ArgumentParser(description="Multi-LCB Data Loader")
    parser.add_argument("--cache-dir", type=str, default="data/raw", help="Directory to store shards")
    parser.add_argument("--verify-checksum", action="store_true", help="Verify checksums after download")
    args = parser.parse_args()
    
    cache_dir = Path(args.cache_dir)
    manifest_path = cache_dir / "manifest.json"
    
    # Only download if manifest doesn't exist or we want to force a refresh
    if not manifest_path.exists():
        manifest = stream_and_shard(cache_dir)
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        log.info(f"Manifest written to {manifest_path}")
    else:
        log.info(f"Manifest already exists at {manifest_path}, skipping download.")
    
    if args.verify_checksum:
        log.info("Verifying shard checksums...")
        if verify_shards(cache_dir, manifest_path):
            log.info("All shards verified successfully.")
        else:
            log.error("Shard verification failed!")
            exit(1)

if __name__ == "__main__":
    main()
