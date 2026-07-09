"""
Synthetic dataset generator for A/B test summary validation (FR-030).
Generates at least 10,000 simulated summaries with both binary and continuous outcomes.
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants
MIN_RECORDS = 10000
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
OUTPUT_DIR = Path("data/synthetic")
OUTPUT_FILE = OUTPUT_DIR / "synthetic_summaries.csv"
METADATA_FILE = OUTPUT_DIR / "synthetic_metadata.json"

logger: AuditLogger = get_default_logger("synthetic_generator")


def set_all_seeds(seed: int = SEED) -> None:
    """Seed all random number generators for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)


def generate_sample_sizes() -> Tuple[int, int]:
    """Generate realistic sample sizes for control and treatment groups."""
    # Sample sizes typically range from 100 to 10000
    n_control = np.random.randint(100, 10000)
    n_treatment = np.random.randint(100, 10000)
    return n_control, n_treatment


def generate_binary_outcome(n_control: int, n_treatment: int) -> Dict[str, Any]:
    """
    Generate a synthetic binary A/B test summary.
    Returns conversion rates, success counts, and a reported p-value.
    """
    # Base conversion rate between 0.01 and 0.30
    base_rate = np.random.uniform(0.01, 0.30)

    # Effect size: small to moderate (0% to 15% relative change)
    effect_magnitude = np.random.uniform(0.0, 0.15)
    effect_direction = np.random.choice([-1, 1])
    treatment_rate = base_rate * (1 + effect_direction * effect_magnitude)

    # Clamp rates to valid range
    treatment_rate = max(0.001, min(0.999, treatment_rate))

    # Generate success counts (binomial distribution)
    successes_control = np.random.binomial(n_control, base_rate)
    successes_treatment = np.random.binomial(n_treatment, treatment_rate)

    # Calculate observed rates
    rate_control = successes_control / n_control if n_control > 0 else 0.0
    rate_treatment = successes_treatment / n_treatment if n_treatment > 0 else 0.0

    # Calculate p-value using two-proportion z-test
    if successes_control > 0 and successes_treatment > 0 and n_control > 0 and n_treatment > 0:
        pooled_rate = (successes_control + successes_treatment) / (n_control + n_treatment)
        se = np.sqrt(pooled_rate * (1 - pooled_rate) * (1/n_control + 1/n_treatment))
        if se > 0:
            z_stat = (rate_treatment - rate_control) / se
            p_value = 2 * (1 - abs(stats.norm.cdf(z_stat)))
        else:
            p_value = 1.0
    else:
        p_value = 1.0

    return {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "rate_control": float(rate_control),
        "rate_treatment": float(rate_treatment),
        "p_value": float(p_value),
        "effect_size": float(rate_treatment - rate_control)
    }


def generate_continuous_outcome(n_control: int, n_treatment: int) -> Dict[str, Any]:
    """
    Generate a synthetic continuous A/B test summary.
    Returns means, standard deviations, and a reported p-value.
    """
    # Base mean between 10 and 100
    base_mean = np.random.uniform(10, 100)

    # Standard deviation typically 10-30% of mean
    std_dev = base_mean * np.random.uniform(0.1, 0.3)

    # Effect size: small to moderate (0% to 10% relative change)
    effect_magnitude = np.random.uniform(0.0, 0.10)
    effect_direction = np.random.choice([-1, 1])
    treatment_mean = base_mean * (1 + effect_direction * effect_magnitude)

    # Generate sample data
    control_data = np.random.normal(base_mean, std_dev, n_control)
    treatment_data = np.random.normal(treatment_mean, std_dev, n_treatment)

    # Calculate observed statistics
    mean_control = float(np.mean(control_data))
    mean_treatment = float(np.mean(treatment_data))
    std_control = float(np.std(control_data, ddof=1))
    std_treatment = float(np.std(treatment_data, ddof=1))

    # Calculate p-value using Welch's t-test
    if n_control > 1 and n_treatment > 1:
        t_stat, p_value = stats.ttest_ind_from_stats(
            mean_control, std_control, n_control,
            mean_treatment, std_treatment, n_treatment,
            equal_var=False
        )
    else:
        p_value = 1.0

    return {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": mean_control,
        "mean_treatment": mean_treatment,
        "std_control": std_control,
        "std_treatment": std_treatment,
        "p_value": float(p_value),
        "effect_size": float(mean_treatment - mean_control)
    }


def generate_synthetic_dataset(num_records: int = MIN_RECORDS) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.
    Ensures both binary and continuous outcomes are present.
    """
    set_all_seeds()

    records = []
    num_binary = int(num_records * BINARY_RATIO)
    num_continuous = num_records - num_binary

    logger.info(f"Generating {num_binary} binary and {num_continuous} continuous summaries")

    # Generate binary outcomes
    for i in range(num_binary):
        n_c, n_t = generate_sample_sizes()
        record = generate_binary_outcome(n_c, n_t)
        record["id"] = f"synthetic_binary_{i:05d}"
        record["domain"] = random.choice(["tech", "finance", "health", "retail", "education"])
        record["year"] = random.randint(2020, 2025)
        records.append(record)

    # Generate continuous outcomes
    for i in range(num_continuous):
        n_c, n_t = generate_sample_sizes()
        record = generate_continuous_outcome(n_c, n_t)
        record["id"] = f"synthetic_continuous_{i:05d}"
        record["domain"] = random.choice(["tech", "finance", "health", "retail", "education"])
        record["year"] = random.randint(2020, 2025)
        records.append(record)

    # Shuffle to mix outcome types
    random.shuffle(records)

    return records


def verify_outcome_types(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Verify that both outcome types are present in the generated dataset."""
    binary_count = sum(1 for r in records if r["outcome_type"] == "binary")
    continuous_count = sum(1 for r in records if r["outcome_type"] == "continuous")

    logger.info(f"Verification: {binary_count} binary, {continuous_count} continuous")

    if binary_count == 0:
        raise ValueError("No binary outcomes generated!")
    if continuous_count == 0:
        raise ValueError("No continuous outcomes generated!")
    if len(records) < MIN_RECORDS:
        raise ValueError(f"Generated {len(records)} records, expected at least {MIN_RECORDS}")

    return binary_count, continuous_count


def write_metadata(records: List[Dict[str, Any]], binary_count: int, continuous_count: int) -> None:
    """Write metadata about the generated dataset."""
    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(records),
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "seed": SEED,
        "output_file": str(OUTPUT_FILE),
        "domains": list(set(r["domain"] for r in records)),
        "years": sorted(list(set(r["year"] for r in records)))
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Metadata written to {METADATA_FILE}")


def write_summaries_to_csv(records: List[Dict[str, Any]]) -> None:
    """Write synthetic summaries to CSV file."""
    if not records:
        raise ValueError("No records to write!")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = list(records[0].keys())
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Wrote {len(records)} records to {OUTPUT_FILE}")


def main() -> int:
    """Main entry point for synthetic dataset generation."""
    try:
        logger.info("Starting synthetic dataset generation")

        # Generate dataset
        records = generate_synthetic_dataset(MIN_RECORDS)

        # Verify outcome types
        binary_count, continuous_count = verify_outcome_types(records)

        # Write outputs
        write_summaries_to_csv(records)
        write_metadata(records, binary_count, continuous_count)

        logger.info(f"Successfully generated {len(records)} synthetic summaries "
                   f"({binary_count} binary, {continuous_count} continuous)")

        return 0

    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
