"""
Synthetic Dataset Generator for A/B Test Validity Evaluation (FR-030).

Generates a synthetic corpus of at least 10,000 A/B test summaries with
both binary and continuous outcomes. The data is generated using the
configured random seed to ensure reproducibility.

Output:
    data/synthetic/summaries.csv: The generated dataset.
    data/synthetic/metadata.json: Generation metadata and verification stats.
"""

import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants for generation
MIN_SAMPLES = 50
MAX_SAMPLES = 5000
BASELINE_RANGE = (0.05, 0.50)
EFFECT_SIZE_RANGE = (0.01, 0.15)
CONTINUOUS_MEAN_A = 10.0
CONTINUOUS_STD_A = 5.0
CONTINUOUS_EFFECT_RANGE = (0.5, 3.0)

logger = get_default_logger(__name__)


def set_all_seeds(seed: int = SEED) -> None:
    """Initialize all random number generators for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    set_rng_seed(seed)
    logger.info(f"Seeds initialized with value: {seed}")


def generate_sample_sizes() -> Tuple[int, int]:
    """Generate random sample sizes for control and treatment groups."""
    n_control = random.randint(MIN_SAMPLES, MAX_SAMPLES)
    n_treatment = random.randint(MIN_SAMPLES, MAX_SAMPLES)
    return n_control, n_treatment


def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: Optional[float] = None,
    effect_size: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate synthetic binary A/B test data.

    Args:
        n_control: Sample size for control group.
        n_treatment: Sample size for treatment group.
        baseline_rate: Conversion rate for control (if None, random).
        effect_size: Absolute lift for treatment (if None, random).

    Returns:
        Dictionary with counts and rates.
    """
    if baseline_rate is None:
        baseline_rate = random.uniform(*BASELINE_RANGE)
    if effect_size is None:
        # Randomly decide if effect is positive, negative, or null
        direction = random.choice([-1, 0, 1])
        magnitude = random.uniform(0, EFFECT_SIZE_RANGE[1])
        effect_size = direction * magnitude

    p_control = baseline_rate
    p_treatment = max(0.0, min(1.0, baseline_rate + effect_size))

    # Generate counts
    x_control = np.random.binomial(n_control, p_control)
    x_treatment = np.random.binomial(n_treatment, p_treatment)

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "x_control": int(x_control),
        "x_treatment": int(x_treatment),
        "p_control": float(p_control),
        "p_treatment": float(p_treatment),
        "effect_size": float(effect_size)
    }


