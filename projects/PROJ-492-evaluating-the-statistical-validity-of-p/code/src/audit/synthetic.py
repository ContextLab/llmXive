"""
Synthetic dataset generator for A/B test summaries (FR-030).

Generates at least 10,000 simulated summaries with both binary and continuous
outcomes, ensuring statistical validity and reproducibility.
"""

import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants
MIN_RECORDS = 10000
BINARY_OUTCOME_RATIO = 0.5  # 50% binary, 50% continuous
BASELINE_RATES = [0.05, 0.10, 0.15, 0.20, 0.30, 0.50]
EFFECT_SIZES = [0.01, 0.02, 0.05, 0.10, 0.15]  # Absolute difference
SAMPLE_SIZE_RANGE = (100, 50000)
DOMAINS = ["tech", "health", "finance", "e-commerce", "education"]
YEARS = list(range(2018, 2025))

logger = get_default_logger(__name__)


def set_all_seeds(seed: int = SEED) -> None:
    """Set all random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"All RNG seeds set to {seed}")


def generate_sample_sizes(n_records: int) -> List[Tuple[int, int]]:
    """Generate sample sizes for control and treatment groups."""
    sample_sizes = []
    for _ in range(n_records):
        n_control = np.random.randint(SAMPLE_SIZE_RANGE[0], SAMPLE_SIZE_RANGE[1])
        # Treatment size can be similar or slightly different
        n_treatment = np.random.randint(
            int(n_control * 0.8), int(n_control * 1.2)
        )
        sample_sizes.append((n_control, n_treatment))
    return sample_sizes


def generate_binary_outcome(
    n_control: int, n_treatment: int, baseline_rate: float, effect_size: float
) -> Dict[str, Any]:
    """
    Generate synthetic binary outcome data.

    Returns a dictionary with counts and calculated metrics.
    """
    # True effect: baseline + effect_size (can be negative for control)
    p_treatment = baseline_rate + effect_size
    p_treatment = np.clip(p_treatment, 0.001, 0.999)  # Ensure valid probability

    # Generate successes
    successes_control = np.random.binomial(n_control, baseline_rate)
    successes_treatment = np.random.binomial(n_treatment, p_treatment)

    # Calculate proportions
    prop_control = successes_control / n_control
    prop_treatment = successes_treatment / n_treatment

    # Two-proportion z-test
    pooled_p = (successes_control + successes_treatment) / (n_control + n_treatment)
    se = np.sqrt(
        pooled_p * (1 - pooled_p) * (1 / n_control + 1 / n_treatment)
    )
    if se > 0:
        z_stat = (prop_treatment - prop_control) / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    else:
        z_stat = 0.0
        p_value = 1.0

    # Effect size (absolute difference)
    effect = prop_treatment - prop_control

    return {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "prop_control": float(prop_control),
        "prop_treatment": float(prop_treatment),
        "effect_size": float(effect),
        "p_value": float(p_value),
        "z_statistic": float(z_stat),
        "baseline_rate": float(baseline_rate),
    }


def generate_continuous_outcome(
    n_control: int, n_treatment: int, baseline_mean: float, effect_size: float
) -> Dict[str, Any]:
    """
    Generate synthetic continuous outcome data.

    Returns a dictionary with means, standard deviations, and calculated metrics.
    """
    # Generate data
    data_control = np.random.normal(baseline_mean, 1.0, n_control)
    data_treatment = np.random.normal(
        baseline_mean + effect_size, 1.0, n_treatment
    )

    # Calculate statistics
    mean_control = float(np.mean(data_control))
    mean_treatment = float(np.mean(data_treatment))
    std_control = float(np.std(data_control, ddof=1))
    std_treatment = float(np.std(data_treatment, ddof=1))

    # Welch's t-test
    t_stat, p_value = stats.ttest_ind(
        data_treatment, data_control, equal_var=False
    )

    # Effect size (Cohen's d)
    pooled_std = np.sqrt((std_control**2 + std_treatment**2) / 2)
    if pooled_std > 0:
        cohens_d = (mean_treatment - mean_control) / pooled_std
    else:
        cohens_d = 0.0

    return {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": mean_control,
        "mean_treatment": mean_treatment,
        "std_control": std_control,
        "std_treatment": std_treatment,
        "effect_size": float(mean_treatment - mean_control),
        "p_value": float(p_value),
        "t_statistic": float(t_stat),
        "cohens_d": float(cohens_d),
        "baseline_mean": float(baseline_mean),
    }


def generate_synthetic_dataset(
    n_records: int = MIN_RECORDS, output_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.

    Args:
        n_records: Number of records to generate (minimum 10,000)
        output_dir: Directory to write output files

    Returns:
        List of generated summary dictionaries
    """
    n_records = max(n_records, MIN_RECORDS)
    logger.info(f"Generating {n_records} synthetic summaries...")

    # Set seeds for reproducibility
    set_all_seeds()

    summaries = []
    binary_count = 0
    continuous_count = 0

    # Pre-generate sample sizes
    sample_sizes = generate_sample_sizes(n_records)

    for i in range(n_records):
        n_control, n_treatment = sample_sizes[i]

        # Randomly choose outcome type
        if random.random() < BINARY_OUTCOME_RATIO:
            # Binary outcome
            baseline_rate = random.choice(BASELINE_RATES)
            effect_size = random.choice(EFFECT_SIZES) * random.choice([-1, 1])
            summary = generate_binary_outcome(
                n_control, n_treatment, baseline_rate, effect_size
            )
            binary_count += 1
        else:
            # Continuous outcome
            baseline_mean = random.uniform(10, 100)
            effect_size = random.choice(EFFECT_SIZES) * random.uniform(0.5, 2.0)
            effect_size *= random.choice([-1, 1])
            summary = generate_continuous_outcome(
                n_control, n_treatment, baseline_mean, effect_size
            )
            continuous_count += 1

        # Add metadata
        summary["id"] = f"synthetic_{i:06d}"
        summary["domain"] = random.choice(DOMAINS)
        summary["year"] = random.choice(YEARS)
        summary["generated_at"] = datetime.utcnow().isoformat()

        summaries.append(summary)

        if (i + 1) % 1000 == 0:
            logger.info(f"Generated {i + 1}/{n_records} summaries...")

    logger.info(
        f"Generation complete: {binary_count} binary, {continuous_count} continuous"
    )

    # Write output files if output_dir is provided
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write CSV
        csv_path = output_dir / "synthetic_summaries.csv"
        fieldnames = list(summaries[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summaries)
        logger.info(f"Wrote {csv_path}")

        # Write JSON
        json_path = output_dir / "synthetic_summaries.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summaries, f, indent=2)
        logger.info(f"Wrote {json_path}")

        # Write metadata
        metadata = {
            "total_records": len(summaries),
            "binary_count": binary_count,
            "continuous_count": continuous_count,
            "binary_ratio": binary_count / len(summaries),
            "continuous_ratio": continuous_count / len(summaries),
            "generated_at": datetime.utcnow().isoformat(),
            "seed": SEED,
        }
        metadata_path = output_dir / "synthetic_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Wrote {metadata_path}")

    return summaries


