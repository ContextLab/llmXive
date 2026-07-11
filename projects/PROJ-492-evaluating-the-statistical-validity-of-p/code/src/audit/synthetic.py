"""
Synthetic dataset generator for A/B test validity evaluation.

Generates a large corpus of synthetic A/B test summaries with both binary
and continuous outcomes, preserving statistical constraints and ground truth
labels for validation purposes (FR-030).
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger
from code.src.models.data_models import ABTestSummary

# Constants for generation
MIN_SAMPLE_SIZE = 50
MAX_SAMPLE_SIZE = 10000
BINARY_BASELINE_RANGE = (0.05, 0.50)
CONTINUOUS_MEAN_RANGE = (10.0, 100.0)
CONTINUOUS_STD_RANGE = (5.0, 20.0)
EFFECT_SIZE_RANGE = (0.01, 0.15)  # Small to medium effects
DOMAINS = ["tech", "finance", "health", "e-commerce", "education"]
YEARS = list(range(2018, 2025))

logger = get_default_logger(__name__)

def set_all_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds set to {seed} for reproducibility")

def generate_sample_sizes() -> Tuple[int, int]:
    """Generate realistic sample sizes for control and treatment groups."""
    n_control = random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
    # Treatment size is typically similar but can vary slightly
    n_treatment = random.randint(
        int(n_control * 0.8), int(n_control * 1.2)
    )
    return n_control, n_treatment

def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: Optional[float] = None,
    effect_size: Optional[float] = None,
    make_inconsistent: bool = False,
) -> Dict[str, Any]:
    """
    Generate binary outcome data (conversion rates).
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_rate: Conversion rate for control group (0-1)
        effect_size: Absolute difference in conversion rates
        make_inconsistent: If True, introduce statistical inconsistency
        
    Returns:
        Dictionary with ground truth and reported metrics
    """
    if baseline_rate is None:
        baseline_rate = random.uniform(*BINARY_BASELINE_RANGE)
    
    if effect_size is None:
        effect_size = random.uniform(*EFFECT_SIZE_RANGE)
    
    # Determine direction of effect
    direction = random.choice([-1, 1])
    treatment_rate = baseline_rate + (direction * effect_size)
    
    # Ensure rates stay within valid bounds
    treatment_rate = max(0.001, min(0.999, treatment_rate))
    
    # Generate actual successes
    successes_control = np.random.binomial(n_control, baseline_rate)
    successes_treatment = np.random.binomial(n_treatment, treatment_rate)
    
    # Calculate observed rates
    observed_rate_control = successes_control / n_control
    observed_rate_treatment = successes_treatment / n_treatment
    
    # Calculate true p-value using two-proportion z-test
    stat, true_p_value = stats.proportions_ztest(
        [successes_control, successes_treatment],
        [n_control, n_treatment]
    )
    
    # Calculate effect size (Cohen's h for proportions)
    effect_h = 2 * (np.arcsin(np.sqrt(observed_rate_treatment)) - 
                   np.arcsin(np.sqrt(observed_rate_control)))
    
    # Introduce inconsistency if requested
    if make_inconsistent:
        # Inflate p-value to make it appear non-significant when it should be
        reported_p_value = min(1.0, true_p_value * random.uniform(1.5, 3.0))
        # Or distort effect size
        reported_effect_size = effect_h * random.uniform(0.5, 1.5)
    else:
        reported_p_value = true_p_value
        reported_effect_size = effect_h
    
    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "baseline_rate": baseline_rate,
        "treatment_rate": treatment_rate,
        "observed_rate_control": observed_rate_control,
        "observed_rate_treatment": observed_rate_treatment,
        "true_p_value": true_p_value,
        "reported_p_value": reported_p_value,
        "true_effect_size": effect_h,
        "reported_effect_size": reported_effect_size,
        "is_significant": reported_p_value < 0.05,
        "is_inconsistent": make_inconsistent
    }

def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    mean_control: Optional[float] = None,
    mean_treatment: Optional[float] = None,
    std_dev: Optional[float] = None,
    make_inconsistent: bool = False,
) -> Dict[str, Any]:
    """
    Generate continuous outcome data (e.g., time on page, revenue).
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        mean_control: Mean for control group
        mean_treatment: Mean for treatment group
        std_dev: Standard deviation (assumed equal for both groups)
        make_inconsistent: If True, introduce statistical inconsistency
        
    Returns:
        Dictionary with ground truth and reported metrics
    """
    if mean_control is None:
        mean_control = random.uniform(*CONTINUOUS_MEAN_RANGE)
    
    if mean_treatment is None:
        effect_size = random.uniform(*EFFECT_SIZE_RANGE)
        direction = random.choice([-1, 1])
        mean_treatment = mean_control + (direction * effect_size * mean_control)
    
    if std_dev is None:
        std_dev = random.uniform(*CONTINUOUS_STD_RANGE)
    
    # Generate actual data points
    data_control = np.random.normal(mean_control, std_dev, n_control)
    data_treatment = np.random.normal(mean_treatment, std_dev, n_treatment)
    
    # Calculate observed statistics
    obs_mean_control = np.mean(data_control)
    obs_mean_treatment = np.mean(data_treatment)
    obs_std_control = np.std(data_control, ddof=1)
    obs_std_treatment = np.std(data_treatment, ddof=1)
    
    # Calculate true p-value using Welch's t-test
    stat, true_p_value = stats.ttest_ind(
        data_control, data_treatment, equal_var=False
    )
    
    # Calculate effect size (Cohen's d)
    pooled_std = np.sqrt((obs_std_control**2 + obs_std_treatment**2) / 2)
    true_effect_size = (obs_mean_treatment - obs_mean_control) / pooled_std
    
    # Introduce inconsistency if requested
    if make_inconsistent:
        reported_p_value = min(1.0, true_p_value * random.uniform(1.5, 3.0))
        reported_effect_size = true_effect_size * random.uniform(0.5, 1.5)
    else:
        reported_p_value = true_p_value
        reported_effect_size = true_effect_size
    
    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": mean_control,
        "mean_treatment": mean_treatment,
        "obs_mean_control": obs_mean_control,
        "obs_mean_treatment": obs_mean_treatment,
        "obs_std_control": obs_std_control,
        "obs_std_treatment": obs_std_treatment,
        "true_p_value": true_p_value,
        "reported_p_value": reported_p_value,
        "true_effect_size": true_effect_size,
        "reported_effect_size": reported_effect_size,
        "is_significant": reported_p_value < 0.05,
        "is_inconsistent": make_inconsistent
    }

def generate_synthetic_dataset(
    num_records: int = 10000,
    output_dir: Optional[Path] = None,
    seed: int = SEED,
) -> Path:
    """
    Generate a synthetic dataset of A/B test summaries.
    
    Args:
        num_records: Number of records to generate (default 10,000)
        output_dir: Directory to write output files
        seed: Random seed for reproducibility
        
    Returns:
        Path to the generated CSV file
    """
    set_all_seeds(seed)
    
    if output_dir is None:
        output_dir = Path("data/synthetic")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    records = []
    inconsistent_count = 0
    
    logger.info(f"Generating {num_records} synthetic A/B test records...")
    
    for i in range(num_records):
        # Decide outcome type: 60% binary, 40% continuous
        is_binary = random.random() < 0.6
        
        # Decide if this should be inconsistent (15% rate)
        make_inconsistent = random.random() < 0.15
        if make_inconsistent:
            inconsistent_count += 1
        
        # Generate sample sizes
        n_control, n_treatment = generate_sample_sizes()
        
        # Generate outcome data
        if is_binary:
            data = generate_binary_outcome(
                n_control, n_treatment,
                make_inconsistent=make_inconsistent
            )
            outcome_type = "binary"
            metric_name = "conversion_rate"
        else:
            data = generate_continuous_outcome(
                n_control, n_treatment,
                make_inconsistent=make_inconsistent
            )
            outcome_type = "continuous"
            metric_name = "continuous_metric"
        
        # Add metadata
        record = {
            "id": f"synthetic_{i:06d}",
            "outcome_type": outcome_type,
            "metric_name": metric_name,
            "domain": random.choice(DOMAINS),
            "year": random.choice(YEARS),
            "n_control": data["n_control"],
            "n_treatment": data["n_treatment"],
            "observed_rate_control": data.get("observed_rate_control"),
            "observed_rate_treatment": data.get("observed_rate_treatment"),
            "obs_mean_control": data.get("obs_mean_control"),
            "obs_mean_treatment": data.get("obs_mean_treatment"),
            "obs_std_control": data.get("obs_std_control"),
            "obs_std_treatment": data.get("obs_std_treatment"),
            "reported_p_value": data["reported_p_value"],
            "reported_effect_size": data["reported_effect_size"],
            "true_p_value": data["true_p_value"],
            "true_effect_size": data["true_effect_size"],
            "is_significant": data["is_significant"],
            "is_inconsistent": data["is_inconsistent"],
            "ground_truth_label": "inconsistent" if make_inconsistent else "consistent"
        }
        
        records.append(record)
        
        if (i + 1) % 1000 == 0:
            logger.info(f"Generated {i + 1} records...")
    
    # Write to CSV
    output_file = output_dir / "synthetic_ab_tests.csv"
    fieldnames = list(records[0].keys())
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    # Write metadata
    metadata = {
        "total_records": num_records,
        "binary_count": sum(1 for r in records if r["outcome_type"] == "binary"),
        "continuous_count": sum(1 for r in records if r["outcome_type"] == "continuous"),
        "inconsistent_count": inconsistent_count,
        "inconsistent_rate": inconsistent_count / num_records,
        "domains": {d: sum(1 for r in records if r["domain"] == d) for d in DOMAINS},
        "years": {y: sum(1 for r in records if r["year"] == y) for y in YEARS},
        "seed": seed,
        "generated_at": datetime.now().isoformat(),
        "file_path": str(output_file)
    }
    
    metadata_file = output_dir / "synthetic_metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Generated {num_records} records with {inconsistent_count} inconsistent ({inconsistent_count/num_records:.1%})")
    logger.info(f"Output written to {output_file}")
    logger.info(f"Metadata written to {metadata_file}")
    
    return output_file

def verify_outcome_types(input_file: Path) -> Tuple[int, int]:
    """
    Verify that the generated dataset contains both binary and continuous outcomes.
    
    Args:
        input_file: Path to the generated CSV file
        
    Returns:
        Tuple of (binary_count, continuous_count)
    """
    binary_count = 0
    continuous_count = 0
    
    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["outcome_type"] == "binary":
                binary_count += 1
            elif row["outcome_type"] == "continuous":
                continuous_count += 1
    
    logger.info(f"Verification: {binary_count} binary, {continuous_count} continuous")
    return binary_count, continuous_count

def write_summaries_to_csv(
    summaries: List[ABTestSummary],
    output_path: Path,
) -> None:
    """Write a list of ABTestSummary objects to a CSV file."""
    fieldnames = [
        "id", "url", "domain", "year", "outcome_type",
        "n_control", "n_treatment", "metric_name",
        "observed_rate_control", "observed_rate_treatment",
        "obs_mean_control", "obs_mean_treatment", "obs_std_control", "obs_std_treatment",
        "reported_p_value", "reported_effect_size",
        "reconstructed_p_value", "is_inconsistent"
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for summary in summaries:
            row = summary.model_dump(mode="json")
            writer.writerow(row)

def write_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """Write metadata dictionary to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation (T026)...")
    
    output_dir = Path("data/synthetic")
    output_file = generate_synthetic_dataset(
        num_records=10000,
        output_dir=output_dir,
        seed=SEED
    )
    
    # Verify outcome types
    binary_count, continuous_count = verify_outcome_types(output_file)
    
    if binary_count == 0 or continuous_count == 0:
        logger.error("Generated dataset missing one outcome type!")
        raise ValueError("Dataset must contain both binary and continuous outcomes")
    
    # Verify record count
    if binary_count + continuous_count < 10000:
        logger.error(f"Generated {binary_count + continuous_count} records, expected >= 10000")
        raise ValueError("Insufficient records generated")
    
    logger.info("Synthetic dataset generation completed successfully.")
    logger.info(f"Total records: {binary_count + continuous_count}")
    logger.info(f"Binary: {binary_count}, Continuous: {continuous_count}")

if __name__ == "__main__":
    main()