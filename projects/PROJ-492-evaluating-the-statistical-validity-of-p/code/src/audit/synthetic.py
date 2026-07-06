"""
Synthetic Dataset Generator for A/B Test Audit Validation (FR-030).

Generates a synthetic dataset of at least 10,000 simulated A/B test summaries
containing both binary and continuous outcomes to validate the audit pipeline.
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
from code.src.models.data_models import ABTestSummary

# Constants
MIN_RECORDS = 10000
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
logger = get_default_logger()

def set_all_seeds(seed: int = SEED) -> None:
    """Initialize all random number generators for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

def generate_sample_sizes(n_total: int) -> Tuple[int, int]:
    """Generate realistic sample sizes for control and treatment groups."""
    # Sample sizes typically range from 100 to 10,000 per group
    n_control = int(np.random.lognormal(mean=4.0, sigma=0.5))
    n_treatment = int(np.random.lognormal(mean=4.0, sigma=0.5))
    # Ensure minimum sample size for statistical validity
    n_control = max(50, n_control)
    n_treatment = max(50, n_treatment)
    return n_control, n_treatment

def generate_binary_outcome(n_control: int, n_treatment: int, baseline_rate: float) -> Dict[str, Any]:
    """
    Generate synthetic binary outcome data.
    
    Returns:
        Dict with successes, totals, and calculated metrics.
    """
    # Introduce a small effect size (0% to 10% relative lift)
    effect_size = np.random.uniform(0.0, 0.10)
    treatment_rate = baseline_rate * (1 + effect_size)
    
    # Ensure rates stay within valid probability bounds
    treatment_rate = np.clip(treatment_rate, 0.01, 0.99)
    
    # Simulate binomial outcomes
    successes_control = np.random.binomial(n_control, baseline_rate)
    successes_treatment = np.random.binomial(n_treatment, treatment_rate)
    
    # Calculate observed rates
    rate_control = successes_control / n_control
    rate_treatment = successes_treatment / n_treatment
    
    # Calculate p-value using two-proportion z-test
    try:
        stat, p_value = stats.proportions_ztest(
            [successes_control, successes_treatment],
            [n_control, n_treatment]
        )
    except Exception:
        p_value = 0.5  # Fallback for edge cases
    
    return {
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "n_control": n_control,
        "n_treatment": n_treatment,
        "rate_control": float(rate_control),
        "rate_treatment": float(rate_treatment),
        "p_value": float(p_value),
        "effect_size": float(rate_treatment - rate_control),
        "outcome_type": "binary"
    }

def generate_continuous_outcome(n_control: int, n_treatment: int, baseline_mean: float) -> Dict[str, Any]:
    """
    Generate synthetic continuous outcome data.
    
    Returns:
        Dict with means, stds, totals, and calculated metrics.
    """
    # Introduce a small effect size (0% to 10% relative lift)
    effect_size = np.random.uniform(0.0, 0.10)
    treatment_mean = baseline_mean * (1 + effect_size)
    
    # Standard deviation typically 10-30% of mean
    std_dev = baseline_mean * np.random.uniform(0.1, 0.3)
    std_dev = max(0.01, std_dev)
    
    # Simulate normal outcomes
    data_control = np.random.normal(baseline_mean, std_dev, n_control)
    data_treatment = np.random.normal(treatment_mean, std_dev, n_treatment)
    
    # Calculate observed statistics
    mean_control = float(np.mean(data_control))
    mean_treatment = float(np.mean(data_treatment))
    std_control = float(np.std(data_control, ddof=1))
    std_treatment = float(np.std(data_treatment, ddof=1))
    
    # Calculate p-value using Welch's t-test
    try:
        stat, p_value = stats.ttest_ind(data_control, data_treatment, equal_var=False)
    except Exception:
        p_value = 0.5  # Fallback for edge cases
    
    return {
        "mean_control": mean_control,
        "mean_treatment": mean_treatment,
        "std_control": std_control,
        "std_treatment": std_treatment,
        "n_control": n_control,
        "n_treatment": n_treatment,
        "p_value": float(p_value),
        "effect_size": float(mean_treatment - mean_control),
        "outcome_type": "continuous"
    }

