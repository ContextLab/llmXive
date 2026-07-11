"""
Synthetic dataset generator for A/B test audit validation (FR-030).

Generates a large-scale synthetic dataset of A/B test summaries containing
both binary and continuous outcomes. The data is constructed to be statistically
valid, with ground-truth p-values and effect sizes that can be used to
validate the consistency of the audit pipeline.

The generator ensures:
1. Realistic sample sizes drawn from empirical distributions.
2. Correct statistical relationships between sample size, effect size, and p-values.
3. A mix of binary (proportion) and continuous (mean difference) outcomes.
4. Deterministic generation via seeded RNGs for reproducibility.
"""
import csv
import json
import logging
import math
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
from scipy import stats

from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants
MIN_SAMPLE_SIZE = 100
MAX_SAMPLE_SIZE = 50000
BINARY_RATIO = 0.6  # 60% binary, 40% continuous
TOTAL_RECORDS = 10500  # Slightly more than 10,000 to ensure threshold
OUTPUT_DIR = Path("data/synthetic")
OUTPUT_CSV = OUTPUT_DIR / "synthetic_summaries.csv"
OUTPUT_METADATA = OUTPUT_DIR / "synthetic_metadata.json"

logger = get_default_logger(__name__)


def set_all_seeds(seed: int = SEED) -> None:
    """Set all random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"All RNG seeds set to {seed}")


def generate_sample_sizes(n: int) -> np.ndarray:
    """
    Generate realistic sample sizes for A/B tests.
    
    Uses a log-normal distribution to mimic real-world sample sizes,
    which often span several orders of magnitude.
    """
    # Log-normal parameters fitted to typical A/B test sizes
    mu = math.log(5000)
    sigma = 1.2
    sizes = np.random.lognormal(mu, sigma, n)
    # Clamp to realistic bounds
    sizes = np.clip(sizes, MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
    return sizes.astype(int)


def generate_binary_outcome(
    n_control: int, n_treatment: int, baseline_rate: float, lift: float
) -> Tuple[int, int, int, float, float]:
    """
    Generate binary outcome data and compute statistics.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_rate: Conversion rate for control group (0 < rate < 1)
        lift: Relative lift (e.g., 0.10 for 10% increase)
    
    Returns:
        Tuple of (successes_control, successes_treatment, n_control, n_treatment, p_value)
    """
    p_control = baseline_rate
    p_treatment = baseline_rate * (1 + lift)
    
    # Ensure probabilities are valid
    p_control = max(0.001, min(0.999, p_control))
    p_treatment = max(0.001, min(0.999, p_treatment))
    
    # Simulate successes (binomial)
    successes_control = np.random.binomial(n_control, p_control)
    successes_treatment = np.random.binomial(n_treatment, p_treatment)
    
    # Compute p-value using two-proportion z-test
    p_pool = (successes_control + successes_treatment) / (n_control + n_treatment)
    se = math.sqrt(p_pool * (1 - p_pool) * (1/n_control + 1/n_treatment))
    
    if se == 0:
        p_value = 1.0
    else:
        z_stat = (p_treatment - p_control) / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    return successes_control, successes_treatment, n_control, n_treatment, p_value


def generate_continuous_outcome(
    n_control: int, n_treatment: int, baseline_mean: float, lift: float, std_dev: float
) -> Tuple[float, float, float, float, float]:
    """
    Generate continuous outcome data and compute statistics.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_mean: Mean for control group
        lift: Relative lift (e.g., 0.05 for 5% increase)
        std_dev: Standard deviation of the outcome
    
    Returns:
        Tuple of (mean_control, mean_treatment, std_control, std_treatment, p_value)
    """
    mean_control = baseline_mean
    mean_treatment = baseline_mean * (1 + lift)
    
    # Simulate data
    data_control = np.random.normal(mean_control, std_dev, n_control)
    data_treatment = np.random.normal(mean_treatment, std_dev, n_treatment)
    
    # Compute Welch's t-test
    t_stat, p_value = stats.ttest_ind(data_control, data_treatment, equal_var=False)
    
    std_control = np.std(data_control, ddof=1)
    std_treatment = np.std(data_treatment, ddof=1)
    
    return float(np.mean(data_control)), float(np.mean(data_treatment)), \
           float(std_control), float(std_treatment), float(p_value)


def generate_synthetic_dataset(
    n_records: int = TOTAL_RECORDS,
    seed: int = SEED
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.
    
    Creates a mix of binary and continuous outcomes with statistically
    consistent metrics.
    """
    set_all_seeds(seed)
    records = []
    
    # Generate sample sizes for all records
    sample_sizes = generate_sample_sizes(n_records * 2)  # Need pairs for control/treatment
    
    # Generate baseline rates and lifts for binary outcomes
    binary_indices = np.random.choice(n_records, size=int(n_records * BINARY_RATIO), replace=False)
    continuous_indices = [i for i in range(n_records) if i not in binary_indices]
    
    for idx, i in enumerate(binary_indices):
        n_control = sample_sizes[2 * idx]
        n_treatment = sample_sizes[2 * idx + 1]
        
        # Realistic baseline rates (0.5% to 15%)
        baseline_rate = np.random.uniform(0.005, 0.15)
        # Lifts ranging from -10% to +30% (mostly positive)
        lift = np.random.normal(0.05, 0.10)
        
        successes_c, successes_t, n_c, n_t, p_val = generate_binary_outcome(
            n_control, n_treatment, baseline_rate, lift
        )
        
        record = {
            "id": f"synthetic_{idx:06d}",
            "outcome_type": "binary",
            "n_control": n_c,
            "n_treatment": n_t,
            "successes_control": successes_c,
            "successes_treatment": successes_t,
            "baseline_rate": round(baseline_rate, 6),
            "lift": round(lift, 6),
            "p_value": round(p_val, 8),
            "effect_size": round(lift, 6),
            "statistical_test": "two_proportion_z_test",
            "domain": np.random.choice(["ecommerce", "saas", "content", "mobile", "finance"]),
            "year": np.random.choice([2022, 2023, 2024, 2025]),
            "is_significant": p_val < 0.05
        }
        records.append(record)
    
    for idx, i in enumerate(continuous_indices):
        # Adjust index for continuous generation
        c_idx = continuous_indices.index(i)
        n_control = sample_sizes[len(binary_indices) * 2 + 2 * c_idx]
        n_treatment = sample_sizes[len(binary_indices) * 2 + 2 * c_idx + 1]
        
        # Realistic baseline means (e.g., session duration in seconds)
        baseline_mean = np.random.uniform(100, 500)
        lift = np.random.normal(0.03, 0.08)
        std_dev = baseline_mean * 0.5  # Coefficient of variation ~50%
        
        mean_c, mean_t, std_c, std_t, p_val = generate_continuous_outcome(
            n_control, n_treatment, baseline_mean, lift, std_dev
        )
        
        record = {
            "id": f"synthetic_{idx + len(binary_indices):06d}",
            "outcome_type": "continuous",
            "n_control": n_control,
            "n_treatment": n_treatment,
            "mean_control": round(mean_c, 4),
            "mean_treatment": round(mean_t, 4),
            "std_control": round(std_c, 4),
            "std_treatment": round(std_t, 4),
            "baseline_mean": round(baseline_mean, 4),
            "lift": round(lift, 6),
            "p_value": round(p_val, 8),
            "effect_size": round(lift, 6),
            "statistical_test": "welch_t_test",
            "domain": np.random.choice(["ecommerce", "saas", "content", "mobile", "finance"]),
            "year": np.random.choice([2022, 2023, 2024, 2025]),
            "is_significant": p_val < 0.05
        }
        records.append(record)
    
    return records


