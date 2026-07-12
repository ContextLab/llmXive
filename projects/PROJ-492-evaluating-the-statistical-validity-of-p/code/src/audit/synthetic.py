"""
Synthetic Dataset Generator for A/B Test Validity Audit (FR-030)

Generates a synthetic corpus of A/B test summaries with known ground truth
to validate the statistical reconstruction and inconsistency detection pipeline.
Supports both binary and continuous outcomes with configurable effect sizes
and sample sizes to ensure constraint preservation.
"""

import csv
import json
import logging
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy import stats

# Import project-specific utilities and models
from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

# Constants
MIN_RECORDS = 10000
DOMAINS = [
    "tech_crunch",
    "nytimes",
    "medium",
    "linkedin",
    "twitter",
    "reddit",
    "hacker_news",
    "shopify_blog",
    "optimizely",
    "google_analytics"
]

# Outcome types
OUTCOME_BINARY = "binary"
OUTCOME_CONTINUOUS = "continuous"

logger: AuditLogger = get_default_logger(__name__)

def set_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

def generate_base_metadata(domain: str, year: Optional[int] = None) -> Dict[str, Any]:
    """Generate metadata for a synthetic record."""
    if year is None:
        year = random.randint(2018, 2024)
    
    return {
        "url": f"https://{domain}.example.com/experiment-{random.randint(1000, 9999)}",
        "domain": domain,
        "year": year,
        "timestamp": datetime.now().isoformat(),
        "repository_id": f"repo-{domain}-{year}"
    }

def generate_binary_summary(
    metadata: Dict[str, Any],
    true_baseline_rate: float,
    true_effect_size: float,
    n_control: int,
    n_treatment: int,
    noise_level: float = 0.0
) -> ABTestSummary:
    """
    Generate a binary outcome summary with known ground truth.
    
    Args:
        metadata: Base metadata dict
        true_baseline_rate: True conversion rate for control group
        true_effect_size: True lift (e.g., 0.05 for 5% lift)
        n_control: Sample size for control
        n_treatment: Sample size for treatment
        noise_level: Optional noise to add to reported values (0.0 = exact)
    
    Returns:
        ABTestSummary object
    """
    # Calculate true values
    baseline_rate = true_baseline_rate
    treatment_rate = baseline_rate * (1 + true_effect_size)
    
    # Simulate observed counts (with binomial noise)
    observed_control_successes = np.random.binomial(n_control, baseline_rate)
    observed_treatment_successes = np.random.binomial(n_treatment, treatment_rate)
    
    observed_baseline_rate = observed_control_successes / n_control
    observed_treatment_rate = observed_treatment_successes / n_treatment
    
    # Calculate true p-value using two-proportion z-test
    pooled_rate = (observed_control_successes + observed_treatment_successes) / (n_control + n_treatment)
    se = np.sqrt(pooled_rate * (1 - pooled_rate) * (1/n_control + 1/n_treatment))
    z_stat = (observed_treatment_rate - observed_baseline_rate) / se if se > 0 else 0
    true_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    # Add noise to reported values if requested
    reported_baseline = observed_baseline_rate * (1 + noise_level * (random.random() - 0.5))
    reported_treatment = observed_treatment_rate * (1 + noise_level * (random.random() - 0.5))
    reported_p_value = true_p_value * (1 + noise_level * (random.random() - 0.5))
    
    return ABTestSummary(
        url=metadata["url"],
        domain=metadata["domain"],
        year=metadata["year"],
        test_type="binary",
        baseline_rate=round(reported_baseline, 4),
        treatment_rate=round(reported_treatment, 4),
        sample_size_control=n_control,
        sample_size_treatment=n_treatment,
        reported_p_value=round(reported_p_value, 4),
        effect_size=round(reported_treatment_rate - reported_baseline_rate, 4),
        ground_truth_p_value=round(true_p_value, 4),
        ground_truth_effect_size=round(true_effect_size, 4),
        ground_truth_baseline_rate=round(true_baseline_rate, 4),
        is_inconsistent=abs(reported_p_value - true_p_value) > 0.05 or abs(reported_treatment_rate - true_treatment_rate) > 0.05 * true_treatment_rate
    )

