#!/usr/bin/env python
"""
Task T043: Add Data Source Verification & Hashing.

Extends T012/T042 to verify the integrity of streamed data.
Computes SHA256 hashes for written files and compares them against
the stream hashes stored in state/artifact_hashes.yaml by T042.
"""
import argparse
import json
import hashlib
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Ensure imports match existing API surface
from utils.config import get_config

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent

def calculate_sha256_file(file_path: Path) -> str:
    """
    Calculates the SHA256 hash of a file.
    Reads the file in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_stream_hashes(state_dir: Path) -> Dict[str, str]:
    """
    Loads the stream hashes from state/artifact_hashes.yaml.
    Returns an empty dict if the file does not exist.
    """
    hash_file = state_dir / "artifact_hashes.yaml"
    if not hash_file.exists():
        return {}
    
    try:
        with open(hash_file, 'r') as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"Warning: Could not load stream hashes from {hash_file}: {e}")
        return {}

def save_source_hashes(results_dir: Path, hashes: Dict[str, str]) -> None:
    """
    Saves the computed file hashes to data/results/source_hashes.json.
    """
    output_file = results_dir / "source_hashes.json"
    with open(output_file, 'w') as f:
        json.dump(hashes, f, indent=2)
    print(f"Source hashes saved to {output_file}")

def save_verification_log(results_dir: Path, log_entry: Dict[str, Any]) -> None:
    """
    Appends a verification log entry to data/results/verification_log.json.
    """
    log_file = results_dir / "verification_log.json"
    log_data = []
    
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                log_data = json.load(f)
        except json.JSONDecodeError:
            log_data = []
    
    log_data.append(log_entry)
    
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    print(f"Verification log updated at {log_file}")

def verify_data_sources(
    raw_dir: Path, 
    state_dir: Path, 
    results_dir: Path,
    expected_files: list
) -> bool:
    """
    Verifies the integrity of streamed data files.
    
    1. Computes SHA256 hashes for written files.
    2. Compares against stream hashes from state/artifact_hashes.yaml.
    3. If stream hash is missing (pre-fetched data), stores file hash for future use.
    4. Fails loudly (exit 1) if stream hash exists and does not match.
    
    Returns True if verification passes or if no stream hash exists (first run).
    Returns False if verification fails.
    """
    stream_hashes = load_stream_hashes(state_dir)
    file_hashes = {}
    all_verified = True
    
    for file_name in expected_files:
        file_path = raw_dir / file_name
        
        if not file_path.exists():
            print(f"ERROR: Expected file not found: {file_path}")
            all_verified = False
            continue
        
        # Compute file hash
        file_hash = calculate_sha256_file(file_path)
        file_hashes[file_name] = file_hash
        
        # Determine key for stream hash
        # T042 stores hashes as: source_stream_hash_<dataset_name>
        # We assume file names map to dataset names (e.g., imagenet_samples.parquet -> imagenet)
        dataset_name = file_name.replace("_samples.parquet", "").replace("laion", "laion400m")
        stream_key = f"source_stream_hash_{dataset_name}"
        
        stream_hash = stream_hashes.get(stream_key)
        
        if stream_hash:
            # We have a canonical stream hash to compare against
            if file_hash == stream_hash:
                print(f"VERIFIED: {file_name} matches stream hash.")
                log_entry = {
                    "file": file_name,
                    "status": "verified",
                    "file_hash": file_hash,
                    "stream_hash": stream_hash,
                    "timestamp": "current_run"
                }
            else:
                print(f"ERROR: Hash mismatch for {file_name}!")
                print(f"  File hash:  {file_hash}")
                print(f"  Stream hash: {stream_hash}")
                print("This indicates data corruption or a change in the source stream.")
                log_entry = {
                    "file": file_name,
                    "status": "failed",
                    "file_hash": file_hash,
                    "stream_hash": stream_hash,
                    "timestamp": "current_run"
                }
                all_verified = False
        else:
            # No stream hash found (e.g., pre-fetched data or first run)
            print(f"INFO: No stream hash found for {file_name}. Storing file hash for future verification.")
            log_entry = {
                "file": file_name,
                "status": "stored",
                "file_hash": file_hash,
                "stream_hash": None,
                "timestamp": "current_run"
            }
        
        save_verification_log(results_dir, log_entry)
    
    # Save all computed file hashes
    save_source_hashes(results_dir, file_hashes)
    
    return all_verified

def main():
    """Main entry point for T043 verification."""
    parser = argparse.ArgumentParser(description="Verify data source integrity (T043)")
    parser.add_argument("--raw-dir", type=str, default=None, help="Path to raw data directory")
    parser.add_argument("--state-dir", type=str, default=None, help="Path to state directory")
    parser.add_argument("--results-dir", type=str, default=None, help="Path to results directory")
    
    args = parser.parse_args()
    
    project_root = get_project_root()
    
    raw_dir = Path(args.raw_dir) if args.raw_dir else project_root / "data" / "raw"
    state_dir = Path(args.state_dir) if args.state_dir else project_root / "state"
    results_dir = Path(args.results_dir) if args.results_dir else project_root / "data" / "results"
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Files to verify (as per T042 and T012)
    expected_files = [
        "imagenet_samples.parquet",
        "laion_samples.parquet"
    ]
    
    print(f"Verifying data sources in {raw_dir}...")
    print(f"Stream hashes loaded from {state_dir / 'artifact_hashes.yaml'}")
    
    success = verify_data_sources(raw_dir, state_dir, results_dir, expected_files)
    
    if not success:
        print("Data source verification FAILED. Exiting with code 1.")
        sys.exit(1)
    else:
        print("Data source verification completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