def verify_outcome_types(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """Verify the distribution of outcome types in the generated dataset."""
    counts = {"binary": 0, "continuous": 0}
    for r in records:
        if r["outcome_type"] in counts:
            counts[r["outcome_type"]] += 1
        else:
            logger.warning(f"Unknown outcome type: {r['outcome_type']}")
    return counts


def write_summaries_to_csv(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write the synthetic summaries to a CSV file."""
    if not records:
        raise ValueError("No records to write")
    
    # Define all possible fields to ensure consistent columns
    fieldnames = [
        "id", "outcome_type", "n_control", "n_treatment",
        "successes_control", "successes_treatment", "baseline_rate", "lift",
        "mean_control", "mean_treatment", "std_control", "std_treatment",
        "p_value", "effect_size", "statistical_test", "domain", "year", "is_significant"
    ]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)
    
    logger.info(f"Wrote {len(records)} records to {output_path}")


def write_metadata(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write metadata about the generated dataset."""
    outcome_counts = verify_outcome_types(records)
    total_records = len(records)
    significant_count = sum(1 for r in records if r["is_significant"])
    
    metadata = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_records": total_records,
        "outcome_type_distribution": outcome_counts,
        "significant_count": significant_count,
        "significant_rate": round(significant_count / total_records, 4),
        "domains": list(set(r["domain"] for r in records)),
        "years": list(set(r["year"] for r in records)),
        "seed": SEED,
        "constraints": {
            "min_sample_size": MIN_SAMPLE_SIZE,
            "max_sample_size": MAX_SAMPLE_SIZE,
            "binary_ratio": BINARY_RATIO
        }
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Wrote metadata to {output_path}")


def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation for T026")
    
    try:
        records = generate_synthetic_dataset(n_records=TOTAL_RECORDS, seed=SEED)
        
        if len(records) < 10000:
            logger.error(f"Generated only {len(records)} records, expected >= 10000")
            raise ValueError("Insufficient records generated")
        
        write_summaries_to_csv(records, OUTPUT_CSV)
        write_metadata(records, OUTPUT_METADATA)
        
        logger.info(f"Successfully generated {len(records)} synthetic records")
        logger.info(f"Output files: {OUTPUT_CSV}, {OUTPUT_METADATA}")
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}")
        raise


if __name__ == "__main__":
    main()
