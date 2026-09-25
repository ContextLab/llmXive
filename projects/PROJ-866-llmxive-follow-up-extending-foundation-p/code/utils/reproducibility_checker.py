"""
Reproducibility Checker for llmXive Pipeline.

This script executes the full pipeline twice with the same seed and verifies
that the SHA-256 hashes of all output files are identical.

Usage:
    python code/utils/reproducibility_checker.py --seed 42 --runs 2
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from main import run_full_pipeline, ensure_directories
from utils.finalize_state_registry import compute_directory_hash, collect_all_artifact_hashes, update_state_registry
from utils.checksum_utils import compute_sha256_file


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return compute_sha256_file(str(file_path))


def compute_directory_hashes(directory: Path) -> Dict[str, str]:
    """Compute SHA-256 hashes for all files in a directory recursively."""
    if not directory.exists():
        return {}
    
    hashes = {}
    for file_path in sorted(directory.rglob('*')):
        if file_path.is_file():
            relative_path = file_path.relative_to(directory)
            hashes[str(relative_path)] = compute_file_hash(file_path)
    return hashes


def run_pipeline_run(run_id: int, seed: int, data_dir: Path, state_dir: Path) -> Tuple[int, Dict[str, str]]:
    """
    Run the full pipeline with a specific seed and return the hashes of all output files.
    
    Args:
        run_id: Identifier for this run (1 or 2)
        seed: Random seed for reproducibility
        data_dir: Path to the data directory
        state_dir: Path to the state directory
        
    Returns:
        Tuple of (exit_code, dict of file paths to hashes)
    """
    print(f"\n=== Starting Pipeline Run {run_id} with seed {seed} ===")
    
    # Ensure directories exist
    ensure_directories()
    
    # Set random seeds for reproducibility
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)
    
    # Run the full pipeline
    try:
        # We need to run the pipeline with the specific seed
        # The main.py should handle this via environment or direct call
        # For now, we'll call the run_full_pipeline function directly
        # Note: This assumes run_full_pipeline uses the global random state
        
        # Generate workflows
        print(f"Run {run_id}: Generating workflows...")
        # We'll use the main.py CLI interface for consistency
        # But since we're calling from code, we'll simulate the calls
        
        # Actually, let's just call the main function with the right args
        # We need to be careful about how we pass the seed
        
        # For reproducibility, we'll set the seed before each major operation
        # and ensure the pipeline uses it consistently
        
        # Run the pipeline
        exit_code = run_full_pipeline(
            generate=True,
            compress=True,
            analyze=True,
            seed=seed,
            workflow_count=500
        )
        
        if exit_code != 0:
            print(f"Pipeline run {run_id} failed with exit code {exit_code}")
            return exit_code, {}
        
        # Collect hashes of all output files
        print(f"Run {run_id}: Computing hashes...")
        all_hashes = {}
        
        # Hash data directories
        for subdir in ['raw', 'processed', 'results']:
            subdir_path = data_dir / subdir
            if subdir_path.exists():
                dir_hashes = compute_directory_hashes(subdir_path)
                for rel_path, hash_val in dir_hashes.items():
                    all_hashes[f"data/{subdir}/{rel_path}"] = hash_val
        
        # Hash state directory
        state_path = state_dir / 'projects'
        if state_path.exists():
            state_hashes = compute_directory_hashes(state_path)
            for rel_path, hash_val in state_hashes.items():
                all_hashes[f"state/projects/{rel_path}"] = hash_val
        
        print(f"Run {run_id}: Computed {len(all_hashes)} file hashes")
        return 0, all_hashes
        
    except Exception as e:
        print(f"Pipeline run {run_id} failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1, {}


def compare_hashes(run1_hashes: Dict[str, str], run2_hashes: Dict[str, str]) -> Tuple[bool, List[str], List[str]]:
    """
    Compare hashes from two runs and report differences.
    
    Returns:
        Tuple of (all_match, list of missing in run2, list of different)
    """
    missing_in_run2 = []
    different = []
    
    for key, hash1 in run1_hashes.items():
        if key not in run2_hashes:
            missing_in_run2.append(key)
        elif run2_hashes[key] != hash1:
            different.append(key)
    
    all_match = len(missing_in_run2) == 0 and len(different) == 0
    return all_match, missing_in_run2, different


def main():
    parser = argparse.ArgumentParser(description='Reproducibility Checker for llmXive Pipeline')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--runs', type=int, default=2, help='Number of runs to perform')
    parser.add_argument('--workflow-count', type=int, default=500, help='Number of workflows to generate')
    parser.add_argument('--output-dir', type=str, default='data/reproducibility_test', 
                      help='Directory to store reproducibility test results')
    args = parser.parse_args()
    
    # Set up paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / 'data'
    state_dir = project_root / 'state'
    output_dir = project_root / args.output_dir
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean up any previous test data
    if (data_dir / 'raw').exists():
        shutil.rmtree(data_dir / 'raw')
    if (data_dir / 'processed').exists():
        shutil.rmtree(data_dir / 'processed')
    if (data_dir / 'results').exists():
        shutil.rmtree(data_dir / 'results')
    if (state_dir / 'projects').exists():
        shutil.rmtree(state_dir / 'projects')
    
    # Run the pipeline multiple times
    all_hashes = []
    for run_id in range(1, args.runs + 1):
        exit_code, hashes = run_pipeline_run(run_id, args.seed, data_dir, state_dir)
        if exit_code != 0:
            print(f"Reproducibility test FAILED: Run {run_id} failed")
            sys.exit(1)
        all_hashes.append(hashes)
    
    # Compare all runs
    if len(all_hashes) < 2:
        print("Reproducibility test FAILED: Not enough runs completed")
        sys.exit(1)
    
    # Compare run 1 with run 2
    all_match, missing, different = compare_hashes(all_hashes[0], all_hashes[1])
    
    # Save results
    results = {
        'seed': args.seed,
        'workflow_count': args.workflow_count,
        'runs_completed': len(all_hashes),
        'reproducible': all_match,
        'missing_files_in_run2': missing,
        'different_files': different,
        'timestamp': datetime.now().isoformat(),
        'run1_hashes': all_hashes[0],
        'run2_hashes': all_hashes[1]
    }
    
    results_path = output_dir / 'reproducibility_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n=== Reproducibility Test Results ===")
    print(f"Seed: {args.seed}")
    print(f"Workflow count: {args.workflow_count}")
    print(f"Runs completed: {len(all_hashes)}")
    print(f"Reproducible: {all_match}")
    
    if not all_match:
        if missing:
            print(f"Missing files in run 2: {len(missing)}")
            for f in missing[:10]:  # Show first 10
                print(f"  - {f}")
            if len(missing) > 10:
                print(f"  ... and {len(missing) - 10} more")
        
        if different:
            print(f"Different files: {len(different)}")
            for f in different[:10]:  # Show first 10
                print(f"  - {f}")
            if len(different) > 10:
                print(f"  ... and {len(different) - 10} more")
        
        print("\nReproducibility test FAILED")
        sys.exit(1)
    else:
        print("All files match between runs!")
        print("Reproducibility test PASSED")
        
        # Also update the state registry with the reproducibility hash
        project_state_file = state_dir / 'projects' / 'PROJ-866-llmxive-follow-up-extending-foundation-p.yaml'
        if project_state_file.exists():
            reproducibility_hash = compute_directory_hash(data_dir)
            update_state_registry(
                state_file=str(project_state_file),
                reproducibility_hash=reproducibility_hash,
                final_verification_timestamp=datetime.now().isoformat()
            )
            print(f"State registry updated with reproducibility hash: {reproducibility_hash}")
        
        sys.exit(0)


if __name__ == '__main__':
    main()
