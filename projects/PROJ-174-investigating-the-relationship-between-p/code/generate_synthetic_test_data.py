"""
Synthetic Test Data Generator for Unit Tests.

This script generates deterministic synthetic data ONLY when invoked with
the --test-mode flag. It is explicitly designed to be NEVER called by the
main pipeline. Its output is hashed and recorded in state/test_artifacts.yaml
for integrity verification.

Usage:
    python code/generate_synthetic_test_data.py --test-mode
"""

import argparse
import os
import sys
import hashlib
import json
from datetime import datetime, timezone
from typing import List, Dict, Any

import numpy as np
import pandas as pd

# Project relative imports
# Ensure code/ is in path for imports if run from root
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.provenance import hash_file, write_meta
from data_model import Dataset


def generate_synthetic_dataset(
    subject_id: int,
    num_trials: int,
    seed: int,
    noise_level: float = 0.1
) -> pd.DataFrame:
    """
    Generates a synthetic DataFrame mimicking the structure of processed eye-tracking data.

    Columns: timestamp, x, y, pupil_diameter, search_time, target_salience, fixation_count, trial_id
    """
    np.random.seed(seed)

    # Generate timestamps (1000Hz sampling, 2 seconds per trial)
    timestamps = np.arange(0, 2.0, 0.001)
    n_samples = len(timestamps)
    total_rows = num_trials * n_samples

    # Simulate data
    trial_ids = np.repeat(np.arange(num_trials), n_samples)
    subject_ids = np.full(total_rows, subject_id)

    # X, Y coordinates (random walk around center)
    x = np.cumsum(np.random.normal(0, 0.5, total_rows))
    y = np.cumsum(np.random.normal(0, 0.5, total_rows))

    # Pupil diameter (simulated load: 4.0mm base + load effect)
    # Load effect: slightly larger pupil in later trials or specific conditions
    base_pupil = 4.0
    load_effect = np.random.normal(0, noise_level, total_rows)
    pupil_diameter = base_pupil + load_effect + (0.05 * (trial_ids / num_trials))

    # Search time (fixed per trial for simplicity in synthetic data)
    search_time = np.repeat(np.random.uniform(1.5, 3.5, num_trials), n_samples)

    # Target salience (random 0.0 to 1.0)
    target_salience = np.repeat(np.random.uniform(0.0, 1.0, num_trials), n_samples)

    # Fixation count (integer, correlated with search time)
    fixation_count = np.repeat(np.random.randint(3, 10, num_trials), n_samples)

    df = pd.DataFrame({
        'subject_id': subject_ids,
        'trial_id': trial_ids,
        'timestamp': timestamps,
        'pupil_diameter': pupil_diameter,
        'x': x,
        'y': y,
        'search_time': search_time,
        'target_salience': target_salience,
        'fixation_count': fixation_count
    })

    return df


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic test data for unit tests ONLY."
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="REQUIRED: Enable generation. Without this flag, the script exits safely."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Directory to save synthetic data (default: data/raw)"
    )
    parser.add_argument(
        "--num-subjects",
        type=int,
        default=2,
        help="Number of synthetic subjects to generate"
    )
    parser.add_argument(
        "--num-trials",
        type=int,
        default=5,
        help="Number of trials per subject"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    if not args.test_mode:
        print("ERROR: --test-mode flag is required to generate synthetic data.")
        print("This script is for unit tests ONLY and should not be part of the main pipeline.")
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    generated_files = []

    print(f"Generating synthetic data for {args.num_subjects} subjects...")

    for i in range(args.num_subjects):
        subject_id = i + 100  # Start IDs at 100 to distinguish from real data
        seed = args.seed + i

        df = generate_synthetic_dataset(
            subject_id=subject_id,
            num_trials=args.num_trials,
            seed=seed
        )

        filename = f"synthetic_subject_{subject_id}_seed_{seed}.csv"
        filepath = os.path.join(args.output_dir, filename)

        df.to_csv(filepath, index=False)
        generated_files.append(filepath)
        print(f"  Generated: {filepath}")

    # Hash outputs and write meta
    meta_path = os.path.join("state", "test_artifacts.yaml")
    os.makedirs("state", exist_ok=True)

    artifact_records = []

    for filepath in generated_files:
        file_hash = hash_file(filepath)
        record = {
            "path": filepath,
            "hash": file_hash,
            "type": "synthetic_test_data",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        artifact_records.append(record)

    # Write a simple YAML-like structure manually to avoid dependency on PyYAML if not needed,
    # but the project has pyyaml in requirements. We'll use standard json for safety or simple text.
    # The task asks for state/test_artifacts.yaml.
    with open(meta_path, "w") as f:
        f.write("# Test Artifacts Manifest\n")
        f.write(f"# Generated: {datetime.now(timezone.utc).isoformat()}\n")
        f.write("artifacts:\n")
        for rec in artifact_records:
            f.write(f"  - path: {rec['path']}\n")
            f.write(f"    hash: {rec['hash']}\n")
            f.write(f"    type: {rec['type']}\n")
            f.write(f"    timestamp: {rec['timestamp']}\n")

    print(f"Manifest written to: {meta_path}")
    print("Synthetic data generation complete.")


if __name__ == "__main__":
    main()