def generate_continuous_summary(
    metadata: Dict[str, Any],
    true_baseline_mean: float,
    true_effect_size: float,
    baseline_std: float,
    n_control: int,
    n_treatment: int,
    noise_level: float = 0.0
) -> ABTestSummary:
    """
    Generate a continuous outcome summary with known ground truth.
    
    Args:
        metadata: Base metadata dict
        true_baseline_mean: True mean for control group
        true_effect_size: True lift (absolute difference)
        baseline_std: Standard deviation of the metric
        n_control: Sample size for control
        n_treatment: Sample size for treatment
        noise_level: Optional noise to add to reported values
    
    Returns:
        ABTestSummary object
    """
    # Calculate true values
    baseline_mean = true_baseline_mean
    treatment_mean = baseline_mean + true_effect_size
    
    # Simulate observed means (with sampling noise)
    observed_control = np.random.normal(baseline_mean, baseline_std, n_control)
    observed_treatment = np.random.normal(treatment_mean, baseline_std, n_treatment)
    
    observed_baseline_mean = np.mean(observed_control)
    observed_treatment_mean = np.mean(observed_treatment)
    observed_baseline_std = np.std(observed_control, ddof=1)
    observed_treatment_std = np.std(observed_treatment, ddof=1)
    
    # Calculate true p-value using Welch's t-test
    _, true_p_value = stats.ttest_ind(
        observed_control, observed_treatment, equal_var=False
    )
    
    # Add noise to reported values if requested
    reported_baseline = observed_baseline_mean * (1 + noise_level * (random.random() - 0.5))
    reported_treatment = observed_treatment_mean * (1 + noise_level * (random.random() - 0.5))
    reported_p_value = true_p_value * (1 + noise_level * (random.random() - 0.5))
    
    return ABTestSummary(
        url=metadata["url"],
        domain=metadata["domain"],
        year=metadata["year"],
        test_type="continuous",
        baseline_rate=round(reported_baseline, 4),
        treatment_rate=round(reported_treatment, 4),
        sample_size_control=n_control,
        sample_size_treatment=n_treatment,
        reported_p_value=round(reported_p_value, 4),
        effect_size=round(reported_treatment_mean - reported_baseline_mean, 4),
        ground_truth_p_value=round(true_p_value, 4),
        ground_truth_effect_size=round(true_effect_size, 4),
        ground_truth_baseline_rate=round(true_baseline_mean, 4),
        is_inconsistent=abs(reported_p_value - true_p_value) > 0.05 or abs(reported_treatment_mean - true_effect_size - true_baseline_mean) > 0.05 * true_baseline_mean
    )

