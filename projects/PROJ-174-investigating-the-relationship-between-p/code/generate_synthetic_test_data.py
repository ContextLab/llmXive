"""
Synthetic Test Data Generator for Unit Tests ONLY.

This module generates synthetic eye-tracking data for unit testing purposes.
It is flagged by the --test-mode argument and MUST NEVER be called by the
main pipeline. Its output is hashed and recorded in state/test_artifacts.yaml.
"""
import argparse
import os
import sys
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Ensure directories exist
STATE_DIR.mkdir(parents=True, exist_ok=True)
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

def generate_synthetic_dataset(
    n_subjects: int = 5,
    n_trials: int = 10,
    n_samples_per_trial: int = 100,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate a synthetic dataset mimicking the structure of real eye-tracking data.

    Columns: subject_id, trial_id, timestamp, pupil_diameter, x, y, search_time, target_salience, fixation_count
    """
    np.random.seed(seed)
    records = []

    for subj_idx in range(n_subjects):
        subject_id = f"sub_{subj_idx:03d}"
        for trial_idx in range(n_trials):
            trial_id = f"tr_{trial_idx:03d}"
            # Simulate a trial duration
            base_time = 1000.0 + trial_idx * 100.0
            timestamps = np.linspace(base_time, base_time + 2000.0, n_samples_per_trial)
            
            # Simulate pupil diameter (mean ~5.0mm, slight fluctuation)
            pupil_diameter = 5.0 + np.random.normal(0, 0.2, n_samples_per_trial)
            
            # Simulate gaze coordinates (random walk)
            x = np.cumsum(np.random.normal(0, 0.5, n_samples_per_trial))
            y = np.cumsum(np.random.normal(0, 0.5, n_samples_per_trial))
            
            # Derived metrics (synthetic)
            search_time = np.random.uniform(1.5, 4.0)
            target_salience = np.random.uniform(0.1, 0.9)
            fixation_count = np.random.randint(3, 15)

            for i in range(n_samples_per_trial):
                records.append({
                    "subject_id": subject_id,
                    "trial_id": trial_id,
                    "timestamp": timestamps[i],
                    "pupil_diameter": pupil_diameter[i],
                    "x": x[i],
                    "y": y[i],
                    "search_time": search_time,
                    "target_salience": target_salience,
                    "fixation_count": fixation_count
                })

    return pd.DataFrame(records)

def hash_file_content(content: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()

def write_test_artifacts_manifest(output_path: Path, file_path: Path, file_hash: str):
    """
    Write the hash of the generated test artifact to state/test_artifacts.yaml.
    This ensures the test data is tracked and never confused with real data.
    """
    manifest_path = STATE_DIR / "test_artifacts.yaml"
    
    # Load existing manifest or create new
    if manifest_path.exists():
        # Simple YAML parsing for this specific structure
        import yaml
        with open(manifest_path, 'r') as f:
            try:
                manifest = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                manifest = {}
    else:
        manifest = {}

    # Update entry
    entry = {
        "file_path": str(file_path.relative_to(PROJECT_ROOT)),
        "hash": file_hash,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "type": "synthetic_test_data",
        "note": "DO NOT USE FOR PIPELINE EXECUTION"
    }
    manifest[str(file_path)] = entry

    # Write back
    with open(manifest_path, 'w') as f:
        import yaml
        yaml.dump(manifest, f, default_flow_style=False)

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic test data for unit tests ONLY.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        WARNING: This script is for unit testing ONLY.
        It must be called with --test-mode flag.
        It MUST NOT be part of the main pipeline execution.
        """
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        required=True,
        help="Required flag. This script will exit with error if this is not provided."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/synthetic_test_data.csv",
        help="Output path relative to project root."
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=5,
        help="Number of synthetic subjects."
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=10,
        help="Number of trials per subject."
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=100,
        help="Samples per trial."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )

    args = parser.parse_args()

    # Safety check: Ensure we are not accidentally running in production
    if not args.test_mode:
        print("ERROR: --test-mode flag is required. This script is for unit tests ONLY.", file=sys.stderr)
        sys.exit(1)

    print(f"Generating synthetic dataset with {args.subjects} subjects, {args.trials} trials each...")
    
    df = generate_synthetic_dataset(
        n_subjects=args.subjects,
        n_trials=args.trials,
        n_samples_per_trial=args.samples,
        seed=args.seed
    )

    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    df.to_csv(output_path, index=False)
    print(f"Saved synthetic data to: {output_path}")

    # Hash the file
    with open(output_path, 'rb') as f:
        file_hash = hash_file_content(f.read())

    # Update manifest
    write_test_artifacts_manifest(STATE_DIR / "test_artifacts.yaml", output_path, file_hash)
    print(f"Registered artifact hash in state/test_artifacts.yaml: {file_hash[:16]}...")

if __name__ == "__main__":
    main()
