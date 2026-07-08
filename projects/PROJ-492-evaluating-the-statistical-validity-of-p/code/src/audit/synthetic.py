"""
Synthetic Dataset Generator for A/B Test Validity Evaluation.

Generates a large corpus of simulated A/B test summaries with known ground truth
to evaluate the statistical reconstruction and inconsistency detection pipeline.

Per FR-030: Generates at least 10,000 simulated summaries covering both binary
and continuous outcomes with realistic parameter distributions.
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants for synthetic data generation
DEFAULT_COUNT = 10000
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
MIN_SAMPLE_SIZE = 100
MAX_SAMPLE_SIZE = 50000
MIN_BASELINE_RATE = 0.01
MAX_BASELINE_RATE = 0.99
MIN_EFFECT_SIZE = 0.001
MAX_EFFECT_SIZE = 0.5
CONTINUOUS_MEAN = 10.0
CONTINUOUS_STD = 5.0
DOMAIN_LIST = [
    "tech", "marketing", "finance", "healthcare", "education",
    "e-commerce", "gaming", "social-media", "retail", "logistics"
]
YEAR_START = 2018
YEAR_END = 2024

logger = get_default_logger(__name__)

def set_all_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed}")

def generate_sample_sizes(n: int) -> np.ndarray:
    """
    Generate sample sizes following a log-normal distribution to mimic
    real-world A/B test sizes (many small tests, few very large ones).
    """
    # Log-normal parameters chosen to produce realistic range
    mu = np.log(2000)
    sigma = 1.5
    sizes = np.random.lognormal(mu, sigma, n)
    sizes = np.clip(sizes, MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
    return sizes.astype(int)

def generate_binary_outcome(
    n: int,
    baseline_rate: float,
    effect_size: float,
    test_variant_rate: Optional[float] = None
) -> Tuple[int, int, int, int]:
    """
    Generate binary outcome counts for control and treatment groups.

    Returns:
        Tuple of (control_successes, control_total, treatment_successes, treatment_total)
    """
    control_total = n // 2
    treatment_total = n - control_total

    if test_variant_rate is None:
        # Apply effect size to baseline
        treatment_rate = baseline_rate + effect_size
        # Clamp to valid probability range
        treatment_rate = np.clip(treatment_rate, 0.0, 1.0)
    else:
        treatment_rate = test_variant_rate

    control_successes = np.random.binomial(control_total, baseline_rate)
    treatment_successes = np.random.binomial(treatment_total, treatment_rate)

    return control_successes, control_total, treatment_successes, treatment_total

def generate_continuous_outcome(
    n: int,
    baseline_mean: float,
    effect_size: float,
    std: float = CONTINUOUS_STD
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate continuous outcome values for control and treatment groups.

    Returns:
        Tuple of (control_values, treatment_values)
    """
    control_total = n // 2
    treatment_total = n - control_total

    treatment_mean = baseline_mean + effect_size

    control_values = np.random.normal(baseline_mean, std, control_total)
    treatment_values = np.random.normal(treatment_mean, std, treatment_total)

    return control_values, treatment_values

def compute_p_value_binary(
    control_successes: int,
    control_total: int,
    treatment_successes: int,
    treatment_total: int
) -> float:
    """Compute two-proportion z-test p-value."""
    if control_total == 0 or treatment_total == 0:
        return 1.0

    p_control = control_successes / control_total
    p_treatment = treatment_successes / treatment_total

    p_pooled = (control_successes + treatment_successes) / (control_total + treatment_total)
    if p_pooled == 0 or p_pooled == 1:
        return 1.0

    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/control_total + 1/treatment_total))
    if se == 0:
        return 1.0

    z_stat = (p_treatment - p_control) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    return float(np.clip(p_value, 1e-10, 1.0))

def compute_p_value_continuous(
    control_values: np.ndarray,
    treatment_values: np.ndarray
) -> float:
    """Compute Welch's t-test p-value."""
    if len(control_values) < 2 or len(treatment_values) < 2:
        return 1.0

    _, p_value = stats.ttest_ind(control_values, treatment_values, equal_var=False)
    return float(np.clip(p_value, 1e-10, 1.0))

