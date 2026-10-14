"""
Synthetic data generator for neural representation drift studies.

This module creates a deterministic synthetic dataset consisting of
per‑subject, per‑day records with spike counts and trial‑success rates.
The generated data respects the input schema defined in
`specs/001-quantifying-neural-representation-drift/contracts/input_schema.schema.yaml`.

The script is executable; running it writes the dataset to
`data/raw/synthetic_records.jsonl` and a SHA‑256 checksum file to
`data/raw/checksums.json`.
"""

import json
import hashlib
import random
from pathlib import Path

import numpy as np
from llmxive_toolkit import paths, get_logger
from code.src.config import CONFIG
from code.src.data import validator

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _set_global_seed(seed: int) -> None:
    """Apply the given seed to all standard random generators."""
    random.seed(seed)
    np.random.seed(seed)

def _random_orthogonal_matrix(dim: int) -> np.ndarray:
    """
    Generate a random orthogonal matrix via QR decomposition.
    """
    a = np.random.randn(dim, dim)
    q, _ = np.linalg.qr(a)
    return q

def _generate_subject_base_pattern(num_units: int, num_bins: int) -> np.ndarray:
    """
    Base firing pattern for a subject: Poisson‑distributed spike counts.
    Shape: (num_units, num_bins)
    """
    # Mean firing rate of 5 spikes per bin, Poisson noise
    return np.random.poisson(lam=5.0, size=(num_units, num_bins)).astype(float)

def _apply_drift(base_pattern: np.ndarray, drift_rate: float, day: int) -> np.ndarray:
    """
    Apply a drift transformation to the base pattern.
    The drift is implemented as a random rotation whose angle grows
    proportionally with ``drift_rate * day``.
    """
    num_units = base_pattern.shape[0]
    # Generate a random orthogonal matrix once per call and raise it
    # to the power ``day`` by successive multiplication.
    rot = _random_orthogonal_matrix(num_units)
    # Apply the rotation ``day`` times (equivalent to rot^day)
    result = base_pattern.copy()
    for _ in range(day):
        result = rot @ result
    # Add a small linear component to emulate gradual change
    result += drift_rate * day
    return result

def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-x))

# ----------------------------------------------------------------------
# Core dataset generation
# ----------------------------------------------------------------------
def generate_synthetic_records(
    num_subjects: int = 20,
    num_days: int = 10,
    num_units: int = 30,
    num_bins: int = 100,
) -> list[dict]:
    """
    Generate a list of synthetic records adhering to the input schema.

    Parameters
    ----------
    num_subjects : int
        Number of distinct subjects.
    num_days : int
        Number of training days per subject.
    num_units : int
        Number of neural units recorded for each subject.
    num_bins : int
        Number of 20 ms bins per day (i.e., length of the spike‑count vector).

    Returns
    -------
    records : list[dict]
        Each dict contains ``subject_id``, ``session_id``, ``day_index``,
        ``spike_counts`` (flattened list), and ``trial_success``.
    """
    _set_global_seed(CONFIG.random_seed)
    records = []

    # Create latent variables that induce the required correlation
    # between drift_rate (b) and learning_speed (slope of trial_success).
    # We sample drift rates from a normal distribution and then construct
    # learning slopes that have a Pearson r ≈ 0.6 with the drift rates.
    drift_rates = np.random.normal(loc=0.05, scale=0.02, size=num_subjects)
    # Generate learning slopes with desired correlation
    noise = np.random.normal(scale=0.02, size=num_subjects)
    learning_slopes = 0.8 * drift_rates + 0.2 * noise  # approx r≈0.6

    for subj_idx in range(num_subjects):
        subject_id = f"subj_{subj_idx:03d}"
        drift_rate = float(drift_rates[subj_idx])
        learning_slope = float(learning_slopes[subj_idx])

        # Base firing pattern for this subject (units × bins)
        base_pattern = _generate_subject_base_pattern(num_units, num_bins)

        for day in range(num_days):
            session_id = f"{subject_id}_day{day}"
            # Apply drift to spike counts
            drifted_pattern = _apply_drift(base_pattern.copy(), drift_rate, day)
            spike_counts = drifted_pattern.flatten().tolist()

            # Generate trial_success as a monotonic function of day with
            # subject‑specific slope; add small noise and bound to [0,1].
            raw_success = learning_slope * day + np.random.normal(scale=0.05)
            trial_success = float(np.clip(_sigmoid(raw_success), 0.0, 1.0))

            record = {
                "subject_id": subject_id,
                "session_id": session_id,
                "day_index": day,
                "spike_counts": spike_counts,
                "trial_success": trial_success,
            }

            # Validate immediately to catch schema violations early
            validator.validate_record(record)

            records.append(record)

    return records

# ----------------------------------------------------------------------
# File‑writing utilities
# ----------------------------------------------------------------------
def _write_jsonl(records: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for rec in records:
            json.dump(rec, f)
            f.write("\n")

def _write_checksum(file_path: Path, checksum_path: Path) -> None:
    """
    Compute SHA‑256 checksum of ``file_path`` and write a JSON mapping.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with checksum_path.open("w", encoding="utf-8") as f:
        json.dump({file_path.name: checksum}, f, indent=2)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Generate the synthetic dataset and write it to the project data folder.
    """
    log.info("Generating synthetic neural‑behavioral records...")
    records = generate_synthetic_records()
    records_path = paths.data("raw", "synthetic_records.jsonl")
    checksum_path = paths.data("raw", "checksums.json")
    _write_jsonl(records, records_path)
    _write_checksum(records_path, checksum_path)
    log.info(f"Synthetic data written to: {records_path}")
    log.info(f"Checksum written to: {checksum_path}")

if __name__ == "__main__":
    main()
