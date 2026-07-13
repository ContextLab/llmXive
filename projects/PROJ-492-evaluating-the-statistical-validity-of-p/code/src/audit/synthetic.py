"""
Synthetic Dataset Generator for A/B Test Validity Audit.

Implements FR-030: Generates a synthetic corpus of A/B test summaries
with known ground truth for binary and continuous outcomes.
Ensures constraint preservation (statistical consistency) for the majority
of records, with a controlled injection of inconsistencies for validation.
"""
import json
import csv
import logging
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats
from scipy.stats import norm, t as t_dist, binom as binom_dist

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger
from code.src.models.data_models import ABTestSummary

logger = get_default_logger(__name__)

# Configuration constants
DEFAULT_SEED = 42
TOTAL_RECORDS = 10500  # Exceeds 10,000 requirement
BINARY_RATIO = 0.6     # 60% binary outcomes
CONTINUOUS_RATIO = 0.4 # 40% continuous outcomes
CONSISTENCY_RATE = 0.92 # 92% of records will be statistically consistent

def set_seeds(seed: int = DEFAULT_SEED) -> None:
    """Ensure deterministic generation."""
    set_rng_seed(seed)
    np.random.seed(seed)

def generate_binary_summary(
    rng: np.random.Generator,
    is_consistent: bool = True,
    force_inconsistency: bool = False
) -> Tuple[Dict[str, Any], bool]:
    """
    Generate a synthetic ABTestSummary for a binary outcome (conversion rate).
    Uses two-proportion z-test logic.
    """
    # Sample sizes
    n_control = rng.integers(100, 5000)
    n_treatment = rng.integers(100, 5000)

    # Baseline conversion rate
    p_control = rng.uniform(0.05, 0.30)

    # Effect size (lift)
    lift = rng.uniform(-0.2, 0.3) # -20% to +30% lift
    p_treatment = p_control * (1 + lift)
    p_treatment = np.clip(p_treatment, 0.01, 0.99)

    # Calculate expected successes
    successes_control = int(n_control * p_control)
    successes_treatment = int(n_treatment * p_treatment)

    # Reconstruct p-value from these counts (Ground Truth)
    # Use normal approximation for large N, exact for small N
    if n_control < 30 or n_treatment < 30:
        # Fallback to Fisher's logic simulation if needed, but for synthetic
        # we generate the "reported" p-value based on the counts.
        # We will use the z-statistic for consistency generation.
        pass

    # Calculate Z-statistic manually
    p_pooled = (successes_control + successes_treatment) / (n_control + n_treatment)
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))
    
    if se == 0:
        z_stat = 0.0
    else:
        p_diff = (successes_treatment/n_treatment) - (successes_control/n_control)
        z_stat = p_diff / se

    # Calculate true p-value (two-tailed)
    true_p_value = 2 * (1 - norm.cdf(abs(z_stat)))

    # Determine reported p-value
    if is_consistent:
        reported_p_value = true_p_value
    else:
        # Inject inconsistency: shift p-value significantly
        # If true p < 0.05, report > 0.05, or vice versa, with noise
        if true_p_value < 0.05:
            reported_p_value = rng.uniform(0.06, 0.20)
        else:
            reported_p_value = rng.uniform(0.01, 0.04)

    # Calculate effect size (difference in proportions)
    effect_size = (successes_treatment / n_treatment) - (successes_control / n_control)
    
    # Confidence Interval for effect size (95%)
    se_diff = math.sqrt(
        (successes_control/n_control)*(1-successes_control/n_control)/n_control +
        (successes_treatment/n_treatment)*(1-successes_treatment/n_treatment)/n_treatment
    )
    ci_lower = effect_size - 1.96 * se_diff
    ci_upper = effect_size + 1.96 * se_diff

    return {
        "test_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": successes_control,
        "successes_treatment": successes_treatment,
        "baseline_rate": p_control,
        "treatment_rate": p_treatment,
        "reported_p_value": reported_p_value,
        "true_p_value": true_p_value,
        "effect_size": effect_size,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "is_consistent": is_consistent,
        "domain": rng.choice(["ecommerce", "saaS", "media", "finance"]),
        "year": rng.integers(2018, 2025)
    }, is_consistent

