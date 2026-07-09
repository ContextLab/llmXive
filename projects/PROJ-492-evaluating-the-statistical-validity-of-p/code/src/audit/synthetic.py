"""
Synthetic dataset generator for A/B test audit validation.

Generates a large corpus of simulated A/B test summaries with known ground truth
statistical properties to validate the audit pipeline's consistency detection.

Produces:
  - data/synthetic/summaries.csv: The synthetic dataset (>= 10,000 records)
  - data/synthetic/metadata.json: Generation parameters and verification stats
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
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants
MIN_RECORDS = 10000
BINARY_RATIO = 0.6  # 60% binary, 40% continuous
DOMAIN_LIST = [
    "tech-blogs", "marketing", "e-commerce", "finance", "health", 
    "education", "gaming", "social-media", "saas", "retail"
]
YEAR_RANGE = (2018, 2024)

logger: AuditLogger = get_default_logger()


def set_all_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds set to {seed}")


def generate_sample_sizes(n_total: int) -> Tuple[int, int]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Sizes are drawn from a log-normal distribution to mimic real-world variance.
    """
    # Log-normal parameters tuned for realistic web A/B test sizes
    mu, sigma = 6.0, 1.5
    n_control = int(np.random.lognormal(mu, sigma))
    n_treatment = int(np.random.lognormal(mu, sigma))
    
    # Ensure minimum viable sizes
    n_control = max(n_control, 50)
    n_treatment = max(n_treatment, 50)
    
    return n_control, n_treatment


def generate_binary_outcome(
    n_control: int, 
    n_treatment: int, 
    baseline_rate: float, 
    effect_size: float, 
    inject_inconsistency: bool = False
) -> Dict[str, Any]:
    """
    Generate a binary outcome A/B test summary.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_rate: True conversion rate for control
        effect_size: True lift (e.g., 0.10 for 10% lift)
        inject_inconsistency: If True, report a p-value that doesn't match the data
        
    Returns:
        Dictionary with metrics and reported p-value
    """
    # True treatment rate
    treatment_rate = baseline_rate * (1 + effect_size)
    
    # Generate actual successes (binomial)
    successes_control = np.random.binomial(n_control, baseline_rate)
    successes_treatment = np.random.binomial(n_treatment, treatment_rate)
    
    # Calculate reconstructed p-value (ground truth)
    p_reconstructed, _ = stats.fisher_exact([
        [successes_control, n_control - successes_control],
        [successes_treatment, n_treatment - successes_treatment]
    ])
    
    # Decide reported p-value
    if inject_inconsistency:
        # Report a p-value that is significantly different from the truth
        # e.g., if p < 0.05, report > 0.10, and vice versa
        if p_reconstructed < 0.05:
            p_reported = round(np.random.uniform(0.10, 0.50), 4)
        else:
            p_reported = round(np.random.uniform(0.001, 0.04), 4)
    else:
        # Report the true p-value with minor noise (simulating rounding)
        p_reported = round(p_reconstructed + np.random.normal(0, 0.001), 4)
        p_reported = max(0.0, min(1.0, p_reported))
    
    return {
        "outcome_type": "binary",
        "n_control": int(n_control),
        "n_treatment": int(n_treatment),
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "baseline_rate": round(baseline_rate, 4),
        "treatment_rate": round(treatment_rate, 4),
        "effect_size": round(effect_size, 4),
        "p_reconstructed": round(p_reconstructed, 4),
        "p_reported": p_reported,
        "is_inconsistent": inject_inconsistency
    }


def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    mean_control: float,
    effect_size: float,
    std_dev: float,
    inject_inconsistency: bool = False
) -> Dict[str, Any]:
    """
    Generate a continuous outcome A/B test summary.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        mean_control: True mean for control group
        effect_size: True difference in means
        std_dev: Standard deviation for both groups
        inject_inconsistency: If True, report a p-value that doesn't match the data
        
    Returns:
        Dictionary with metrics and reported p-value
    """
    mean_treatment = mean_control + effect_size
    
    # Generate samples
    sample_control = np.random.normal(mean_control, std_dev, n_control)
    sample_treatment = np.random.normal(mean_treatment, std_dev, n_treatment)
    
    # Calculate statistics
    mean_control_obs = np.mean(sample_control)
    mean_treatment_obs = np.mean(sample_treatment)
    std_control_obs = np.std(sample_control, ddof=1)
    std_treatment_obs = np.std(sample_treatment, ddof=1)
    
    # Welch's t-test
    t_stat, p_reconstructed = stats.ttest_ind(
        sample_treatment, sample_control, equal_var=False
    )
    p_reconstructed = float(p_reconstructed)
    
    # Decide reported p-value
    if inject_inconsistency:
        if p_reconstructed < 0.05:
            p_reported = round(np.random.uniform(0.10, 0.50), 4)
        else:
            p_reported = round(np.random.uniform(0.001, 0.04), 4)
    else:
        p_reported = round(p_reconstructed + np.random.normal(0, 0.001), 4)
        p_reported = max(0.0, min(1.0, p_reported))
    
    return {
        "outcome_type": "continuous",
        "n_control": int(n_control),
        "n_treatment": int(n_treatment),
        "mean_control": round(mean_control_obs, 4),
        "mean_treatment": round(mean_treatment_obs, 4),
        "std_control": round(std_control_obs, 4),
        "std_treatment": round(std_treatment_obs, 4),
        "effect_size": round(effect_size, 4),
        "p_reconstructed": round(p_reconstructed, 4),
        "p_reported": p_reported,
        "is_inconsistent": inject_inconsistency
    }


