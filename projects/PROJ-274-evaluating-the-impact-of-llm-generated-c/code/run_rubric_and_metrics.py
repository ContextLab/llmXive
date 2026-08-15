import json
import os
import sys
import hashlib
import logging
from typing import List, Dict, Any, Tuple
from validation import run_rubric_on_candidates, collect_metrics_for_covariates, calculate_file_checksum, update_checksums

logger = logging.getLogger(__name__)

def ensure_dirs():
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/checksums", exist_ok=True) # Ensure checksums dir exists if needed

def calculate_file_checksum(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums(checksum_file: str, filename: str, checksum: str):
    os.makedirs(os.path.dirname(checksum_file), exist_ok=True)
    if os.path.exists(checksum_file):
        with open(checksum_file, 'r') as f:
            lines = f.readlines()
        lines = [l for l in lines if not l.startswith(f"{filename}:")]
    else:
        lines = []
    lines.append(f"{filename}:{checksum}\n")
    with open(checksum_file, 'w') as f:
        f.writelines(lines)

def load_existing_metrics(metrics_file: str) -> List[Dict[str, Any]]:
    if os.path.exists(metrics_file):
        with open(metrics_file, 'r') as f:
            return json.load(f)
    return []

def main():
    """
    Main entry point for T021a and T021c execution.
    Runs the rubric and collects metrics.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run rubric and collect metrics")
    parser.add_argument("--repos", nargs='+', required=True, help="List of repository paths to evaluate")
    parser.add_argument("--metrics-output", default="data/raw/repo_metrics.json", help="Output path for metrics")
    parser.add_argument("--rubric-output", default="data/raw/repo_selection_rubric.json", help="Output path for rubric results")
    parser.add_argument("--checksums", default="data/checksums.txt", help="Path to checksums file")
    args = parser.parse_args()

    ensure_dirs()

    # 1. Collect Metrics (T021c)
    metrics_data = []
    for repo in args.repos:
        if os.path.isdir(repo):
            m = collect_metrics_for_covariates(repo)
            metrics_data.append(m)
    
    os.makedirs(os.path.dirname(args.metrics_output), exist_ok=True)
    with open(args.metrics_output, 'w') as f:
        json.dump(metrics_data, f, indent=2)
    logger.info(f"Metrics saved to {args.metrics_output}")

    # 2. Run Rubric (T021a)
    rubric_results = run_rubric_on_candidates(args.repos)
    os.makedirs(os.path.dirname(args.rubric_output), exist_ok=True)
    with open(args.rubric_output, 'w') as f:
        json.dump(rubric_results, f, indent=2)
    logger.info(f"Rubric results saved to {args.rubric_output}")

    # 3. Generate Checksums
    if os.path.exists(args.metrics_output):
        checksum = calculate_file_checksum(args.metrics_output)
        update_checksums(args.checksums, args.metrics_output, checksum)
        logger.info(f"Checksum for {args.metrics_output}: {checksum}")
    
    if os.path.exists(args.rubric_output):
        checksum = calculate_file_checksum(args.rubric_output)
        update_checksums(args.checksums, args.rubric_output, checksum)
        logger.info(f"Checksum for {args.rubric_output}: {checksum}")

    print("Success: Metrics and Rubric generated and checksums updated.")

if __name__ == "__main__":
    main()