def generate_continuous_summary(
    rng: np.random.Generator,
    is_consistent: bool = True
) -> Tuple[Dict[str, Any], bool]:
    """
    Generate a synthetic ABTestSummary for a continuous outcome (e.g., time on site, revenue).
    Uses Welch's t-test logic.
    """
    n_control = rng.integers(50, 2000)
    n_treatment = rng.integers(50, 2000)

    mean_control = rng.uniform(10.0, 100.0)
    std_control = rng.uniform(2.0, 20.0)
    
    # Lift in mean
    lift = rng.uniform(-0.15, 0.20)
    mean_treatment = mean_control * (1 + lift)
    std_treatment = std_control * rng.uniform(0.8, 1.2) # Slight variance variation

    # Calculate Welch's t-statistic
    se_control = std_control / math.sqrt(n_control)
    se_treatment = std_treatment / math.sqrt(n_treatment)
    se_diff = math.sqrt(se_control**2 + se_treatment**2)

    if se_diff == 0:
        t_stat = 0.0
    else:
        t_stat = (mean_treatment - mean_control) / se_diff

    # Degrees of freedom (Welch-Satterthwaite)
    num = (se_control**2 + se_treatment**2)**2
    denom = (se_control**4 / (n_control - 1)) + (se_treatment**4 / (n_treatment - 1))
    if denom == 0:
        df = 1
    else:
        df = num / denom

    true_p_value = 2 * (1 - t_dist.cdf(abs(t_stat), df))

    if is_consistent:
        reported_p_value = true_p_value
    else:
        if true_p_value < 0.05:
            reported_p_value = rng.uniform(0.06, 0.20)
        else:
            reported_p_value = rng.uniform(0.01, 0.04)

    effect_size = mean_treatment - mean_control

    return {
        "test_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": mean_control,
        "mean_treatment": mean_treatment,
        "std_control": std_control,
        "std_treatment": std_treatment,
        "reported_p_value": reported_p_value,
        "true_p_value": true_p_value,
        "effect_size": effect_size,
        "is_consistent": is_consistent,
        "domain": rng.choice(["ecommerce", "saaS", "media", "finance"]),
        "year": rng.integers(2018, 2025)
    }, is_consistent

def generate_synthetic_dataset(
    output_dir: Path,
    total_records: int = TOTAL_RECORDS,
    seed: int = DEFAULT_SEED
) -> Tuple[Path, Path]:
    """
    Generates the synthetic dataset files.
    Returns paths to the generated JSON (summaries) and CSV (ground truth).
    """
    set_seeds(seed)
    rng = np.random.default_rng(seed)

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "synthetic_summaries.json"
    csv_path = output_dir / "synthetic_ground_truth.csv"

    records = []
    ground_truth_rows = []

    consistent_count = 0
    inconsistent_count = 0

    logger.info(f"Generating {total_records} synthetic records...")

    for i in range(total_records):
        # Determine outcome type
        is_binary = rng.random() < BINARY_RATIO
        
        # Determine consistency
        is_consistent = rng.random() < CONSISTENCY_RATE

        if is_binary:
            data, is_consistent = generate_binary_summary(rng, is_consistent)
        else:
            data, is_consistent = generate_continuous_summary(rng, is_consistent)

        if is_consistent:
            consistent_count += 1
        else:
            inconsistent_count += 1

        # Format for ABTestSummary model (simplified for JSON)
        summary_record = {
            "id": f"syn_{i:05d}",
            "url": f"https://example.com/test_{i}",
            "domain": data["domain"],
            "year": data["year"],
            "test_type": data["test_type"],
            "n_control": data["n_control"],
            "n_treatment": data["n_treatment"],
            "reported_p_value": round(data["reported_p_value"], 6),
            "effect_size": round(data["effect_size"], 6),
            # Include raw data for reconstruction validation
            "raw_data": data
        }
        records.append(summary_record)

        # Ground truth row for evaluation
        gt_row = {
            "id": f"syn_{i:05d}",
            "test_type": data["test_type"],
            "true_p_value": round(data["true_p_value"], 6),
            "reported_p_value": round(data["reported_p_value"], 6),
            "is_consistent": is_consistent,
            "domain": data["domain"],
            "year": data["year"]
        }
        ground_truth_rows.append(gt_row)

        if (i + 1) % 1000 == 0:
            logger.info(f"Generated {i + 1}/{total_records} records...")

    # Write JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
    
    # Write CSV Ground Truth
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=ground_truth_rows[0].keys())
        writer.writeheader()
        writer.writerows(ground_truth_rows)

    logger.info(f"Generated {consistent_count} consistent and {inconsistent_count} inconsistent records.")
    logger.info(f"Files written to: {json_path} and {csv_path}")

    return json_path, csv_path

def main() -> int:
    """Entry point for synthetic data generation."""
    output_dir = Path("data/synthetic")
    try:
        json_path, csv_path = generate_synthetic_dataset(output_dir)
        print(f"SUCCESS: Synthetic dataset generated.")
        print(f"  Summaries: {json_path}")
        print(f"  Ground Truth: {csv_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
