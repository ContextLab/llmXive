import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from main import run_full_pipeline
from utils.checksum_utils import compute_directory_hash, compute_sha256_file


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a single file."""
    if not file_path.exists():
        return ""
    return compute_sha256_file(file_path)


def compute_directory_hashes(data_dirs: List[Path]) -> Dict[str, str]:
    """
    Compute a combined hash for a set of directories.
    We hash every file in the directory tree, sort by relative path,
    and hash the concatenation to ensure order independence of file system traversal.
    """
    hasher = hashlib.sha256()
    all_file_hashes = []

    for directory in data_dirs:
        if not directory.exists():
            continue
        for file_path in sorted(directory.rglob("*")):
            if file_path.is_file():
                rel_path = file_path.relative_to(directory)
                file_hash = compute_file_hash(file_path)
                # Include relative path in the hash to prevent collisions across renames
                all_file_hashes.append(f"{rel_path}:{file_hash}")

    # Sort to ensure deterministic ordering regardless of filesystem traversal
    all_file_hashes.sort()
    combined_string = "\n".join(all_file_hashes)
    hasher.update(combined_string.encode('utf-8'))
    return hasher.hexdigest()


def run_pipeline_run(run_id: int, seed: int, count: int) -> Tuple[bool, str]:
    """
    Execute the full pipeline with the given parameters.
    Returns (success, message).
    """
    print(f"Starting Pipeline Run {run_id} with seed={seed}, count={count}...")
    try:
        # Clear previous data to ensure clean state for this run
        # We do this by relying on the main pipeline to overwrite,
        # but for strict reproducibility, we ensure the output dirs are clean if the script doesn't handle it.
        # However, run_full_pipeline is expected to handle generation/overwriting.
        
        # We invoke the main pipeline logic directly
        # Note: run_full_pipeline in main.py expects args. We simulate the args structure.
        # The main.py logic uses argparse, so we construct a namespace or call functions directly.
        # Since run_full_pipeline is exposed, we call it. 
        # To ensure determinism, we must set seeds before calling.
        
        import random
        import numpy as np
        random.seed(seed)
        np.random.seed(seed)
        
        # We need to pass the specific arguments to the pipeline logic.
        # Since main.py's run_full_pipeline might be wrapped in argparse, 
        # we check if we can call the underlying logic or if we need to simulate args.
        # Based on T033, run_full_pipeline orchestrates the steps.
        # Let's assume run_full_pipeline can be called with parameters or we mock sys.argv.
        
        # Safer approach: Call the specific functions if exposed, or run the script via subprocess.
        # Given the constraints, we will assume run_full_pipeline accepts parameters or we can set global state.
        # However, the safest way to replicate the CLI exactly is to set sys.argv.
        
        original_argv = sys.argv
        sys.argv = [
            "main.py",
            "--generate",
            "--count", str(count),
            "--seed", str(seed),
            "--compress",
            "--depths", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
            "--analyze"
        ]
        
        try:
            # Import main to ensure it's fresh
            import importlib
            import main
            importlib.reload(main)
            main.main()
        finally:
            sys.argv = original_argv
        
        print(f"Pipeline Run {run_id} completed successfully.")
        return True, "Success"
    except Exception as e:
        print(f"Pipeline Run {run_id} FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, str(e)


def compare_hashes(run1_hash: str, run2_hash: str) -> bool:
    """Compare two hash strings."""
    return run1_hash == run2_hash


def main():
    parser = argparse.ArgumentParser(description="Reproducibility Checker for llmXive Pipeline")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for both runs")
    parser.add_argument("--count", type=int, default=500, help="Number of workflows to generate")
    parser.add_argument("--output", type=str, default="data/results/reproducibility_report.json",
                        help="Path to save the reproducibility report")
    
    args = parser.parse_args()
    
    data_dirs = [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "results",
        PROJECT_ROOT / "state" / "projects"
    ]
    
    print(f"Running Reproducibility Check with seed={args.seed}, count={args.count}")
    
    # Run 1
    success1, msg1 = run_pipeline_run(1, args.seed, args.count)
    if not success1:
        print(f"Run 1 failed: {msg1}")
        sys.exit(1)
    
    hash1 = compute_directory_hashes(data_dirs)
    print(f"Run 1 Hash: {hash1}")
    
    # Run 2
    # We need to ensure the pipeline runs again, potentially overwriting the same files.
    # The compute_directory_hashes function will re-read the files.
    success2, msg2 = run_pipeline_run(2, args.seed, args.count)
    if not success2:
        print(f"Run 2 failed: {msg2}")
        sys.exit(1)
        
    hash2 = compute_directory_hashes(data_dirs)
    print(f"Run 2 Hash: {hash2}")
    
    identical = compare_hashes(hash1, hash2)
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    report = {
        "run1_hash": hash1,
        "run2_hash": hash2,
        "identical": identical,
        "timestamp": timestamp,
        "seed": args.seed,
        "count": args.count
    }
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    print(f"Reproducibility report saved to {output_path}")
    print(f"Result: {'IDENTICAL' if identical else 'DIFFERENT'}")
    
    if not identical:
        sys.exit(1)


if __name__ == "__main__":
    main()