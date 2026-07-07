"""
Synthetic Dataset Generator for A/B Test Validation (FR-030)

Generates a synthetic dataset of at least 10,000 simulated A/B test summaries
including both binary and continuous outcomes. The data is generated using
deterministic seeds to ensure reproducibility and statistical validity.

Output:
  - data/synthetic/summaries.csv: The generated dataset
  - data/synthetic/metadata.json: Generation metadata and verification stats
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

# Ensure output directories exist
OUTPUT_DIR = Path("data/synthetic")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger = get_default_logger()

def set_all_seeds(seed: int = SEED) -> None:
    """Set all random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logging.getLogger().setLevel(logging.INFO)

def generate_sample_sizes(n_min: int = 50, n_max: int = 5000) -> Tuple[int, int]:
    """Generate random sample sizes for control and treatment groups."""
    n_control = np.random.randint(n_min, n_max)
    n_treatment = np.random.randint(n_min, n_max)
    return int(n_control), int(n_treatment)

def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: float,
    effect_size: float,
    seed: int
) -> Dict[str, Any]:
    """
    Generate binary outcome data (e.g., conversion rates).

    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_rate: Conversion rate for control group (0-1)
        effect_size: Relative effect size (e.g., 0.1 for 10% lift)
        seed: Random seed for this specific generation

    Returns:
        Dictionary with generated metrics
    """
    # Set seed for this specific generation to ensure reproducibility
    local_rng = np.random.RandomState(seed)

    # Calculate treatment rate
    treatment_rate = baseline_rate * (1 + effect_size)
    treatment_rate = np.clip(treatment_rate, 0.0, 1.0)

    # Generate counts
    x_control = local_rng.binomial(1, baseline_rate, n_control).sum()
    x_treatment = local_rng.binomial(1, treatment_rate, n_treatment).sum()

    # Calculate p-value using two-proportion z-test
    # Note: We use the actual generated counts to compute the p-value
    # to ensure statistical consistency in the generated data
    p_value = stats.proportions_ztest(
        [x_control, x_treatment],
        [n_control, n_treatment]
    )[1]

    # Calculate effect size (absolute difference)
    effect = treatment_rate - baseline_rate

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "x_control": int(x_control),
        "x_treatment": int(x_treatment),
        "baseline_rate": float(baseline_rate),
        "treatment_rate": float(treatment_rate),
        "p_value": float(p_value),
        "effect_size": float(effect),
        "outcome_type": "binary"
    }

def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    baseline_mean: float,
    effect_size: float,
    std_dev: float,
    seed: int
) -> Dict[str, Any]:
    """
    Generate continuous outcome data (e.g., average order value).

    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_mean: Mean for control group
        effect_size: Absolute effect size (difference in means)
        std_dev: Standard deviation for both groups
        seed: Random seed for this specific generation

    Returns:
        Dictionary with generated metrics
    """
    # Set seed for this specific generation
    local_rng = np.random.RandomState(seed)

    # Generate data
    control_data = local_rng.normal(baseline_mean, std_dev, n_control)
    treatment_data = local_rng.normal(baseline_mean + effect_size, std_dev, n_treatment)

    # Calculate statistics
    mean_control = np.mean(control_data)
    mean_treatment = np.mean(treatment_data)
    std_control = np.std(control_data, ddof=1)
    std_treatment = np.std(treatment_data, ddof=1)

    # Calculate p-value using Welch's t-test
    t_stat, p_value = stats.ttest_ind(
        control_data,
        treatment_data,
        equal_var=False
    )

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": float(mean_control),
        "mean_treatment": float(mean_treatment),
        "std_control": float(std_control),
        "std_treatment": float(std_treatment),
        "p_value": float(p_value),
        "effect_size": float(effect_size),
        "outcome_type": "continuous"
    }