def verify_outcome_types(summaries: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, int]]:
    """
    Verify that both binary and continuous outcomes are present.

    Args:
        summaries: List of generated summaries

    Returns:
        Tuple of (is_valid, counts_dict)
    """
    counts = {"binary": 0, "continuous": 0}
    for summary in summaries:
        outcome_type = summary.get("outcome_type")
        if outcome_type in counts:
            counts[outcome_type] += 1

    is_valid = counts["binary"] > 0 and counts["continuous"] > 0

    logger.info(
        f"Verification: {counts['binary']} binary, {counts['continuous']} continuous"
    )

    if not is_valid:
        logger.error("Verification failed: Missing outcome type(s)")
    else:
        logger.info("Verification passed: Both outcome types present")

    return is_valid, counts


def write_metadata(output_path: Path, metadata: Dict[str, Any]) -> None:
    """Write metadata to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Wrote metadata to {output_path}")


def main() -> int:
    """
    Main entry point for synthetic dataset generation.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Starting synthetic dataset generation (T026)...")

    try:
        # Define output directory
        output_dir = Path("code/data/synthetic")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate dataset
        summaries = generate_synthetic_dataset(n_records=MIN_RECORDS, output_dir=output_dir)

        # Verify outcome types
        is_valid, counts = verify_outcome_types(summaries)

        if not is_valid:
            logger.error("Verification failed: Not both outcome types present")
            return 1

        # Verify record count
        if len(summaries) < MIN_RECORDS:
            logger.error(
                f"Verification failed: Only {len(summaries)} records, need {MIN_RECORDS}"
            )
            return 1

        logger.info(
            f"SUCCESS: Generated {len(summaries)} records "
            f"({counts['binary']} binary, {counts['continuous']} continuous)"
        )

        return 0

    except Exception as e:
        logger.error(f"Error during synthetic dataset generation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
