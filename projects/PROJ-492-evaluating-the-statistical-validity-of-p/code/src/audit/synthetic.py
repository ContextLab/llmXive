"""
Synthetic Dataset Generator for A/B Test Validity Audit.

Generates a large corpus of simulated A/B test summaries with known ground truth
to validate the statistical reconstruction and inconsistency detection pipeline.

Produces both binary (proportion) and continuous (mean difference) outcomes.
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)

# Constants for generation
MIN_SAMPLE_SIZE = 50
MAX_SAMPLE_SIZE = 50000
BASELINE_PROPORTION_RANGE = (0.05, 0.95)
EFFECT_SIZE_BINARY_RANGE = (-0.15, 0.15)  # Absolute difference in proportions
BASELINE_MEAN_RANGE = (10.0, 100.0)
EFFECT_SIZE_CONTINUOUS_RANGE = (-5.0, 5.0)  # Absolute difference in means
STD_DEV_RANGE = (1.0, 20.0)
DOMAINS = ["tech", "health", "finance", "retail", "education"]
YEARS = list(range(2018, 2025))

def set_all_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed}")

def generate_sample_sizes(n: int) -> Tuple[int, int]:
    """Generate two sample sizes for control and treatment groups."""
    # Prefer similar sizes but allow some variation
    n1 = np.random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
    variation = np.random.uniform(0.8, 1.2)
    n2 = int(n1 * variation)
    n2 = max(MIN_SAMPLE_SIZE, min(n2, MAX_SAMPLE_SIZE))
    return int(n1), int(n2)

def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_p: Optional[float] = None,
    effect_size: Optional[float] = None,
    inject_inconsistency: bool = False,
) -> Dict[str, Any]:
    """
    Generate a binary outcome A/B test summary.

    Returns a dictionary with ground truth and reported values.
    If inject_inconsistency is True, the reported p-value will be manipulated.
    """
    if baseline_p is None:
        baseline_p = np.random.uniform(*BASELINE_PROPORTION_RANGE)
    if effect_size is None:
        effect_size = np.random.uniform(*EFFECT_SIZE_BINARY_RANGE)

    p_treatment = baseline_p + effect_size
    p_treatment = max(0.01, min(0.99, p_treatment))

    # Generate actual counts
    successes_control = np.random.binomial(n_control, baseline_p)
    successes_treatment = np.random.binomial(n_treatment, p_treatment)

    # Calculate true p-value using two-proportion z-test
    p_hat_pooled = (successes_control + successes_treatment) / (n_control + n_treatment)
    se = np.sqrt(p_hat_pooled * (1 - p_hat_pooled) * (1/n_control + 1/n_treatment))
    z_stat = (successes_treatment / n_treatment - successes_control / n_control) / se
    true_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    # Reported values
    reported_p_value = true_p_value
    if inject_inconsistency:
        # Inject a significant discrepancy (e.g., report p=0.01 when true is > 0.1)
        if true_p_value > 0.1:
            reported_p_value = 0.01
        else:
            reported_p_value = 0.5

    return {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "baseline_proportion": baseline_p,
        "treatment_proportion": p_treatment,
        "effect_size": effect_size,
        "true_p_value": true_p_value,
        "reported_p_value": reported_p_value,
        "is_inconsistent": inject_inconsistency,
    }

def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    baseline_mean: Optional[float] = None,
    effect_size: Optional[float] = None,
    std_dev: Optional[float] = None,
    inject_inconsistency: bool = False,
) -> Dict[str, Any]:
    """
    Generate a continuous outcome A/B test summary.

    Returns a dictionary with ground truth and reported values.
    """
    if baseline_mean is None:
        baseline_mean = np.random.uniform(*BASELINE_MEAN_RANGE)
    if effect_size is None:
        effect_size = np.random.uniform(*EFFECT_SIZE_CONTINUOUS_RANGE)
    if std_dev is None:
        std_dev = np.random.uniform(*STD_DEV_RANGE)

    mean_control = baseline_mean
    mean_treatment = baseline_mean + effect_size

    # Generate sample data (we only need summary stats for the output)
    # Simulate data to compute true statistics
    data_control = np.random.normal(mean_control, std_dev, n_control)
    data_treatment = np.random.normal(mean_treatment, std_dev, n_treatment)

    # Welch's t-test
    t_stat, true_p_value = stats.ttest_ind(
        data_control, data_treatment, equal_var=False
    )

    # Reported values
    reported_p_value = true_p_value
    if inject_inconsistency:
        # Inject discrepancy
        if true_p_value > 0.1:
            reported_p_value = 0.01
        else:
            reported_p_value = 0.5

    return {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": float(np.mean(data_control)),
        "mean_treatment": float(np.mean(data_treatment)),
        "std_control": float(np.std(data_control, ddof=1)),
        "std_treatment": float(np.std(data_treatment, ddof=1)),
        "baseline_mean": baseline_mean,
        "effect_size": effect_size,
        "std_dev": std_dev,
        "true_p_value": true_p_value,
        "reported_p_value": reported_p_value,
        "is_inconsistent": inject_inconsistency,
    }

def generate_synthetic_dataset(
    n_records: int = 10000,
    output_dir: str = "data/synthetic",
    seed: int = SEED,
    inconsistency_rate: float = 0.15,
) -> Tuple[Path, Path]:
    """
    Generate a synthetic dataset of A/B test summaries.

    Args:
        n_records: Number of records to generate (minimum 10,000).
        output_dir: Directory to write output files.
        seed: Random seed for reproducibility.
        inconsistency_rate: Proportion of records with injected inconsistencies.

    Returns:
        Tuple of (path to summaries CSV, path to ground truth JSON).
    """
    set_all_seeds(seed)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    summaries_path = output_path / "synthetic_summaries.csv"
    ground_truth_path = output_path / "synthetic_ground_truth.json"

    summaries = []
    ground_truth = []

    # Ensure we have a mix of binary and continuous
    n_binary = n_records // 2
    n_continuous = n_records - n_binary

    logger.info(f"Generating {n_binary} binary and {n_continuous} continuous outcomes...")

    for i in range(n_records):
        is_binary = i < n_binary
        inject_inconsistency = random.random() < inconsistency_rate

        n1, n2 = generate_sample_sizes(1000)  # Base size for generation

        if is_binary:
            data = generate_binary_outcome(
                n1, n2, inject_inconsistency=inject_inconsistency
            )
        else:
            data = generate_continuous_outcome(
                n1, n2, inject_inconsistency=inject_inconsistency
            )

        # Add metadata
        domain = random.choice(DOMAINS)
        year = random.choice(YEARS)

        # Create summary record (what the extractor would see)
        summary_record = {
            "id": f"syn_{i:06d}",
            "domain": domain,
            "year": year,
            "outcome_type": data["outcome_type"],
            "n_control": data["n_control"],
            "n_treatment": data["n_treatment"],
            "reported_p_value": data["reported_p_value"],
            "effect_size": data["effect_size"],
            "baseline_rate": data.get("baseline_proportion", data.get("baseline_mean")),
            "treatment_rate": data.get("treatment_proportion", data.get("mean_treatment")),
        }

        # Create ground truth record
        truth_record = {
            "id": f"syn_{i:06d}",
            "true_p_value": data["true_p_value"],
            "is_inconsistent": data["is_inconsistent"],
            "outcome_type": data["outcome_type"],
            "full_details": data,
        }

        summaries.append(summary_record)
        ground_truth.append(truth_record)

    # Write summaries to CSV
    fieldnames = [
        "id", "domain", "year", "outcome_type", "n_control", "n_treatment",
        "reported_p_value", "effect_size", "baseline_rate", "treatment_rate"
    ]
    with open(summaries_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)

    # Write ground truth to JSON
    with open(ground_truth_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    logger.info(f"Generated {len(summaries)} synthetic summaries to {summaries_path}")
    logger.info(f"Ground truth written to {ground_truth_path}")

    return summaries_path, ground_truth_path

def verify_outcome_types(ground_truth_path: Path) -> Dict[str, int]:
    """Verify that both binary and continuous outcomes are present."""
    with open(ground_truth_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    counts = {"binary": 0, "continuous": 0}
    for record in data:
        outcome_type = record.get("outcome_type")
        if outcome_type in counts:
            counts[outcome_type] += 1

    logger.info(f"Outcome type verification: {counts}")
    if counts["binary"] == 0 or counts["continuous"] == 0:
        raise ValueError("Missing one of the required outcome types (binary or continuous)")

    return counts

def write_metadata(output_dir: Path, n_records: int, counts: Dict[str, int]) -> Path:
    """Write metadata about the generated dataset."""
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "total_records": n_records,
        "outcome_type_counts": counts,
        "source": "synthetic_generator",
        "version": "1.0",
    }
    metadata_path = output_dir / "synthetic_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    return metadata_path

def main() -> None:
    """Main entry point for synthetic dataset generation."""
    output_dir = Path("data/synthetic")
    n_records = 10000
    seed = SEED

    logger.info(f"Starting synthetic dataset generation with {n_records} records...")

    summaries_path, ground_truth_path = generate_synthetic_dataset(
        n_records=n_records, output_dir=str(output_dir), seed=seed
    )

    counts = verify_outcome_types(ground_truth_path)
    write_metadata(output_dir, n_records, counts)

    logger.info("Synthetic dataset generation completed successfully.")
    logger.info(f"Summaries: {summaries_path}")
    logger.info(f"Ground Truth: {ground_truth_path}")
    logger.info(f"Outcome distribution: {counts}")

    # Verify record count
    with open(summaries_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        row_count = sum(1 for _ in reader) - 1  # Exclude header

    if row_count < 10000:
        raise RuntimeError(f"Generated {row_count} records, expected at least 10000")

    logger.info(f"Verified {row_count} records in output file.")

if __name__ == "__main__":
    main()