def generate_synthetic_dataset(
    total_records: int = 10000,
    binary_ratio: float = 0.5,
    seed: int = SEED
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.

    Args:
        total_records: Total number of records to generate
        binary_ratio: Ratio of binary outcomes (0.0 to 1.0)
        seed: Random seed for reproducibility

    Returns:
        List of generated summary dictionaries
    """
    set_all_seeds(seed)
    logger.info(f"Generating synthetic dataset with {total_records} records...")

    records = []
    binary_count = int(total_records * binary_ratio)
    continuous_count = total_records - binary_count

    # Generate binary outcomes
    for i in range(binary_count):
        n_control, n_treatment = generate_sample_sizes()
        baseline_rate = np.random.uniform(0.05, 0.50)
        # Generate effect sizes that are sometimes significant, sometimes not
        effect_size = np.random.choice([-0.1, 0.0, 0.1, 0.2]) * np.random.uniform(0.5, 1.5)
        record = generate_binary_outcome(
            n_control, n_treatment, baseline_rate, effect_size, seed + i
        )
        record["id"] = f"B{i:05d}"
        record["domain"] = np.random.choice(
            ["tech", "finance", "health", "retail", "education"]
        )
        record["year"] = np.random.randint(2020, 2025)
        records.append(record)

    # Generate continuous outcomes
    for i in range(continuous_count):
        n_control, n_treatment = generate_sample_sizes()
        baseline_mean = np.random.uniform(10.0, 100.0)
        std_dev = np.random.uniform(5.0, 20.0)
        effect_size = np.random.choice([-5.0, 0.0, 5.0, 10.0]) * np.random.uniform(0.5, 1.5)
        record = generate_continuous_outcome(
            n_control, n_treatment, baseline_mean, effect_size, std_dev, seed + binary_count + i
        )
        record["id"] = f"C{i:05d}"
        record["domain"] = np.random.choice(
            ["tech", "finance", "health", "retail", "education"]
        )
        record["year"] = np.random.randint(2020, 2025)
        records.append(record)

    logger.info(f"Generated {len(records)} records ({binary_count} binary, {continuous_count} continuous)")
    return records

def verify_outcome_types(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verify that both binary and continuous outcomes are present.

    Args:
        records: List of generated records

    Returns:
        Verification statistics
    """
    binary_count = sum(1 for r in records if r["outcome_type"] == "binary")
    continuous_count = sum(1 for r in records if r["outcome_type"] == "continuous")
    total = len(records)

    result = {
        "total_records": total,
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "binary_percentage": (binary_count / total * 100) if total > 0 else 0,
        "continuous_percentage": (continuous_count / total * 100) if total > 0 else 0,
        "meets_minimum": total >= 10000,
        "has_both_types": binary_count > 0 and continuous_count > 0
    }

    logger.info(f"Verification: {binary_count} binary, {continuous_count} continuous")
    logger.info(f"Meets minimum (>=10000): {result['meets_minimum']}")
    logger.info(f"Has both types: {result['has_both_types']}")

    return result

def write_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """Write generation metadata to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, default=str)
    logger.info(f"Metadata written to {output_path}")

def write_summaries(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write generated summaries to CSV file."""
    if not records:
        logger.error("No records to write")
        return

    fieldnames = [
        "id", "outcome_type", "n_control", "n_treatment",
        "baseline_rate", "treatment_rate", "mean_control", "mean_treatment",
        "std_control", "std_treatment", "x_control", "x_treatment",
        "p_value", "effect_size", "domain", "year"
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Summaries written to {output_path}")

def main() -> int:
    """Main entry point for synthetic dataset generation."""
    try:
        logger.info("Starting synthetic dataset generation (Task T026)")

        # Generate dataset
        records = generate_synthetic_dataset(
            total_records=10000,
            binary_ratio=0.5,
            seed=SEED
        )

        # Verify outcome types
        verification = verify_outcome_types(records)

        if not verification["meets_minimum"]:
            logger.error("Generated dataset does not meet minimum record count (10,000)")
            return 1

        if not verification["has_both_types"]:
            logger.error("Generated dataset missing one or both outcome types")
            return 1

        # Write outputs
        csv_path = OUTPUT_DIR / "summaries.csv"
        write_summaries(records, csv_path)

        metadata = {
            "generated_at": datetime.utcnow().isoformat(),
            "seed": SEED,
            "total_records": len(records),
            "verification": verification,
            "file_path": str(csv_path)
        }

        metadata_path = OUTPUT_DIR / "metadata.json"
        write_metadata(metadata, metadata_path)

        logger.info("Synthetic dataset generation completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Error during synthetic dataset generation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
