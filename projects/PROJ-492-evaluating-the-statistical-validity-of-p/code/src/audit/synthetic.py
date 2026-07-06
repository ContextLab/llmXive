"""
Synthetic dataset generator for the AB‑test audit pipeline.

This module generates a synthetic corpus of AB‑test summaries that can be used
to validate the end‑to‑end audit components (reconstruction, validation,
prevalence calculation, etc.).  The generator fulfills the following
functional requirements (FR‑030):

* Produce **at least 10 000** summary records.
* Include **both binary and continuous** outcome types (constraint‑preservation‑2958f04c).
* Write the generated data to both CSV and JSON files under the ``data/`` directory.
* Write a small metadata file describing the generated corpus.

The implementation deliberately uses only standard‑library modules together with
the project’s existing dependencies (``numpy``, ``scipy`` and ``statsmodels``) and
respects the project‑wide random‑seed configuration (``src.config.SEED``).
"""

import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest

# Project imports – these are guaranteed to exist according to the API surface.
from src.config import SEED, set_rng_seed
from src.utils.logger import get_default_logger

logger = get_default_logger(__name__)

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def set_all_seeds(seed: int = SEED) -> None:
    """
    Initialise all randomness sources used by the generator.

    Args:
        seed: The deterministic seed defined in ``src.config``.  The default
              ensures reproducibility across runs and satisfies Constitution
              Principle I.
    """
    logger.debug("Setting all random seeds to %s", seed)
    random.seed(seed)
    np.random.seed(seed)
    set_rng_seed(seed)  # Project‑wide helper that also seeds any RNG wrappers.


def generate_sample_sizes(num_records: int) -> List[Tuple[int, int]]:
    """
    Generate a list of (control, treatment) sample sizes.

    Sample sizes are drawn uniformly from a sensible range (100‑5000) that
    keeps the synthetic data realistic while still being quick to generate.

    Returns:
        List of tuples ``[(n_control, n_treatment), ...]``.
    """
    logger.debug("Generating %d sample‑size pairs", num_records)
    return [
        (random.randint(100, 5_000), random.randint(100, 5_000))
        for _ in range(num_records)
    ]


# --------------------------------------------------------------------------- #
# Binary outcome generation
# --------------------------------------------------------------------------- #
def generate_binary_outcome(sample_sizes: List[Tuple[int, int]]) -> List[Dict]:
    """
    For each (n_control, n_treatment) pair generate a synthetic binary‑outcome
    summary.

    The conversion probabilities are drawn uniformly from (0.01, 0.30) and
    successes are sampled from a binomial distribution.  A two‑proportion
    Z‑test is performed to obtain a p‑value.

    Returns:
        List of dicts, each representing a binary AB‑test summary.
    """
    logger.debug("Generating binary outcomes for %d records", len(sample_sizes))
    records = []
    for n_c, n_t in sample_sizes:
        # Random conversion probabilities
        p_c = random.uniform(0.01, 0.30)
        p_t = random.uniform(0.01, 0.30)

        # Simulate successes
        successes_c = np.random.binomial(n_c, p_c)
        successes_t = np.random.binomial(n_t, p_t)

        # Two‑proportion Z‑test
        count = np.array([successes_c, successes_t])
        nobs = np.array([n_c, n_t])
        stat, p_value = proportions_ztest(count, nobs)

        record = {
            "outcome_type": "binary",
            "n_control": n_c,
            "n_treatment": n_t,
            "conversion_control": successes_c / n_c,
            "conversion_treatment": successes_t / n_t,
            "p_value": float(p_value),
            # Fields that are only relevant for continuous outcomes are left empty.
            "mean_control": None,
            "mean_treatment": None,
            "std_control": None,
            "std_treatment": None,
        }
        records.append(record)
    return records


# --------------------------------------------------------------------------- #
# Continuous outcome generation
# --------------------------------------------------------------------------- #
def generate_continuous_outcome(sample_sizes: List[Tuple[int, int]]) -> List[Dict]:
    """
    For each (n_control, n_treatment) pair generate a synthetic continuous‑outcome
    summary.

    Means are drawn from (0.0, 100.0) and standard deviations from (5.0, 30.0).
    A Welch’s t‑test provides the p‑value.

    Returns:
        List of dicts, each representing a continuous AB‑test summary.
    """
    logger.debug("Generating continuous outcomes for %d records", len(sample_sizes))
    records = []
    for n_c, n_t in sample_sizes:
        mu_c = random.uniform(0.0, 100.0)
        mu_t = random.uniform(0.0, 100.0)
        sigma_c = random.uniform(5.0, 30.0)
        sigma_t = random.uniform(5.0, 30.0)

        # Simulate raw data
        data_c = np.random.normal(mu_c, sigma_c, n_c)
        data_t = np.random.normal(mu_t, sigma_t, n_t)

        # Welch's t‑test
        t_stat, p_value = stats.ttest_ind(data_c, data_t, equal_var=False)

        record = {
            "outcome_type": "continuous",
            "n_control": n_c,
            "n_treatment": n_t,
            "mean_control": float(np.mean(data_c)),
            "mean_treatment": float(np.mean(data_t)),
            "std_control": float(np.std(data_c, ddof=1)),
            "std_treatment": float(np.std(data_t, ddof=1)),
            "p_value": float(p_value),
            # Binary‑specific fields are left empty.
            "conversion_control": None,
            "conversion_treatment": None,
        }
        records.append(record)
    return records