def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    mean_a: Optional[float] = None,
    std_a: Optional[float] = None,
    effect_size: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate synthetic continuous A/B test data (means and standard deviations).

    Args:
        n_control: Sample size for control group.
        n_treatment: Sample size for treatment group.
        mean_a: Mean for control (if None, default).
        std_a: Std dev for control (if None, default).
        effect_size: Difference in means (if None, random).

    Returns:
        Dictionary with summary statistics.
    """
    if mean_a is None:
        mean_a = CONTINUOUS_MEAN_A
    if std_a is None:
        std_a = CONTINUOUS_STD_A
    if effect_size is None:
        direction = random.choice([-1, 0, 1])
        magnitude = random.uniform(0, CONTINUOUS_EFFECT_RANGE[1])
        effect_size = direction * magnitude

    mean_b = mean_a + effect_size
    # Assume equal variance for simplicity in generation
    std_b = std_a

    # Generate sample statistics (simulating what an extractor might see)
    # We simulate the sample mean and std dev that would result from a draw
    # to add realism, rather than just returning population params.
    sample_mean_a = np.random.normal(mean_a, std_a / np.sqrt(n_control))
    sample_std_a = std_a * np.sqrt(np.random.chisquare(n_control - 1) / (n_control - 1))

    sample_mean_b = np.random.normal(mean_b, std_b / np.sqrt(n_treatment))
    sample_std_b = std_b * np.sqrt(np.random.chisquare(n_treatment - 1) / (n_treatment - 1))

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": float(sample_mean_a),
        "mean_treatment": float(sample_mean_b),
        "std_control": float(sample_std_a),
        "std_treatment": float(sample_std_b),
        "effect_size": float(effect_size)
    }


def generate_synthetic_dataset(
    total_records: int = 10000,
    binary_ratio: float = 0.5,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Generate the full synthetic dataset.

    Args:
        total_records: Total number of summaries to generate (>= 10,000).
        binary_ratio: Proportion of records that are binary outcomes.
        output_dir: Directory to write the CSV file. Defaults to data/synthetic/.

    Returns:
        Path to the generated CSV file.
    """
    if total_records < 10000:
        logger.warning(f"Requested {total_records} records, but FR-030 requires >= 10,000. "
                       f"Proceeding with {total_records} but validation may fail.")

    if output_dir is None:
        output_dir = Path("data/synthetic")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "summaries.csv"

    binary_count = int(total_records * binary_ratio)
    continuous_count = total_records - binary_count

    logger.info(f"Generating {binary_count} binary and {continuous_count} continuous records.")

    records = []
    current_id = 1

    # Generate Binary Records
    for _ in range(binary_count):
        n_c, n_t = generate_sample_sizes()
        data = generate_binary_outcome(n_c, n_t)
        record = {
            "id": current_id,
            "outcome_type": "binary",
            "n_control": data["n_control"],
            "n_treatment": data["n_treatment"],
            "success_control": data["x_control"],
            "success_treatment": data["x_treatment"],
            "rate_control": data["p_control"],
            "rate_treatment": data["p_treatment"],
            "effect_size": data["effect_size"],
            "metric_name": "conversion_rate",
            "domain": random.choice(["tech", "finance", "health", "retail", "education"]),
            "year": random.randint(2018, 2025)
        }
        records.append(record)
        current_id += 1

    # Generate Continuous Records
    for _ in range(continuous_count):
        n_c, n_t = generate_sample_sizes()
        data = generate_continuous_outcome(n_c, n_t)
        record = {
            "id": current_id,
            "outcome_type": "continuous",
            "n_control": data["n_control"],
            "n_treatment": data["n_treatment"],
            "mean_control": data["mean_control"],
            "mean_treatment": data["mean_treatment"],
            "std_control": data["std_control"],
            "std_treatment": data["std_treatment"],
            "effect_size": data["effect_size"],
            "metric_name": "average_order_value",
            "domain": random.choice(["tech", "finance", "health", "retail", "education"]),
            "year": random.randint(2018, 2025)
        }
        records.append(record)
        current_id += 1

    # Shuffle to mix types
    random.shuffle(records)

    # Write CSV
    fieldnames = [
        "id", "outcome_type", "n_control", "n_treatment",
        "success_control", "success_treatment", "rate_control", "rate_treatment",
        "mean_control", "mean_treatment", "std_control", "std_treatment",
        "effect_size", "metric_name", "domain", "year"
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Synthetic dataset written to {output_file}")
    return output_file


def verify_outcome_types(file_path: Path) -> Dict[str, Any]:
    """
    Verify that the generated file contains both binary and continuous outcomes
    and meets the count requirement.

    Returns:
        Dictionary with verification results.
    """
    binary_count = 0
    continuous_count = 0
    total_count = 0

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_count += 1
            if row["outcome_type"] == "binary":
                binary_count += 1
            elif row["outcome_type"] == "continuous":
                continuous_count += 1

    results = {
        "total_records": total_count,
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "meets_count_requirement": total_count >= 10000,
        "has_both_outcomes": binary_count > 0 and continuous_count > 0
    }

    if not results["meets_count_requirement"]:
        logger.error(f"Record count {total_count} is less than required 10,000.")
    if not results["has_both_outcomes"]:
        logger.error("Missing one or both outcome types.")

    return results


def write_metadata(output_dir: Path, verification_results: Dict[str, Any]) -> Path:
    """Write generation metadata to a JSON file."""
    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "seed": SEED,
        "verification": verification_results,
        "constraints_satisfied": verification_results["meets_count_requirement"] and verification_results["has_both_outcomes"]
    }
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata written to {metadata_path}")
    return metadata_path


def main() -> int:
    """Main entry point for the synthetic dataset generator."""
    set_all_seeds()

    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Generate dataset
        csv_path = generate_synthetic_dataset(total_records=10500)

        # Verify
        verification = verify_outcome_types(csv_path)

        if not verification["meets_count_requirement"] or not verification["has_both_outcomes"]:
            logger.error("Verification failed. Constraints not met.")
            return 1

        # Write metadata
        write_metadata(output_dir, verification)

        logger.info("Synthetic dataset generation completed successfully.")
        return 0

    except Exception as e:
        logger.exception(f"Failed to generate synthetic dataset: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
