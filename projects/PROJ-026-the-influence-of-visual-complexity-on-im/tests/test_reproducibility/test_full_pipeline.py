"""
Final End-to-End Reproducibility Test (T055).

This script verifies that the full pipeline is fully deterministic given the seed.
It runs the pipeline twice and asserts that the SHA-256 hashes of all output files
in data/results/ match exactly between runs.
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path
import shutil
import json

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_MAIN = PROJECT_ROOT / "code" / "main.py"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
EXCLUDED_FILES = {"logs.json"}  # Files to exclude from hash comparison (e.g., timestamped logs)

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_result_hashes() -> dict:
    """Capture SHA-256 hashes of all output files in data/results/."""
    hashes = {}
    if not RESULTS_DIR.exists():
        raise FileNotFoundError(f"Results directory not found: {RESULTS_DIR}")
    
    for file_path in RESULTS_DIR.iterdir():
        if file_path.is_file():
            # Exclude timestamped logs or specified files
            if file_path.name in EXCLUDED_FILES:
                continue
            hashes[file_path.name] = compute_file_hash(file_path)
    
    return hashes

def run_pipeline() -> None:
    """Run the full pipeline with --null-effect flag."""
    cmd = [sys.executable, str(CODE_MAIN), "--null-effect"]
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Pipeline failed: {result.stderr}")

def test_reproducibility() -> None:
    """
    Test that two consecutive runs of the pipeline produce identical results.
    """
    print("Starting Reproducibility Test (T055)...")
    
    # Clean previous results if any
    if RESULTS_DIR.exists():
        shutil.rmtree(RESULTS_DIR)
    
    # Run 1
    print("Running pipeline (Run 1)...")
    run_pipeline()
    hashes_run1 = get_result_hashes()
    
    if not hashes_run1:
        raise RuntimeError("No result files generated in Run 1.")
    
    print(f"Run 1 completed. Found {len(hashes_run1)} result files.")
    
    # Clean results for Run 2
    shutil.rmtree(RESULTS_DIR)
    
    # Run 2
    print("Running pipeline (Run 2)...")
    run_pipeline()
    hashes_run2 = get_result_hashes()
    
    if not hashes_run2:
        raise RuntimeError("No result files generated in Run 2.")
    
    print(f"Run 2 completed. Found {len(hashes_run2)} result files.")
    
    # Compare hashes
    if set(hashes_run1.keys()) != set(hashes_run2.keys()):
        missing_run1 = set(hashes_run1.keys()) - set(hashes_run2.keys())
        missing_run2 = set(hashes_run2.keys()) - set(hashes_run1.keys())
        raise AssertionError(
            f"Result file sets differ. Missing in Run 2: {missing_run1}, "
            f"Missing in Run 1: {missing_run2}"
        )
    
    mismatches = []
    for filename, hash1 in hashes_run1.items():
        hash2 = hashes_run2[filename]
        if hash1 != hash2:
            mismatches.append(filename)
    
    if mismatches:
        raise AssertionError(
            f"Reproducibility failed! The following files differ between runs: {mismatches}"
        )
    
    print("SUCCESS: All result files are identical across runs. Pipeline is deterministic.")

if __name__ == "__main__":
    test_reproducibility()