def generate_synthetic_dataset(
    n_records: int = MIN_RECORDS,
    inconsistency_rate: float = 0.15
) -> List[Dict[str, Any]]:
    """
    Generate the full synthetic dataset.
    
    Args:
        n_records: Total number of summaries to generate (min 10,000)
        inconsistency_rate: Fraction of records with statistical inconsistencies
        
    Returns:
        List of summary dictionaries
    """
    set_all_seeds()
    summaries = []
    
    n_binary = int(n_records * BINARY_RATIO)
    n_continuous = n_records - n_binary
    n_inconsistent = int(n_records * inconsistency_rate)
    n_consistent = n_records - n_inconsistent
    
    logger.info(f"Generating {n_records} records: {n_binary} binary, {n_continuous} continuous")
    logger.info(f"Inconsistency rate: {inconsistency_rate*100:.1f}%")
    
    # Generate binary records
    for i in range(n_binary):
        n_c, n_t = generate_sample_sizes(0)
        baseline = np.random.uniform(0.05, 0.30)
        effect = np.random.choice([-0.1, -0.05, 0.0, 0.05, 0.1])
        inject = (i < n_inconsistent) if i < n_consistent + n_inconsistent else False
        
        # Distribute inconsistencies roughly evenly
        inject_inconsistency = (i < n_inconsistent)
        
        summary = generate_binary_outcome(n_c, n_t, baseline, effect, inject_inconsistency)
        summary["domain"] = np.random.choice(DOMAIN_LIST)
        summary["year"] = np.random.randint(YEAR_RANGE[0], YEAR_RANGE[1] + 1)
        summary["id"] = f"B{i:05d}"
        summaries.append(summary)
        
    # Generate continuous records
    for i in range(n_continuous):
        n_c, n_t = generate_sample_sizes(0)
        mean = np.random.uniform(100.0, 1000.0)
        effect = np.random.choice([-50, -25, 0, 25, 50])
        std = np.random.uniform(50, 200)
        
        inject_inconsistency = (i < n_inconsistent)
        
        summary = generate_continuous_outcome(n_c, n_t, mean, effect, std, inject_inconsistency)
        summary["domain"] = np.random.choice(DOMAIN_LIST)
        summary["year"] = np.random.randint(YEAR_RANGE[0], YEAR_RANGE[1] + 1)
        summary["id"] = f"C{i:05d}"
        summaries.append(summary)
        
    # Shuffle to mix binary/continuous
    random.shuffle(summaries)
    
    return summaries


def verify_outcome_types(summaries: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Verify that both outcome types are present and count them.
    
    Returns:
        Tuple of (binary_count, continuous_count)
    """
    binary_count = sum(1 for s in summaries if s["outcome_type"] == "binary")
    continuous_count = sum(1 for s in summaries if s["outcome_type"] == "continuous")
    
    logger.info(f"Verification: {binary_count} binary, {continuous_count} continuous")
    
    if binary_count == 0:
        raise ValueError("Generated dataset contains no binary outcomes!")
    if continuous_count == 0:
        raise ValueError("Generated dataset contains no continuous outcomes!")
        
    return binary_count, continuous_count


def write_summaries_to_csv(summaries: List[Dict[str, Any]], output_path: Path) -> None:
    """Write summaries to CSV file."""
    if not summaries:
        raise ValueError("No summaries to write!")
        
    fieldnames = list(summaries[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
        
    logger.info(f"Wrote {len(summaries)} records to {output_path}")


def write_metadata(
    n_records: int,
    binary_count: int,
    continuous_count: int,
    inconsistency_rate: float,
    output_path: Path
) -> None:
    """Write generation metadata to JSON."""
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "total_records": n_records,
        "binary_outcomes": binary_count,
        "continuous_outcomes": continuous_count,
        "inconsistency_rate": inconsistency_rate,
        "seed": SEED,
        "domains": DOMAIN_LIST,
        "year_range": YEAR_RANGE
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Wrote metadata to {output_path}")


def main() -> None:
    """Main entry point for synthetic data generation."""
    logger.info("Starting synthetic dataset generation (T026)")
    
    # Ensure output directory exists
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / "summaries.csv"
    meta_path = output_dir / "metadata.json"
    
    # Generate dataset
    summaries = generate_synthetic_dataset(n_records=MIN_RECORDS, inconsistency_rate=0.15)
    
    # Verify outcome types
    binary_count, continuous_count = verify_outcome_types(summaries)
    
    if binary_count < 1 or continuous_count < 1:
        logger.error("FAILED: Both outcome types must be present")
        raise RuntimeError("Verification failed: missing outcome types")
        
    # Write outputs
    write_summaries_to_csv(summaries, csv_path)
    write_metadata(len(summaries), binary_count, continuous_count, 0.15, meta_path)
    
    logger.info("Synthetic dataset generation completed successfully")
    logger.info(f"Output files: {csv_path}, {meta_path}")


if __name__ == "__main__":
    main()
