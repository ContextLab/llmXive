"""
Synthetic dataset generator for AB test summaries.

This module creates a synthetic dataset containing both binary (conversion rate)
and continuous (e.g., revenue) outcomes. The generated CSV file contains at
least 10 000 records and is written to ``data/synthetic/synthetic_dataset.csv``.
A companion JSON metadata file is written to
``data/synthetic/metadata.json``.
"""

import csv
import json
import logging
import os
import random
from pathlib import Path
from typing import List, Tuple, Dict

import numpy as np

# Project‑specific utilities
from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger

LOGGER = get_default_logger(__name__)

# --------------------------------------------------------------------------- #
# Seed handling
# --------------------------------------------------------------------------- #
def set_all_seeds() -> None:
    """
    Initialise all random number generators for reproducibility.
    """
    set_rng_seed(SEED)          # Project‑wide RNG seed helper
    np.random.seed(SEED)        # NumPy RNG
    random.seed(SEED)           # Python's ``random`` module
    LOGGER.info("All RNG seeds set to %s", SEED)

# --------------------------------------------------------------------------- #
# Sample‑size generation
# --------------------------------------------------------------------------- #
def generate_sample_sizes(num_records: int) -> List[Tuple[int, int]]:
    """
    Generate a list of (control_n, treatment_n) sample‑size pairs.

    Sample sizes are drawn uniformly from 100 – 5 000 (inclusive) to mimic
    realistic A/B test traffic volumes.

    Parameters
    ----------
    num_records: int
        Number of AB‑test records to generate.

    Returns
    -------
    List[Tuple[int, int]]
        List of control / treatment sample‑size tuples.
    """
    sample_sizes = []
    for _ in range(num_records):
        control_n = random.randint(100, 5_000)
        treatment_n = random.randint(100, 5_000)
        sample_sizes.append((control_n, treatment_n))
    LOGGER.debug("Generated %d sample‑size pairs", num_records)
    return sample_sizes

# --------------------------------------------------------------------------- #
# Binary outcome generation
# --------------------------------------------------------------------------- #
def generate_binary_outcome(
    sample_sizes: List[Tuple[int, int]]
) -> List[Dict]:
    """
    Generate synthetic binary (conversion‑rate) outcomes.

    For each record a baseline conversion probability is drawn from
    ``U(0.01, 0.30)``.  An effect size is drawn from ``U(-0.10, 0.10)`` and
    applied to the treatment group.  Conversions are sampled from a
    binomial distribution.

    Returns a list of dictionaries with keys:
    ``test_id``, ``outcome_type``, ``control_n``, ``treatment_n``,
    ``control_metric``, ``treatment_metric`` (rates as floats).
    """
    records = []
    for idx, (c_n, t_n) in enumerate(sample_sizes, start=1):
        baseline = random.uniform(0.01, 0.30)
        effect = random.uniform(-0.10, 0.10)
        treatment_rate = min(max(baseline + effect, 0.0), 1.0)

        # Sample conversions
        control_conversions = np.random.binomial(c_n, baseline)
        treatment_conversions = np.random.binomial(t_n, treatment_rate)

        control_rate = control_conversions / c_n
        treatment_rate_observed = treatment_conversions / t_n

        records.append(
            {
                "test_id": f"binary_{idx}",
                "outcome_type": "binary",
                "control_n": c_n,
                "treatment_n": t_n,
                "control_metric": round(control_rate, 5),
                "treatment_metric": round(treatment_rate_observed, 5),
            }
        )
    LOGGER.debug("Generated %d binary outcome records", len(records))
    return records

# --------------------------------------------------------------------------- #
# Continuous outcome generation
# --------------------------------------------------------------------------- #
def generate_continuous_outcome(
    sample_sizes: List[Tuple[int, int]]
) -> List[Dict]:
    """
    Generate synthetic continuous outcomes (e.g., revenue per user).

    For each record a baseline mean is drawn from ``U(0, 100)`` and an effect
    from ``U(-10, 10)``.  A standard deviation is drawn from ``U(5, 20)``.
    Sample means are drawn from a normal distribution with the specified
    mean and std‑dev.

    Returns a list of dictionaries with the same schema as the binary
    generator, but ``outcome_type`` is ``continuous`` and the metric fields
    contain the sampled means.
    """
    records = []
    for idx, (c_n, t_n) in enumerate(sample_sizes, start=1):
        baseline_mean = random.uniform(0, 100)
        effect = random.uniform(-10, 10)
        stddev = random.uniform(5, 20)

        treatment_mean = baseline_mean + effect

        # Sample means (using CLT approximation)
        control_sample_mean = np.random.normal(
            loc=baseline_mean, scale=stddev / np.sqrt(c_n)
        )
        treatment_sample_mean = np.random.normal(
            loc=treatment_mean, scale=stddev / np.sqrt(t_n)
        )

        records.append(
            {
                "test_id": f"continuous_{idx}",
                "outcome_type": "continuous",
                "control_n": c_n,
                "treatment_n": t_n,
                "control_metric": round(control_sample_mean, 5),
                "treatment_metric": round(treatment_sample_mean, 5),
            }
        )
    LOGGER.debug("Generated %d continuous outcome records", len(records))
    return records