def generate_synthetic_dataset(n_records: int = MIN_RECORDS) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.
    
    Args:
        n_records: Number of records to generate (minimum 10,000).
        
    Returns:
        List of dictionaries representing synthetic A/B test summaries.
    """
    set_all_seeds()
    records = []
    
    # Ensure we generate at least MIN_RECORDS
    n_records = max(n_records, MIN_RECORDS)
    
    for i in range(n_records):
        # Alternate between binary and continuous outcomes
        is_binary = (i % 2 == 0)
        
        # Generate sample sizes
        n_control, n_treatment = generate_sample_sizes(n_records)
        
        if is_binary:
            # Binary outcome: baseline conversion rate between 0.05 and 0.5
            baseline_rate = np.random.uniform(0.05, 0.50)
            data = generate_binary_outcome(n_control, n_treatment, baseline_rate)
        else:
            # Continuous outcome: baseline mean between 10 and 1000
            baseline_mean = np.random.uniform(10, 1000)
            data = generate_continuous_outcome(n_control, n_treatment, baseline_mean)
        
        # Add metadata
        record = {
            "id": f"synthetic_{i:05d}",
            "url": f"https://example.com/ab-test/{i}",
            "domain": f"example.com",
            "year": np.random.choice([2021, 2022, 2023, 2024, 2025]),
            "title": f"Synthetic A/B Test {i}",
            "description": f"Generated synthetic test for validation purposes",
            **data
        }
        records.append(record)
    
    return records

def verify_outcome_types(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Verify that both binary and continuous outcomes are present.
    
    Args:
        records: List of generated records.
        
    Returns:
        Dictionary with counts of each outcome type.
    """
    counts = {"binary": 0, "continuous": 0}
    for record in records:
        outcome_type = record.get("outcome_type", "unknown")
        if outcome_type in counts:
            counts[outcome_type] += 1
        else:
            logger.warning(f"Unknown outcome type: {outcome_type}")
    
    logger.info(f"Outcome type verification: {counts}")
    
    # Assert both types are present
    if counts["binary"] == 0 or counts["continuous"] == 0:
        raise ValueError("Generated dataset must contain both binary and continuous outcomes")
    
    return counts

def write_csv_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic dataset to CSV file."""
    if not records:
        raise ValueError("No records to write")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define CSV columns
    fieldnames = [
        "id", "url", "domain", "year", "title", "description",
        "outcome_type", "n_control", "n_treatment",
        "p_value", "effect_size"
    ]
    
    # Add outcome-specific columns
    first_record = records[0]
    if first_record["outcome_type"] == "binary":
        fieldnames.extend(["successes_control", "successes_treatment", "rate_control", "rate_treatment"])
    else:
        fieldnames.extend(["mean_control", "mean_treatment", "std_control", "std_treatment"])
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            # Filter to only relevant columns for each record type
            row = {k: v for k, v in record.items() if k in fieldnames}
            writer.writerow(row)
    
    logger.info(f"Wrote {len(records)} records to {output_path}")

def write_json_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic dataset to JSON file."""
    if not records:
        raise ValueError("No records to write")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, default=str)
    
    logger.info(f"Wrote {len(records)} records to {output_path}")

def write_metadata(output_dir: Path, records: List[Dict[str, Any]], outcome_counts: Dict[str, int]) -> None:
    """Write metadata file describing the synthetic dataset."""
    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(records),
        "outcome_counts": outcome_counts,
        "min_records_required": MIN_RECORDS,
        "seed": SEED,
        "generator_version": "1.0.0"
    }
    
    metadata_path = output_dir / "synthetic_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Wrote metadata to {metadata_path}")

def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation (T026)")
    
    # Define output paths
    output_dir = Path("data/synthetic")
    csv_path = output_dir / "synthetic_summaries.csv"
    json_path = output_dir / "synthetic_summaries.json"
    
    # Generate dataset
    logger.info(f"Generating {MIN_RECORDS} synthetic records...")
    records = generate_synthetic_dataset(MIN_RECORDS)
    
    # Verify outcome types
    logger.info("Verifying outcome types...")
    outcome_counts = verify_outcome_types(records)
    
    # Validate record count
    if len(records) < MIN_RECORDS:
        raise ValueError(f"Generated {len(records)} records, expected at least {MIN_RECORDS}")
    
    # Write outputs
    logger.info("Writing CSV output...")
    write_csv_output(records, csv_path)
    
    logger.info("Writing JSON output...")
    write_json_output(records, json_path)
    
    logger.info("Writing metadata...")
    write_metadata(output_dir, records, outcome_counts)
    
    logger.info(f"Successfully generated synthetic dataset: {len(records)} records")
    logger.info(f"Outcome distribution: Binary={outcome_counts['binary']}, Continuous={outcome_counts['continuous']}")

if __name__ == "__main__":
    main()
