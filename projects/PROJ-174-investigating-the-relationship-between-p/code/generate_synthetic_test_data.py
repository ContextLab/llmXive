"""
Synthetic Test Data Generator for Unit Tests Only.

This script generates synthetic pupil dilation and cognitive load data
strictly for unit testing purposes. It must NEVER be called by the main
pipeline. Execution requires the explicit '--test-mode' flag.
"""

import argparse
import os
import sys
import hashlib
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

# Ensure we can import from the code root if run as a script
# (Assumes script is run from the project root or code root)
if 'code' not in sys.path:
    code_root = Path(__file__).parent
    if code_root.name == 'code':
        sys.path.insert(0, str(code_root))

from data_model import Dataset

def generate_synthetic_dataset(
    num_subjects: int = 5,
    num_trials: int = 20,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a synthetic dataset mimicking the structure of real eye-tracking data.

    This data is purely for unit testing validation logic, not for scientific analysis.
    """
    rng = np.random.default_rng(seed)
    rows = []

    for sub_idx in range(num_subjects):
        subject_id = f"SUB{sub_idx:03d}"
        for trial_idx in range(num_trials):
            trial_id = f"TR{trial_idx:03d}"
            # Simulate 2 seconds of data at 1000Hz
            timestamps = np.arange(0, 2.0, 0.001)
            n_samples = len(timestamps)

            # Simulate pupil diameter (mm) with some noise and blink artifacts
            base_pupil = 4.5 + rng.normal(0, 0.1)
            pupil_diameter = base_pupil + rng.normal(0, 0.05, n_samples)

            # Simulate gaze coordinates (degrees)
            x = rng.normal(0.5, 0.2, n_samples)
            y = rng.normal(0.5, 0.2, n_samples)

            # Create some blink artifacts (dropouts)
            blink_indices = rng.choice(n_samples, size=10, replace=False)
            pupil_diameter[blink_indices] = 0.0

            # Simulate derived metrics for the row
            search_time = rng.uniform(0.5, 2.5)
            target_salience = rng.uniform(0.1, 0.9)
            fixation_count = rng.integers(5, 15)

            for i in range(n_samples):
                rows.append({
                    'subject_id': subject_id,
                    'trial_id': trial_id,
                    'timestamp': timestamps[i],
                    'pupil_diameter': pupil_diameter[i],
                    'x': x[i],
                    'y': y[i],
                    'search_time': search_time,
                    'target_salience': target_salience,
                    'fixation_count': fixation_count
                })

    return pd.DataFrame(rows)

def hash_file_content(filepath: str) -> str:
    """
    Computes SHA-256 hash of a file's content.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_test_artifacts_manifest(artifacts: list, output_path: str):
    """
    Writes a YAML-like manifest (JSON for simplicity in Python) of test artifacts
    and their hashes to state/test_artifacts.yaml (stored as .json or .yaml).
    The task requires state/test_artifacts.yaml. We will write it as a valid YAML file.
    """
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_script": "generate_synthetic_test_data.py",
        "artifacts": []
    }

    for artifact in artifacts:
        file_hash = hash_file_content(artifact['path'])
        manifest['artifacts'].append({
            "path": artifact['path'],
            "hash": file_hash,
            "size_bytes": os.stat(artifact['path']).st_size
        })

    # Write as YAML compatible JSON (or simple text format)
    # Since we need a .yaml file, we'll format it manually to avoid extra deps
    yaml_content = "generated_at: {}\nsource_script: generate_synthetic_test_data.py\nartifacts:\n".format(
        manifest['generated_at']
    )
    for item in manifest['artifacts']:
        yaml_content += "  - path: {}\n    hash: {}\n    size_bytes: {}\n".format(
            item['path'], item['hash'], item['size_bytes']
        )

    # Ensure state directory exists
    state_dir = Path(output_path).parent
    if not state_dir.exists():
        state_dir.mkdir(parents=True)

    with open(output_path, 'w') as f:
        f.write(yaml_content)

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic test data. MUST be run with --test-mode flag."
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        required=True,
        help="REQUIRED FLAG: Confirms this script is running in test mode only."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Directory to write synthetic data files."
    )
    parser.add_argument(
        "--num-subjects",
        type=int,
        default=5,
        help="Number of synthetic subjects."
    )
    parser.add_argument(
        "--num-trials",
        type=int,
        default=20,
        help="Number of trials per subject."
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
        print("ERROR: This script is for unit tests ONLY. Use --test-mode flag to proceed.")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    print(f"Generating synthetic data for {args.num_subjects} subjects...")
    df = generate_synthetic_dataset(
        num_subjects=args.num_subjects,
        num_trials=args.num_trials,
        seed=args.seed
    )

    output_file = output_dir / "synthetic_test_data.csv"
    df.to_csv(output_file, index=False)
    print(f"Saved synthetic data to: {output_file}")

    # Generate manifest for state tracking
    manifest_path = "state/test_artifacts.yaml"
    artifacts_list = [{"path": str(output_file)}]
    write_test_artifacts_manifest(artifacts_list, manifest_path)
    print(f"Generated test artifacts manifest at: {manifest_path}")

    print("Test data generation complete.")

if __name__ == "__main__":
    main()
