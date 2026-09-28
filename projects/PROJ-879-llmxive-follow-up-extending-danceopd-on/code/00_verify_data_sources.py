#!/usr/bin/env python
"""
Task T043: Add Data Source Verification & Hashing.

Extends the data fetching pipeline (T042) to verify the integrity of streamed data.
It computes SHA256 hashes for the written files and compares them against the
stream hashes recorded in state/artifact_hashes.yaml.

If the stream hash is not present (e.g., pre-fetched data), it computes and stores
the file hash in data/results/source_hashes.json for future verification.
"""
import argparse
import json
import hashlib
import sys
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import yaml

# Import config utilities if available, otherwise define minimal path logic
try:
    from utils.config import get_config
except ImportError:
    # Fallback for standalone execution if utils not in path
    def get_config():
        return None

def get_project_root() -> Path:
    """Returns the project root directory."""
    # Assuming script is in code/ or code/utils/
    return Path(__file__).resolve().parent.parent

def calculate_sha256_file(file_path: Path) -> str:
    """
    Computes the SHA256 hash of a file by reading it in chunks.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal SHA256 hash string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in 4MB chunks to handle large files without loading entirely into RAM
            for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")

def load_stream_hashes(state_path: Path) -> Dict[str, str]:
    """
    Loads the stream hashes recorded during the fetch phase (T042).
    
    Args:
        state_path: Path to state/artifact_hashes.yaml.
        
    Returns:
        Dictionary mapping dataset names to their stream hashes.
        
    Raises:
        FileNotFoundError: If the state file does not exist.
    """
    if not state_path.exists():
        raise FileNotFoundError(f"Stream hash state file not found: {state_path}")
    
    with open(state_path, "r") as f:
        data = yaml.safe_load(f)
    
    if data is None:
        return {}
        
    return data

def save_source_hashes(output_path: Path, hashes: Dict[str, str]) -> None:
    """
    Saves the computed file hashes to the results directory for future reference.
    
    Args:
        output_path: Path to data/results/source_hashes.json.
        hashes: Dictionary of file names to hashes.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(hashes, f, indent=2)

def save_verification_log(log_path: Path, status: str, details: Dict) -> None:
    """
    Saves the verification log indicating success or failure.
    
    Args:
        log_path: Path to data/results/verification_log.json.
        status: 'success' or 'failure'.
        details: Dictionary containing verification details.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_entry = {
        "status": status,
        "verification_time": None, # Could add timestamp if needed
        "details": details
    }
    with open(log_path, "w") as f:
        json.dump(log_entry, f, indent=2)

def verify_data_sources(
    project_root: Path,
    raw_data_dir: Path,
    state_dir: Path,
    results_dir: Path
) -> bool:
    """
    Main verification logic for T043.
    
    1. Identifies target files: imagenet_samples.parquet and laion_samples.parquet.
    2. Loads stream hashes from state/artifact_hashes.yaml.
    3. Computes file hashes for the written files.
    4. Compares hashes.
       - If stream hash exists: Must match exactly. If not, FAIL (exit 1).
       - If stream hash missing (pre-fetched): Compute hash and save to results/source_hashes.json.
    
    Returns:
        True if verification passes or pre-fetched data is handled successfully.
        False if verification fails.
    """
    target_files = {
        "imagenet": raw_data_dir / "imagenet_samples.parquet",
        "laion": raw_data_dir / "laion_samples.parquet"
    }
    
    state_file = state_dir / "artifact_hashes.yaml"
    source_hashes_file = results_dir / "source_hashes.json"
    verification_log_file = results_dir / "verification_log.json"
    
    # Load stream hashes
    stream_hashes = {}
    stream_hash_exists = False
    try:
        stream_hashes = load_stream_hashes(state_file)
        stream_hash_exists = True
    except FileNotFoundError:
        # State file missing might mean T042 didn't run or state was cleared.
        # We proceed but note that we can't verify against stream.
        pass
    
    verification_details = {
        "files_verified": [],
        "errors": [],
        "pre_fetched_handling": []
    }
    
    all_passed = True
    
    for dataset_name, file_path in target_files.items():
        if not file_path.exists():
            msg = f"Target file missing: {file_path}"
            verification_details["errors"].append(msg)
            all_passed = False
            continue
        
        try:
            file_hash = calculate_sha256_file(file_path)
            verification_details["files_verified"].append({
                "dataset": dataset_name,
                "path": str(file_path),
                "file_hash": file_hash
            })
        except (FileNotFoundError, IOError) as e:
            msg = f"Failed to hash {file_path}: {e}"
            verification_details["errors"].append(msg)
            all_passed = False
            continue
        
        if stream_hash_exists and f"source_stream_hash_{dataset_name}" in stream_hashes:
            expected_hash = stream_hashes[f"source_stream_hash_{dataset_name}"]
            if file_hash != expected_hash:
                msg = (
                    f"Hash Mismatch for {dataset_name}!\n"
                    f"  Stream Hash (recorded): {expected_hash}\n"
                    f"  File Hash (computed):   {file_hash}\n"
                    f"  Path: {file_path}\n"
                    f"  Action: Failing verification to prevent silent corruption."
                )
                verification_details["errors"].append(msg)
                all_passed = False
            else:
                verification_details["files_verified"][-1]["status"] = "verified"
        else:
            # No stream hash to compare against (e.g., pre-fetched data)
            # We compute and store the hash for future verification
            msg = (
                f"No stream hash found for {dataset_name}. "
                f"Computed file hash and saving to {source_hashes_file}."
            )
            verification_details["pre_fetched_handling"].append({
                "dataset": dataset_name,
                "file_hash": file_hash,
                "message": msg
            })
    
    # Save source hashes if we computed any (for pre-fetched case)
    if verification_details["pre_fetched_handling"]:
        current_hashes = {}
        if source_hashes_file.exists():
            try:
                with open(source_hashes_file, "r") as f:
                    current_hashes = json.load(f)
            except json.JSONDecodeError:
                current_hashes = {}
        
        for item in verification_details["pre_fetched_handling"]:
            current_hashes[item["dataset"]] = item["file_hash"]
        
        save_source_hashes(source_hashes_file, current_hashes)
    
    # Save verification log
    status = "success" if all_passed else "failure"
    save_verification_log(verification_log_file, status, verification_details)
    
    return all_passed

def main():
    """Entry point for the verification script."""
    parser = argparse.ArgumentParser(
        description="Verify data source integrity against recorded stream hashes (T043)."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Path to project root. Defaults to parent of script directory."
    )
    args = parser.parse_args()
    
    project_root = Path(args.project_root) if args.project_root else get_project_root()
    
    raw_data_dir = project_root / "data" / "raw"
    state_dir = project_root / "state"
    results_dir = project_root / "data" / "results"
    
    # Ensure directories exist
    state_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting Data Source Verification (T043)...")
    print(f"Project Root: {project_root}")
    print(f"Raw Data Dir: {raw_data_dir}")
    print(f"State Dir: {state_dir}")
    print(f"Results Dir: {results_dir}")
    
    try:
        success = verify_data_sources(project_root, raw_data_dir, state_dir, results_dir)
        
        if success:
            print("Verification PASSED.")
            print("All file hashes match recorded stream hashes (or pre-fetched data handled).")
            sys.exit(0)
        else:
            print("Verification FAILED.")
            print("See data/results/verification_log.json for details.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Unexpected error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
