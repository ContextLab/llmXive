"""
Synthetic Test Data Generator for Unit Tests Only.

This script generates synthetic eye-tracking data strictly for unit testing purposes.
It MUST be invoked with the --test-mode flag.
It is NEVER called by the main pipeline (main.py).
Outputs are hashed and recorded in state/test_artifacts.yaml to prevent accidental
usage as real data.
"""
import argparse
import os
import sys
import hashlib
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# Ensure we can import project modules if needed, though this script is standalone
# for test generation.
PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

def generate_synthetic_dataset(
    n_subjects: int = 2,
    n_trials_per_subject: int = 5,
    n_samples_per_trial: int = 100,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a synthetic dataset mimicking the structure of real eye-tracking data.

    Columns: subject_id, trial_id, timestamp, pupil_diameter, x, y, search_time, target_salience, fixation_count

    Note: This data is random noise with structural validity, NOT real measurements.
    """
    np.random.seed(seed)
    rows = []

    for s in range(n_subjects):
        subject_id = f"SUB_{s:03d}"
        for t in range(n_trials_per_subject):
            trial_id = f"TR_{t:03d}"
            # Simulate 100 samples per trial (approx 100Hz sampling)
            timestamps = np.arange(n_samples_per_trial) * 0.01
            
            # Random walk for pupil diameter (simulating noise)
            pupil_diameter = 4.0 + np.cumsum(np.random.normal(0, 0.01, n_samples_per_trial))
            # Add some blinks (NaNs)
            blink_indices = np.random.choice(n_samples_per_trial, size=5, replace=False)
            pupil_diameter[blink_indices] = np.nan

            # Random gaze coordinates
            x = np.random.normal(0.5, 0.1, n_samples_per_trial)
            y = np.random.normal(0.5, 0.1, n_samples_per_trial)

            # Aggregate features for the trial
            search_time = np.random.uniform(2.0, 5.0)
            target_salience = np.random.uniform(0.0, 1.0)
            fixation_count = np.random.randint(5, 20)

            for i in range(n_samples_per_trial):
                rows.append({
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

    return pd.DataFrame(rows)

def hash_file_content(file_path: str) -> str:
    """Calculate SHA-256 hash of a file's content."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_test_artifacts_manifest(artifacts: list, output_path: str):
    """
    Writes a manifest of generated test artifacts to state/test_artifacts.yaml.
    This ensures the main pipeline knows these are test-only artifacts.
    """
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_script": "generate_synthetic_test_data.py",
        "mode": "TEST_ONLY",
        "artifacts": artifacts
    }

    # Simple YAML-like serialization (avoiding extra dependency for this specific script if possible, 
    # but using standard dict-to-string for safety)
    # Since requirements.txt includes pyyaml, we can use it if available, but let's stick to standard lib for robustness
    # or assume pyyaml is installed as per T002a.
    try:
        import yaml
        yaml_str = yaml.dump(manifest, default_flow_style=False, sort_keys=False)
    except ImportError:
        # Fallback to manual formatting if yaml is missing (should not happen based on T002a)
        yaml_str = f"generated_at: {manifest['generated_at']}\n"
        yaml_str += "source_script: generate_synthetic_test_data.py\n"
        yaml_str += "mode: TEST_ONLY\n"
        yaml_str += "artifacts:\n"
        for art in artifacts:
            yaml_str += f"  - path: {art['path']}\n"
            yaml_str += f"    hash: {art['hash']}\n"

    with open(output_path, "w") as f:
        f.write(yaml_str)

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic test data for unit tests ONLY. "
                    "Must be run with --test-mode flag."
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        required=True,
        help="Flag to explicitly enable test data generation. Without this, script exits."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DATA_RAW_DIR),
        help="Directory to save the synthetic CSV file."
    )
    parser.add_argument(
        "--n-subjects",
        type=int,
        default=2,
        help="Number of synthetic subjects."
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=5,
        help="Trials per subject."
    )

    args = parser.parse_args()

    if not args.test_mode:
        print("ERROR: --test-mode flag is required. This script is for unit tests only.")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "synthetic_test_data.csv"
    manifest_file = STATE_DIR / "test_artifacts.yaml"

    print(f"Generating synthetic dataset with {args.n_subjects} subjects...")
    df = generate_synthetic_dataset(
        n_subjects=args.n_subjects,
        n_trials_per_subject=args.n_trials,
        seed=42
    )

    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"Saved synthetic data to: {output_file}")

    # Hash the file
    file_hash = hash_file_content(str(output_file))

    # Write manifest
    artifacts_list = [
        {
            "path": str(output_file.relative_to(PROJECT_ROOT)),
            "hash": file_hash,
            "type": "synthetic_test_data"
        }
    ]
    write_test_artifacts_manifest(artifacts_list, str(manifest_file))
    print(f"Test artifacts manifest written to: {manifest_file}")
    print("WARNING: This data is synthetic and marked for testing only. Do not use for analysis.")

if __name__ == "__main__":
    main()
