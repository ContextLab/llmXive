"""
Synthetic dataset generator for A/B test validity evaluation.

Generates a large-scale synthetic dataset of A/B test summaries with both
binary and continuous outcomes to validate the audit pipeline (FR-030).

The generator creates:
1. Realistic sample sizes (N)
2. Binary outcomes (conversion rates) with p-values
3. Continuous outcomes (means/stds) with p-values
4. Metadata including domain, year, and test type

Output:
- data/synthetic/synthetic_ab_summaries.csv (≥ 10,000 records)
- data/synthetic/synthetic_metadata.json
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

# Import from project config and logging utilities
from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

# Ensure the logger is initialized
logger = get_default_logger(__name__)
audit_logger = AuditLogger(logger)

def set_all_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    audit_logger.info(f"Seeds set to {seed}")

def generate_sample_sizes(n_total: int = 10000) -> List[Tuple[int, int]]:
    """
    Generate realistic sample sizes for A/B tests.
    Returns a list of (n_control, n_treatment) tuples.
    Sample sizes are drawn from a log-normal distribution to mimic real-world variance.
    """
    # Log-normal parameters based on typical web A/B test sizes (1k to 1M)
    mu, sigma = np.log(50000), 1.5
    n_control = np.random.lognormal(mu, sigma, n_total).astype(int)
    n_treatment = np.random.lognormal(mu, sigma, n_total).astype(int)

    # Ensure minimum sample size of 100 per group for statistical validity
    n_control = np.clip(n_control, 100, None)
    n_treatment = np.clip(n_treatment, 100, None)

    return list(zip(n_control, n_treatment))

def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: float = 0.10,
    effect_size: Optional[float] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a binary outcome A/B test summary.

    Args:
        n_control: Sample size of control group
        n_treatment: Sample size of treatment group
        baseline_rate: Expected conversion rate for control (default 10%)
        effect_size: Optional effect size (lift) to apply. If None, random small effect.
        seed: Optional seed for this specific generation

    Returns:
        Dictionary with n_control, n_treatment, successes_control, successes_treatment,
        baseline_rate, observed_lift, p_value, and outcome_type.
    """
    if seed is not None:
        np.random.seed(seed)

    # Determine effect size (random small lift between -5% and +15%)
    if effect_size is None:
        effect_size = np.random.uniform(-0.05, 0.15)

    # Calculate treatment rate
    treatment_rate = baseline_rate * (1 + effect_size)
    treatment_rate = np.clip(treatment_rate, 0.001, 0.999)

    # Generate successes (binomial draws)
    successes_control = np.random.binomial(n_control, baseline_rate)
    successes_treatment = np.random.binomial(n_treatment, treatment_rate)

    # Calculate observed rates
    rate_control = successes_control / n_control
    rate_treatment = successes_treatment / n_treatment
    observed_lift = (rate_treatment - rate_control) / rate_control if rate_control > 0 else 0

    # Perform two-proportion z-test
    try:
        p_value = stats.proportions_ztest(
            [successes_control, successes_treatment],
            [n_control, n_treatment]
        )[1]
    except Exception:
        # Fallback for edge cases
        p_value = 1.0

    return {
        "n_control": int(n_control),
        "n_treatment": int(n_treatment),
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "baseline_rate": float(baseline_rate),
        "observed_lift": float(observed_lift),
        "p_value": float(p_value),
        "outcome_type": "binary"
    }