def generate_synthetic_corpus(
    output_dir: Path,
    total_records: int = MIN_RECORDS,
    binary_ratio: float = 0.6,
    noise_level: float = 0.0
) -> Tuple[Path, Path]:
    """
    Generate a synthetic corpus of A/B test summaries.
    
    Args:
        output_dir: Directory to write output files
        total_records: Total number of records to generate
        binary_ratio: Proportion of binary outcomes (0.0-1.0)
        noise_level: Noise level for reported values (0.0 = exact)
    
    Returns:
        Tuple of (summary_csv_path, ground_truth_json_path)
    """
    set_seeds(SEED)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summaries: List[ABTestSummary] = []
    ground_truth: List[Dict[str, Any]] = []
    
    binary_count = int(total_records * binary_ratio)
    continuous_count = total_records - binary_count
    
    logger.info(f"Generating {binary_count} binary and {continuous_count} continuous records...")
    
    # Generate binary records
    for i in range(binary_count):
        domain = random.choice(DOMAINS)
        year = random.randint(2018, 2024)
        metadata = generate_base_metadata(domain, year)
        
        # Vary parameters to create realistic diversity
        true_baseline = random.uniform(0.05, 0.30)
        true_effect = random.uniform(-0.10, 0.20)  # Can be negative or positive
        n_control = random.randint(500, 5000)
        n_treatment = random.randint(500, 5000)
        
        summary = generate_binary_summary(
            metadata, true_baseline, true_effect, n_control, n_treatment, noise_level
        )
        summaries.append(summary)
        
        # Store ground truth separately
        ground_truth.append({
            "url": summary.url,
            "domain": summary.domain,
            "year": summary.year,
            "test_type": "binary",
            "ground_truth_baseline_rate": summary.ground_truth_baseline_rate,
            "ground_truth_effect_size": summary.ground_truth_effect_size,
            "ground_truth_p_value": summary.ground_truth_p_value,
            "sample_size_control": summary.sample_size_control,
            "sample_size_treatment": summary.sample_size_treatment,
            "is_inconsistent": summary.is_inconsistent
        })
    
    # Generate continuous records
    for i in range(continuous_count):
        domain = random.choice(DOMAINS)
        year = random.randint(2018, 2024)
        metadata = generate_base_metadata(domain, year)
        
        true_baseline = random.uniform(10.0, 100.0)
        true_effect = random.uniform(-5.0, 15.0)
        baseline_std = random.uniform(5.0, 20.0)
        n_control = random.randint(500, 5000)
        n_treatment = random.randint(500, 5000)
        
        summary = generate_continuous_summary(
            metadata, true_baseline, true_effect, baseline_std, n_control, n_treatment, noise_level
        )
        summaries.append(summary)
        
        ground_truth.append({
            "url": summary.url,
            "domain": summary.domain,
            "year": summary.year,
            "test_type": "continuous",
            "ground_truth_baseline_rate": summary.ground_truth_baseline_rate,
            "ground_truth_effect_size": summary.ground_truth_effect_size,
            "ground_truth_p_value": summary.ground_truth_p_value,
            "sample_size_control": summary.sample_size_control,
            "sample_size_treatment": summary.sample_size_treatment,
            "is_inconsistent": summary.is_inconsistent
        })
    
    # Write summaries to CSV
    csv_path = output_dir / "synthetic_summaries.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            "url", "domain", "year", "test_type", "baseline_rate", "treatment_rate",
            "sample_size_control", "sample_size_treatment", "reported_p_value",
            "effect_size", "is_inconsistent"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in summaries:
            writer.writerow({
                "url": s.url,
                "domain": s.domain,
                "year": s.year,
                "test_type": s.test_type,
                "baseline_rate": s.baseline_rate,
                "treatment_rate": s.treatment_rate,
                "sample_size_control": s.sample_size_control,
                "sample_size_treatment": s.sample_size_treatment,
                "reported_p_value": s.reported_p_value,
                "effect_size": s.effect_size,
                "is_inconsistent": s.is_inconsistent
            })
    
    # Write ground truth to JSON
    gt_path = output_dir / "synthetic_ground_truth.json"
    with open(gt_path, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2)
    
    logger.info(f"Generated {len(summaries)} records to {csv_path}")
    logger.info(f"Ground truth written to {gt_path}")
    
    return csv_path, gt_path

def main():
    """Entry point for synthetic data generation."""
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting synthetic dataset generation...")
    
    csv_path, gt_path = generate_synthetic_corpus(
        output_dir=output_dir,
        total_records=MIN_RECORDS,
        binary_ratio=0.6,
        noise_level=0.0  # Exact values for validation
    )
    
    # Verify record count
    with open(csv_path, 'r') as f:
        record_count = sum(1 for _ in f) - 1  # Exclude header
    
    if record_count < MIN_RECORDS:
        logger.error(f"Generated only {record_count} records, expected >= {MIN_RECORDS}")
        sys.exit(1)
    
    logger.info(f"Success: Generated {record_count} records (>= {MIN_RECORDS})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
