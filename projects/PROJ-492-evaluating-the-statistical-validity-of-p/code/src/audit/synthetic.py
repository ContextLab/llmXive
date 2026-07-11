"""
Synthetic Dataset Generator for A/B Test Validity Audit (FR-030).

Generates a synthetic corpus of A/B test summaries with both binary and continuous
outcomes. The generator ensures statistical consistency where possible (to test
the validator's ability to find inconsistencies) and includes realistic noise.

Outputs:
    data/synthetic/summaries.csv: The main dataset of synthetic A/B test summaries.
    data/synthetic/metadata.json: Metadata about the generation process.
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

from code.src.config import SEED, set_rng_seed
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger

# Configuration
TARGET_RECORD_COUNT = 10000
BINARY_RATIO = 0.6  # 60% binary, 40% continuous
DOMAINS = ["tech", "health", "finance", "retail", "education"]
YEARS = list(range(2018, 2025))

logger = get_default_logger(__name__)

def set_all_seeds(seed: int = SEED) -> None:
    """Seed all random number generators for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeded all RNGs with {seed}")

def generate_sample_sizes() -> Tuple[int, int]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Uses a log-normal distribution to mimic real-world variance.
    """
    # Typical A/B tests range from 100 to 100,000 per group
    base_n = int(np.random.lognormal(mean=6.0, sigma=1.0))
    base_n = max(100, min(base_n, 200000))  # Clamp to realistic bounds

    # Control and treatment sizes are usually close but not identical
    ratio = np.random.uniform(0.9, 1.1)
    n_control = base_n
    n_treatment = int(base_n * ratio)

    return n_control, n_treatment

def generate_binary_outcome(
    n_control: int, n_treatment: int, baseline_rate: float, effect_size: float, consistent: bool = True
) -> Dict[str, Any]:
    """
    Generate binary outcome data (conversions).

    Args:
        n_control: Sample size for control.
        n_treatment: Sample size for treatment.
        baseline_rate: Expected conversion rate for control.
        effect_size: Lift in conversion rate for treatment (e.g., 0.1 for 10% lift).
        consistent: If True, p-value will be calculated consistently with the data.
                    If False, injects a discrepancy (e.g., wrong p-value).

    Returns:
        Dict with conversions and p-value.
    """
    # Generate actual conversions
    p_control = baseline_rate
    p_treatment = baseline_rate * (1 + effect_size)

    # Ensure probabilities stay within [0, 1]
    p_treatment = max(0.0, min(1.0, p_treatment))

    x_control = np.random.binomial(n_control, p_control)
    x_treatment = np.random.binomial(n_treatment, p_treatment)

    # Calculate true p-value using two-proportion z-test
    from scipy import stats

    stat, true_p = stats.proportions_ztest([x_control, x_treatment], [n_control, n_treatment])

    if consistent:
        reported_p = true_p
    else:
        # Inject inconsistency: report a p-value that is significantly different
        # e.g., if true p < 0.05, report > 0.10, or vice versa
        if true_p < 0.05:
            reported_p = np.random.uniform(0.08, 0.20)
        else:
            reported_p = np.random.uniform(0.001, 0.04)

    return {
        "conversions_control": int(x_control),
        "conversions_treatment": int(x_treatment),
        "p_value": float(reported_p),
        "true_p_value": float(true_p),
    }

def generate_continuous_outcome(
    n_control: int, n_treatment: int, baseline_mean: float, effect_size: float, consistent: bool = True
) -> Dict[str, Any]:
    """
    Generate continuous outcome data (e.g., revenue per user).

    Args:
        n_control: Sample size for control.
        n_treatment: Sample size for treatment.
        baseline_mean: Expected mean for control.
        effect_size: Difference in means for treatment.
        consistent: If True, p-value consistent with data.

    Returns:
        Dict with means, std devs, and p-value.
    """
    # Generate data
    mean_control = baseline_mean
    mean_treatment = baseline_mean + effect_size
    std_dev = baseline_mean * 0.5  # Assume 50% coefficient of variation

    # Ensure means are positive
    mean_treatment = max(0.01, mean_treatment)

    data_control = np.random.normal(mean_control, std_dev, n_control)
    data_treatment = np.random.normal(mean_treatment, std_dev, n_treatment)

    # Calculate statistics
    mean_c = np.mean(data_control)
    mean_t = np.mean(data_treatment)
    std_c = np.std(data_control, ddof=1)
    std_t = np.std(data_treatment, ddof=1)

    # Avoid division by zero
    if std_c == 0: std_c = 0.001
    if std_t == 0: std_t = 0.001

    # True p-value using Welch's t-test
    from scipy import stats

    stat, true_p = stats.ttest_ind(data_control, data_treatment, equal_var=False)

    if consistent:
        reported_p = true_p
    else:
        # Inject inconsistency
        if true_p < 0.05:
            reported_p = np.random.uniform(0.08, 0.20)
        else:
            reported_p = np.random.uniform(0.001, 0.04)

    return {
        "mean_control": float(mean_c),
        "mean_treatment": float(mean_t),
        "std_control": float(std_c),
        "std_treatment": float(std_t),
        "p_value": float(reported_p),
        "true_p_value": float(true_p),
    }

def generate_synthetic_dataset(
    n_records: int = TARGET_RECORD_COUNT,
    inconsistent_ratio: float = 0.15,
    output_dir: str = "data/synthetic",
) -> Path:
    """
    Generate the full synthetic dataset.

    Args:
        n_records: Total number of records to generate.
        inconsistent_ratio: Fraction of records with statistical inconsistencies.
        output_dir: Directory to write output files.

    Returns:
        Path to the generated CSV file.
    """
    set_all_seeds()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    records = []
    inconsistent_count = 0

    logger.info(f"Generating {n_records} synthetic A/B test summaries...")

    for i in range(n_records):
        # Determine outcome type
        is_binary = random.random() < BINARY_RATIO
        is_inconsistent = random.random() < inconsistent_ratio
        if is_inconsistent:
            inconsistent_count += 1

        domain = random.choice(DOMAINS)
        year = random.choice(YEARS)
        n_control, n_treatment = generate_sample_sizes()

        if is_binary:
            baseline_rate = np.random.uniform(0.05, 0.30)
            effect_size = np.random.choice([-0.1, 0.0, 0.1, 0.2]) # Negative, null, positive
            data = generate_binary_outcome(n_control, n_treatment, baseline_rate, effect_size, consistent=not is_inconsistent)

            record = {
                "id": f"syn_{i:05d}",
                "domain": domain,
                "year": year,
                "outcome_type": "binary",
                "n_control": n_control,
                "n_treatment": n_treatment,
                "baseline_rate": baseline_rate,
                "treatment_rate": (data["conversions_treatment"] / n_treatment) if n_treatment > 0 else 0,
                "conversions_control": data["conversions_control"],
                "conversions_treatment": data["conversions_treatment"],
                "p_value": data["p_value"],
                "test_type": "z_test", # Default for binary
                "consistent": not is_inconsistent,
            }
        else:
            baseline_mean = np.random.uniform(10.0, 100.0)
            effect_size = np.random.choice([-5.0, 0.0, 5.0, 10.0])
            data = generate_continuous_outcome(n_control, n_treatment, baseline_mean, effect_size, consistent=not is_inconsistent)

            record = {
                "id": f"syn_{i:05d}",
                "domain": domain,
                "year": year,
                "outcome_type": "continuous",
                "n_control": n_control,
                "n_treatment": n_treatment,
                "baseline_mean": baseline_mean,
                "treatment_mean": data["mean_treatment"],
                "mean_control": data["mean_control"],
                "mean_treatment": data["mean_treatment"],
                "std_control": data["std_control"],
                "std_treatment": data["std_treatment"],
                "p_value": data["p_value"],
                "test_type": "welch_t", # Default for continuous
                "consistent": not is_inconsistent,
            }

        records.append(record)

    # Write CSV
    csv_path = output_path / "summaries.csv"
    fieldnames = list(records[0].keys())

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    # Write Metadata
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "total_records": n_records,
        "inconsistent_count": inconsistent_count,
        "inconsistent_ratio": inconsistent_ratio,
        "binary_count": sum(1 for r in records if r["outcome_type"] == "binary"),
        "continuous_count": sum(1 for r in records if r["outcome_type"] == "continuous"),
        "domains": DOMAINS,
        "years": YEARS,
        "seed": SEED,
        "fr_030_compliant": True,
    }

    meta_path = output_path / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Generated {n_records} records. Inconsistent: {inconsistent_count} ({inconsistent_ratio*100:.1f}%)")
    logger.info(f"Wrote CSV to {csv_path}")
    logger.info(f"Wrote metadata to {meta_path}")

    return csv_path

def verify_outcome_types(csv_path: Path) -> bool:
    """Verify that the generated CSV contains both binary and continuous outcomes."""
    if not csv_path.exists():
        return False

    has_binary = False
    has_continuous = False

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["outcome_type"] == "binary":
                has_binary = True
            elif row["outcome_type"] == "continuous":
                has_continuous = True
            if has_binary and has_continuous:
                return True

    return has_binary and has_continuous

def write_summaries_to_csv(records: List[Dict], path: Path) -> None:
    """Helper to write records to CSV (used by main if needed)."""
    if not records:
        return
    fieldnames = records[0].keys()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def write_metadata(metadata: Dict, path: Path) -> None:
    """Helper to write metadata to JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

def main() -> None:
    """Entry point for the synthetic dataset generator."""
    logger.info("Starting synthetic dataset generation (T026)...")
    try:
        csv_path = generate_synthetic_dataset(
            n_records=TARGET_RECORD_COUNT,
            inconsistent_ratio=0.15,
            output_dir="data/synthetic"
        )

        if verify_outcome_types(csv_path):
            logger.info("Verification passed: Both binary and continuous outcomes present.")
        else:
            logger.error("Verification failed: Missing outcome types.")
            raise RuntimeError("Outcome type verification failed.")

        record_count = sum(1 for _ in open(csv_path)) - 1 # subtract header
        if record_count < 10000:
            logger.error(f"Record count {record_count} is less than required 10,000.")
            raise RuntimeError(f"Insufficient records: {record_count}")

        logger.info(f"Task T026 completed successfully. Output: {csv_path}")

    except Exception as e:
        logger.error(f"Task T026 failed: {e}")
        raise

if __name__ == "__main__":
    main()