# --------------------------------------------------------------------------- #
# Dataset assembly
# --------------------------------------------------------------------------- #
def generate_synthetic_dataset(num_records: int = 10_000) -> List[Dict]:
    """
    Create a combined synthetic dataset.

    Half of the records are binary, half continuous (rounded up/down as
    required).  The function guarantees at least ``num_records`` total
    records.

    Parameters
    ----------
    num_records: int, optional
        Desired minimum number of records (default 10 000).

    Returns
    -------
    List[Dict]
        List of synthetic AB‑test summary dictionaries.
    """
    # Ensure an even split; if odd we add one extra binary record.
    half = num_records // 2
    remainder = num_records - 2 * half

    # Generate sample sizes for each sub‑population
    binary_sizes = generate_sample_sizes(half + remainder)
    continuous_sizes = generate_sample_sizes(half)

    binary_records = generate_binary_outcome(binary_sizes)
    continuous_records = generate_continuous_outcome(continuous_sizes)

    dataset = binary_records + continuous_records
    random.shuffle(dataset)  # Randomise ordering
    LOGGER.info(
        "Synthetic dataset generated with %d total records (%d binary, %d continuous)",
        len(dataset),
        len(binary_records),
        len(continuous_records),
    )
    return dataset

# --------------------------------------------------------------------------- #
# Validation helpers
# --------------------------------------------------------------------------- #
def verify_outcome_types(dataset: List[Dict]) -> None:
    """
    Simple validation that each record contains a recognised ``outcome_type``.
    Raises ``ValueError`` if an unexpected type is encountered.
    """
    allowed = {"binary", "continuous"}
    for rec in dataset:
        if rec.get("outcome_type") not in allowed:
            raise ValueError(
                f"Unexpected outcome_type {rec.get('outcome_type')} in record {rec.get('test_id')}"
            )
    LOGGER.debug("All outcome types verified as binary or continuous")

# --------------------------------------------------------------------------- #
# Persistence helpers
# --------------------------------------------------------------------------- #
def write_summaries_to_csv(dataset: List[Dict], output_path: Path) -> None:
    """
    Write the synthetic dataset to a CSV file.

    Parameters
    ----------
    dataset: List[Dict]
        List of summary dictionaries.
    output_path: Path
        Destination CSV file path.
    """
    fieldnames = [
        "test_id",
        "outcome_type",
        "control_n",
        "treatment_n",
        "control_metric",
        "treatment_metric",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in dataset:
            writer.writerow(row)
    LOGGER.info("Synthetic dataset written to %s (%d rows)", output_path, len(dataset))

def write_metadata(metadata: Dict, output_path: Path) -> None:
    """
    Write a small JSON metadata file describing the generation run.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)
    LOGGER.info("Metadata written to %s", output_path)

# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Generate the synthetic dataset and persist it to disk.

    The function writes two files:
    * ``data/synthetic/synthetic_dataset.csv`` – the full dataset.
    * ``data/synthetic/metadata.json`` – generation parameters.
    """
    set_all_seeds()

    # Generate data
    dataset = generate_synthetic_dataset(num_records=10_000)

    # Validation step
    verify_outcome_types(dataset)

    # Define output locations
    base_dir = Path("data") / "synthetic"
    csv_path = base_dir / "synthetic_dataset.csv"
    meta_path = base_dir / "metadata.json"

    # Write outputs
    write_summaries_to_csv(dataset, csv_path)
    write_metadata(
        {
            "record_count": len(dataset),
            "binary_fraction": sum(1 for r in dataset if r["outcome_type"] == "binary")
            / len(dataset),
            "seed": SEED,
            "generated_by": "src.audit.synthetic",
        },
        meta_path,
    )

if __name__ == "__main__":
    main()