# --------------------------------------------------------------------------- #
# Dataset orchestration
# --------------------------------------------------------------------------- #
def generate_synthetic_dataset(
    total_records: int = 10_000,
) -> List[Dict]:
    """
    Create a synthetic dataset containing *both* binary and continuous outcomes.

    The function guarantees that at least one record of each type is present.
    The split between binary and continuous is roughly 50/50 but is
    deterministic given the seeded RNG.

    Args:
        total_records: Minimum number of records to generate (default 10 000).

    Returns:
        List of summary dictionaries ready for serialization.
    """
    if total_records < 2:
        raise ValueError("At least two records are required to guarantee both outcome types.")

    logger.info("Generating synthetic dataset with %d total records", total_records)

    # Decide how many of each type – ensure at least one of each.
    half = total_records // 2
    binary_count = half
    continuous_count = total_records - binary_count

    # Generate sample‑size pairs for each subgroup.
    binary_sizes = generate_sample_sizes(binary_count)
    continuous_sizes = generate_sample_sizes(continuous_count)

    binary_records = generate_binary_outcome(binary_sizes)
    continuous_records = generate_continuous_outcome(continuous_sizes)

    dataset = binary_records + continuous_records
    random.shuffle(dataset)  # Randomise ordering for realism
    logger.debug("Synthetic dataset generation complete")
    return dataset


def verify_outcome_types(dataset: List[Dict]) -> None:
    """
    Ensure that the generated dataset contains *both* binary and continuous
    outcome types.  Raises ``ValueError`` if the constraint is violated.

    This function is called by ``main`` and also serves as a guard for any
    downstream code that consumes the synthetic data.
    """
    types = {record.get("outcome_type") for record in dataset}
    logger.debug("Outcome types present in dataset: %s", types)
    missing = {"binary", "continuous"} - types
    if missing:
        raise ValueError(
            f"Synthetic dataset missing required outcome type(s): {', '.join(missing)}"
        )


# --------------------------------------------------------------------------- #
# Serialization helpers
# --------------------------------------------------------------------------- #
def write_csv_output(dataset: List[Dict], output_path: Path) -> None:
    """
    Write the dataset to ``output_path`` as a CSV file.

    The CSV header contains all possible keys.  ``None`` values are written
    as empty strings for CSV compatibility.
    """
    logger.info("Writing CSV output to %s", output_path)
    if not dataset:
        logger.warning("Empty dataset – nothing to write")
        return

    fieldnames = sorted({key for record in dataset for key in record.keys()})

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in dataset:
            # Convert ``None`` to empty string for CSV
            sanitized = {k: ("" if v is None else v) for k, v in record.items()}
            writer.writerow(sanitized)


def write_json_output(dataset: List[Dict], output_path: Path) -> None:
    """
    Write the dataset to ``output_path`` as a JSON array (pretty‑printed).
    """
    logger.info("Writing JSON output to %s", output_path)
    with output_path.open("w", encoding="utf-8") as jsonfile:
        json.dump(dataset, jsonfile, indent=2, ensure_ascii=False)


def write_metadata(metadata: Dict, output_path: Path) -> None:
    """
    Write a small JSON metadata file describing the synthetic corpus.
    """
    logger.info("Writing metadata to %s", output_path)
    with output_path.open("w", encoding="utf-8") as meta_file:
        json.dump(metadata, meta_file, indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Execute the synthetic data generation pipeline.

    The function performs the following steps:

    1. Initialise all RNGs.
    2. Generate ≥ 10 000 summary records with both outcome types.
    3. Verify the presence of both binary and continuous outcomes.
    4. Persist the records to CSV and JSON files under ``data/``.
    5. Persist a short metadata file.
    """
    set_all_seeds()

    # 1️⃣ Generate the data
    dataset = generate_synthetic_dataset(total_records=10_000)

    # 2️⃣ Verify constraints
    verify_outcome_types(dataset)

    # 3️⃣ Prepare output locations
    data_dir = Path(__file__).resolve().parents[2] / "data"
    csv_path = data_dir / "synthetic_summaries.csv"
    json_path = data_dir / "synthetic_summaries.json"
    meta_path = data_dir / "synthetic_metadata.json"

    # Ensure the data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # 4️⃣ Write outputs
    write_csv_output(dataset, csv_path)
    write_json_output(dataset, json_path)

    # 5️⃣ Write metadata
    metadata = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "record_count": len(dataset),
        "outcome_type_counts": {
            "binary": sum(1 for r in dataset if r["outcome_type"] == "binary"),
            "continuous": sum(1 for r in dataset if r["outcome_type"] == "continuous"),
        },
        "seed": SEED,
    }
    write_metadata(metadata, meta_path)

    logger.info(
        "Synthetic dataset generation complete: %d records written to %s and %s",
        len(dataset),
        csv_path,
        json_path,
    )

# --------------------------------------------------------------------------- #
# Allow ``python -m src.audit.synthetic`` execution
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()