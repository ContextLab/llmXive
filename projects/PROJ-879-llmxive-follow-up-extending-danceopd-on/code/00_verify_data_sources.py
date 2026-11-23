#!/usr/bin/env python
"""
T043: Add Data Source Verification & Hashing.

Extends T042 to verify the integrity of streamed data.
Logic:
1. Compute SHA256 hashes for the written files (data/raw/imagenet_samples.parquet, etc.).
2. Compare these file hashes against the stream hashes stored in state/artifact_hashes.yaml by T042.
3. If mismatch -> Fail loud (exit 1).
4. If stream hash missing (pre-fetched data), compute and store file hash in data/results/source_hashes.json.
5. Write verification log to data/results/verification_log.json.
"""
import argparse
import json
import hashlib
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def calculate_sha256_file(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_stream_hashes(state_path: Path) -> Dict[str, str]:
    """Load stream hashes from state/artifact_hashes.yaml."""
    if not state_path.exists():
        logger.warning(f"Stream hash file not found: {state_path}")
        return {}
    try:
        with open(state_path, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('source_stream_hashes', {})
    except Exception as e:
        logger.error(f"Failed to load stream hashes: {e}")
        return {}

def save_source_hashes(output_path: Path, hashes: Dict[str, str]) -> None:
    """Save computed file hashes to data/results/source_hashes.json."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(hashes, f, indent=2)
    logger.info(f"Source hashes saved to {output_path}")

def save_verification_log(output_path: Path, log_data: Dict[str, Any]) -> None:
    """Save verification log to data/results/verification_log.json."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Verification log saved to {output_path}")

def verify_data_sources(
    raw_dir: Path,
    state_path: Path,
    output_hashes_path: Path,
    output_log_path: Path
) -> bool:
    """
    Verify data sources against stream hashes.
    
    Returns:
        bool: True if verification passed, False otherwise.
    """
    files_to_verify = [
        "imagenet_samples.parquet",
        "laion_samples.parquet"
    ]
    
    stream_hashes = load_stream_hashes(state_path)
    verification_results = []
    all_passed = True
    
    for filename in files_to_verify:
        file_path = raw_dir / filename
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}. Skipping verification.")
            verification_results.append({
                "file": filename,
                "status": "missing",
                "message": "File not found"
            })
            continue
        
        # Calculate file hash
        file_hash = calculate_sha256_file(file_path)
        
        # Determine key in stream hashes
        # T042 stores keys like 'source_stream_hash_imagenet'
        key_map = {
            "imagenet_samples.parquet": "source_stream_hash_imagenet",
            "laion_samples.parquet": "source_stream_hash_laion"
        }
        expected_key = key_map.get(filename)
        
        if expected_key and expected_key in stream_hashes:
            expected_hash = stream_hashes[expected_key]
            if file_hash == expected_hash:
                logger.info(f"Verification PASSED for {filename}")
                verification_results.append({
                    "file": filename,
                    "status": "verified",
                    "file_hash": file_hash,
                    "expected_hash": expected_hash
                })
            else:
                logger.error(f"Verification FAILED for {filename}")
                logger.error(f"  File hash: {file_hash}")
                logger.error(f"  Expected hash: {expected_hash}")
                verification_results.append({
                    "file": filename,
                    "status": "failed",
                    "file_hash": file_hash,
                    "expected_hash": expected_hash,
                    "message": "Hash mismatch"
                })
                all_passed = False
        else:
            # No stream hash available (e.g., pre-fetched data)
            logger.info(f"No stream hash found for {filename}. Storing file hash for future verification.")
            verification_results.append({
                "file": filename,
                "status": "recorded",
                "file_hash": file_hash,
                "message": "Stream hash not available; file hash recorded"
            })
    
    # Save source hashes for files that didn't have stream hashes
    new_hashes = {}
    for result in verification_results:
        if result["status"] == "recorded":
            new_hashes[result["file"]] = result["file_hash"]
    
    if new_hashes:
        save_source_hashes(output_hashes_path, new_hashes)
    
    # Save verification log
    log_data = {
        "status": "passed" if all_passed else "failed",
        "timestamp": os.popen('date -Iseconds 2>/dev/null || date').read().strip(),
        "results": verification_results
    }
    save_verification_log(output_log_path, log_data)
    
    return all_passed

def main():
    parser = argparse.ArgumentParser(description="Verify data source integrity")
    parser.add_argument("--raw-dir", type=str, default=None,
                      help="Path to raw data directory (default: data/raw)")
    parser.add_argument("--state-dir", type=str, default=None,
                      help="Path to state directory (default: state)")
    parser.add_argument("--output-hashes", type=str, default=None,
                      help="Path to output hashes JSON (default: data/results/source_hashes.json)")
    parser.add_argument("--output-log", type=str, default=None,
                      help="Path to output verification log (default: data/results/verification_log.json)")
    
    args = parser.parse_args()
    
    project_root = get_project_root()
    
    raw_dir = Path(args.raw_dir) if args.raw_dir else project_root / "data" / "raw"
    state_dir = Path(args.state_dir) if args.state_dir else project_root / "state"
    state_path = state_dir / "artifact_hashes.yaml"
    
    output_hashes_path = Path(args.output_hashes) if args.output_hashes else project_root / "data" / "results" / "source_hashes.json"
    output_log_path = Path(args.output_log) if args.output_log else project_root / "data" / "results" / "verification_log.json"
    
    if not raw_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        sys.exit(1)
    
    success = verify_data_sources(raw_dir, state_path, output_hashes_path, output_log_path)
    
    if not success:
        logger.error("Data source verification FAILED. Exiting with code 1.")
        sys.exit(1)
    
    logger.info("Data source verification PASSED.")
    sys.exit(0)

if __name__ == "__main__":
    main()