def generate_synthetic_dataset(
    count: int = DEFAULT_COUNT,
    seed: int = SEED,
    noise_level: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.

    Args:
        count: Number of summaries to generate (minimum 10,000 per FR-030).
        seed: Random seed for reproducibility.
        noise_level: Fraction of records to introduce inconsistency (0.0 to 1.0).

    Returns:
        List of dictionaries representing ABTestSummary records.
    """
    if count < 10000:
        logger.warning(f"Requested count {count} is below FR-030 minimum of 10,000. Adjusting.")
        count = 10000

    set_all_seeds(seed)
    summaries = []

    # Determine outcome types
    is_binary = np.random.random(count) < BINARY_RATIO

    # Generate sample sizes
    sample_sizes = generate_sample_sizes(count)

    for i in range(count):
        outcome_type = "binary" if is_binary[i] else "continuous"
        n = sample_sizes[i]

        # Generate base parameters
        if outcome_type == "binary":
            baseline = np.random.uniform(MIN_BASELINE_RATE, MAX_BASELINE_RATE)
            effect = np.random.uniform(MIN_EFFECT_SIZE, MAX_EFFECT_SIZE)
            if np.random.random() < 0.3:  # 30% negative effects
                effect = -effect

            c_succ, c_tot, t_succ, t_tot = generate_binary_outcome(n, baseline, effect)
            reported_p = compute_p_value_binary(c_succ, c_tot, t_succ, t_tot)
            effect_size = abs(t_succ/t_tot - c_succ/c_tot) if c_tot > 0 and t_tot > 0 else 0.0

            summary = {
                "url": f"https://example.com/test/{i:06d}",
                "domain": random.choice(DOMAIN_LIST),
                "year": random.randint(YEAR_START, YEAR_END),
                "outcome_type": outcome_type,
                "baseline_conversion_rate": baseline,
                "treatment_conversion_rate": t_succ / t_tot if t_tot > 0 else 0.0,
                "control_sample_size": c_tot,
                "treatment_sample_size": t_tot,
                "reported_p_value": reported_p,
                "effect_size": effect_size,
                "is_significant": reported_p < 0.05,
                "ground_truth_p_value": reported_p,
                "ground_truth_effect_size": effect_size,
                "ground_truth_is_inconsistent": False
            }
        else:
            baseline = np.random.uniform(CONTINUOUS_MEAN - 2, CONTINUOUS_MEAN + 2)
            effect = np.random.uniform(-MAX_EFFECT_SIZE, MAX_EFFECT_SIZE) * CONTINUOUS_STD

            c_vals, t_vals = generate_continuous_outcome(n, baseline, effect)
            reported_p = compute_p_value_continuous(c_vals, t_vals)

            c_mean = np.mean(c_vals)
            t_mean = np.mean(t_vals)
            c_std = np.std(c_vals)
            t_std = np.std(t_vals)
            pooled_std = np.sqrt((c_std**2 + t_std**2) / 2)
            effect_size = abs(t_mean - c_mean) / pooled_std if pooled_std > 0 else 0.0

            summary = {
                "url": f"https://example.com/test/{i:06d}",
                "domain": random.choice(DOMAIN_LIST),
                "year": random.randint(YEAR_START, YEAR_END),
                "outcome_type": outcome_type,
                "baseline_mean": baseline,
                "treatment_mean": t_mean,
                "control_sample_size": len(c_vals),
                "treatment_sample_size": len(t_vals),
                "control_std": c_std,
                "treatment_std": t_std,
                "reported_p_value": reported_p,
                "effect_size": effect_size,
                "is_significant": reported_p < 0.05,
                "ground_truth_p_value": reported_p,
                "ground_truth_effect_size": effect_size,
                "ground_truth_is_inconsistent": False
            }

        # Introduce inconsistency for evaluation (controlled noise)
        if noise_level > 0 and random.random() < noise_level:
            # Corrupt the reported p-value
            if random.random() < 0.5:
                summary["reported_p_value"] = summary["ground_truth_p_value"] + random.uniform(0.01, 0.15)
            else:
                summary["reported_p_value"] = summary["ground_truth_p_value"] * random.uniform(0.1, 0.9)
            summary["reported_p_value"] = np.clip(summary["reported_p_value"], 0.0, 1.0)
            summary["ground_truth_is_inconsistent"] = True

        summaries.append(summary)

    return summaries

def verify_outcome_types(summaries: List[Dict[str, Any]]) -> Dict[str, int]:
    """Verify that both outcome types are present in the generated dataset."""
    counts = {"binary": 0, "continuous": 0}
    for s in summaries:
        if s["outcome_type"] in counts:
            counts[s["outcome_type"]] += 1
    return counts

def write_summaries(summaries: List[Dict[str, Any]], output_path: Path) -> None:
    """Write summaries to a CSV file."""
    if not summaries:
        raise ValueError("No summaries to write")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(summaries[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)

    logger.info(f"Wrote {len(summaries)} summaries to {output_path}")

def write_metadata(summaries: List[Dict[str, Any]], output_path: Path) -> None:
    """Write metadata about the generated dataset."""
    outcome_counts = verify_outcome_types(summaries)
    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_count": len(summaries),
        "outcome_type_counts": outcome_counts,
        "seed": SEED,
        "source": "synthetic_generator"
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Wrote metadata to {output_path}")

def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation (T026)")

    # Output paths
    output_dir = Path("data/synthetic")
    summaries_path = output_dir / "synthetic_summaries.csv"
    metadata_path = output_dir / "synthetic_metadata.json"

    # Generate dataset
    summaries = generate_synthetic_dataset(count=DEFAULT_COUNT, seed=SEED)

    # Verify outcome types
    counts = verify_outcome_types(summaries)
    logger.info(f"Outcome type distribution: {counts}")

    if counts["binary"] == 0 or counts["continuous"] == 0:
        logger.error("Failed to generate both outcome types")
        raise RuntimeError("Synthetic dataset must contain both binary and continuous outcomes")

    # Write outputs
    write_summaries(summaries, summaries_path)
    write_metadata(summaries, metadata_path)

    logger.info(f"Synthetic dataset generation complete. Total records: {len(summaries)}")
    logger.info(f"Binary outcomes: {counts['binary']}, Continuous outcomes: {counts['continuous']}")

if __name__ == "__main__":
    main()