def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    baseline_mean: float = 100.0,
    baseline_std: float = 20.0,
    effect_size: Optional[float] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a continuous outcome A/B test summary.

    Args:
        n_control: Sample size of control group
        n_treatment: Sample size of treatment group
        baseline_mean: Expected mean for control group
        baseline_std: Expected standard deviation
        effect_size: Optional effect size (Cohen's d) to apply.
        seed: Optional seed for this specific generation

    Returns:
        Dictionary with n_control, n_treatment, mean_control, mean_treatment,
        std_control, std_treatment, baseline_mean, observed_lift, p_value, and outcome_type.
    """
    if seed is not None:
        np.random.seed(seed)

    # Determine effect size (random small lift between -0.2 and 0.5 standard deviations)
    if effect_size is None:
        effect_size = np.random.uniform(-0.2, 0.5)

    # Calculate treatment mean
    treatment_mean = baseline_mean + (effect_size * baseline_std)

    # Generate samples
    sample_control = np.random.normal(baseline_mean, baseline_std, n_control)
    sample_treatment = np.random.normal(treatment_mean, baseline_std, n_treatment)

    # Calculate statistics
    mean_control = float(np.mean(sample_control))
    mean_treatment = float(np.mean(sample_treatment))
    std_control = float(np.std(sample_control, ddof=1))
    std_treatment = float(np.std(sample_treatment, ddof=1))

    observed_lift = (mean_treatment - mean_control) / mean_control if mean_control > 0 else 0

    # Perform Welch's t-test
    try:
        p_value = stats.ttest_ind(
            sample_control, sample_treatment, equal_var=False
        )[1]
    except Exception:
        # Fallback for edge cases
        p_value = 1.0

    return {
        "n_control": int(n_control),
        "n_treatment": int(n_treatment),
        "mean_control": mean_control,
        "mean_treatment": mean_treatment,
        "std_control": std_control,
        "std_treatment": std_treatment,
        "baseline_mean": float(baseline_mean),
        "observed_lift": float(observed_lift),
        "p_value": float(p_value),
        "outcome_type": "continuous"
    }

def generate_synthetic_dataset(
    n_records: int = 10000,
    output_dir: Path = None,
    seed: int = SEED
) -> Tuple[Path, Path]:
    """
    Generate the full synthetic dataset with both binary and continuous outcomes.

    Args:
        n_records: Total number of records to generate (must be ≥ 10,000)
        output_dir: Directory to write output files (default: data/synthetic)
        seed: Random seed for reproducibility

    Returns:
        Tuple of (csv_path, metadata_path)
    """
    if output_dir is None:
        output_dir = Path("data/synthetic")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "synthetic_ab_summaries.csv"
    metadata_path = output_dir / "synthetic_metadata.json"

    set_all_seeds(seed)
    audit_logger.info(f"Generating {n_records} synthetic A/B test records...")

    # Generate sample sizes
    sample_sizes = generate_sample_sizes(n_records)

    # Domain and year distributions for realism
    domains = ["ecommerce", "saaS", "fintech", "healthcare", "media"]
    domain_weights = [0.30, 0.25, 0.20, 0.15, 0.10]
    years = list(range(2018, 2025))
    year_weights = [0.05, 0.08, 0.12, 0.15, 0.20, 0.25, 0.15]

    records = []
    binary_count = 0
    continuous_count = 0

    for i, (n_control, n_treatment) in enumerate(sample_sizes):
        # Alternate or randomly assign outcome type to ensure both are present
        # Use a 50/50 split to ensure robustness
        is_binary = (i % 2 == 0) or (random.random() < 0.5)

        # Select domain and year
        domain = random.choices(domains, weights=domain_weights, k=1)[0]
        year = random.choices(years, weights=year_weights, k=1)[0]

        if is_binary:
            record = generate_binary_outcome(n_control, n_treatment)
            binary_count += 1
        else:
            record = generate_continuous_outcome(n_control, n_treatment)
            continuous_count += 1

        # Add metadata
        record["domain"] = domain
        record["year"] = year
        record["id"] = f"synthetic_{i:06d}"
        record["generated_at"] = datetime.utcnow().isoformat()

        records.append(record)

        if (i + 1) % 1000 == 0:
            audit_logger.info(f"Generated {i + 1}/{n_records} records...")

    # Write CSV
    fieldnames = list(records[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    audit_logger.info(f"Wrote {len(records)} records to {csv_path}")

    # Write metadata
    metadata = {
        "total_records": len(records),
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "domains": domains,
        "years": years,
        "seed": seed,
        "generated_at": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "description": "Synthetic A/B test dataset for pipeline validation (FR-030)"
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    audit_logger.info(f"Wrote metadata to {metadata_path}")

    return csv_path, metadata_path

def verify_outcome_types(csv_path: Path) -> Dict[str, Any]:
    """
    Verify that the generated dataset contains both binary and continuous outcomes.

    Args:
        csv_path: Path to the generated CSV file

    Returns:
        Dictionary with verification results
    """
    binary_count = 0
    continuous_count = 0
    total_count = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_count += 1
            if row["outcome_type"] == "binary":
                binary_count += 1
            elif row["outcome_type"] == "continuous":
                continuous_count += 1

    verification = {
        "total_records": total_count,
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "binary_percentage": (binary_count / total_count * 100) if total_count > 0 else 0,
        "continuous_percentage": (continuous_count / total_count * 100) if total_count > 0 else 0,
        "has_binary": binary_count > 0,
        "has_continuous": continuous_count > 0,
        "meets_minimum_threshold": total_count >= 10000,
        "valid": binary_count > 0 and continuous_count > 0 and total_count >= 10000
    }

    if verification["valid"]:
        audit_logger.info(
            f"Verification passed: {binary_count} binary, {continuous_count} continuous, "
            f"total {total_count} records."
        )
    else:
        audit_logger.error(f"Verification failed: {verification}")

    return verification

def write_summaries_to_csv(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write a list of records to a CSV file."""
    if not records:
        audit_logger.warning("No records to write.")
        return

    fieldnames = list(records[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    audit_logger.info(f"Wrote {len(records)} records to {output_path}")

def write_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """Write metadata to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)

    audit_logger.info(f"Wrote metadata to {output_path}")

def main() -> int:
    """
    Main entry point for synthetic dataset generation.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Configuration
        n_records = 10000  # Minimum required by FR-030
        output_dir = Path("data/synthetic")
        seed = SEED

        # Generate dataset
        csv_path, metadata_path = generate_synthetic_dataset(
            n_records=n_records,
            output_dir=output_dir,
            seed=seed
        )

        # Verify outcome types
        verification = verify_outcome_types(csv_path)

        if not verification["valid"]:
            audit_logger.error(
                "Synthetic dataset verification failed. "
                "Both binary and continuous outcomes must be present with ≥ 10,000 total records."
            )
            return 1

        # Update metadata with verification results
        metadata = {
            "total_records": verification["total_records"],
            "binary_count": verification["binary_count"],
            "continuous_count": verification["continuous_count"],
            "verification_passed": verification["valid"],
            "generated_at": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        write_metadata(metadata, metadata_path)

        audit_logger.info("Synthetic dataset generation completed successfully.")
        return 0

    except Exception as e:
        audit_logger.error(f"Synthetic dataset generation failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
