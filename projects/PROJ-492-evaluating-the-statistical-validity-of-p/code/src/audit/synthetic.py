"""
Synthetic dataset generator for A/B test validity evaluation (FR-030).

Generates a large-scale synthetic dataset of A/B test summaries with
both binary and continuous outcomes, ensuring statistical consistency
constraints are preserved for a majority of records while introducing
controlled inconsistencies for validation purposes.

Outputs:
    - data/synthetic/ab_summaries_binary.csv
    - data/synthetic/ab_summaries_continuous.csv
    - data/synthetic/ab_summaries_combined.json
"""
import csv
import json
import logging
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger
from code.src.models.data_models import ABTestSummary

# Configuration constants
NUM_BINARY_RECORDS = 5000
NUM_CONTINUOUS_RECORDS = 5000
CONSISTENCY_RATE = 0.95  # 95% of records will be statistically consistent
INCONSISTENCY_TYPES = ["p_value_drift", "effect_size_drift", "sample_size_mismatch"]

# Domain list for diversity
DOMAINS = [
    "techcrunch.com", "medium.com", "neilpatel.com", "optimizely.com",
    "vwo.com", "google-analytics.com", "hubspot.com", "salesforce.com",
    "stripe.com", "shopify.com"
]

logger = get_default_logger(__name__)

def set_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed}")

def generate_binary_test_record(
    is_consistent: bool,
    domain: str,
    record_id: int
) -> Dict[str, Any]:
    """
    Generate a synthetic binary outcome A/B test record.
    
    Args:
        is_consistent: Whether the record should be statistically consistent
        domain: The domain/source of the test
        record_id: Unique identifier for the record
        
    Returns:
        Dictionary containing all required fields for ABTestSummary
    """
    # Generate base parameters
    n_control = random.randint(1000, 50000)
    n_treatment = random.randint(1000, 50000)
    
    # Ensure sample sizes are close for most records (realistic scenario)
    if is_consistent and random.random() > 0.1:
        n_treatment = int(n_control * random.uniform(0.9, 1.1))
    
    baseline_rate = random.uniform(0.05, 0.30)
    
    # Decide effect size
    if random.random() < 0.7:
        # Small to medium effect
        effect_size = random.uniform(-0.05, 0.05)
    else:
        # Large effect
        effect_size = random.uniform(-0.15, 0.15)
    
    treatment_rate = baseline_rate + effect_size
    treatment_rate = max(0.01, min(0.99, treatment_rate))
    
    # Calculate expected conversions
    x_control = int(n_control * baseline_rate)
    x_treatment = int(n_treatment * treatment_rate)
    
    # Calculate true p-value using two-proportion z-test
    try:
        pooled_p = (x_control + x_treatment) / (n_control + n_treatment)
        se = math.sqrt(pooled_p * (1 - pooled_p) * (1/n_control + 1/n_treatment))
        z_stat = (treatment_rate - baseline_rate) / se
        true_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    except Exception:
        true_p_value = 1.0
    
    if is_consistent:
        reported_p_value = true_p_value
    else:
        # Introduce inconsistency
        inconsistency_type = random.choice(INCONSISTENCY_TYPES)
        if inconsistency_type == "p_value_drift":
            # Report a significantly different p-value
            reported_p_value = true_p_value * random.uniform(0.1, 10.0)
            reported_p_value = max(0.001, min(0.999, reported_p_value))
        elif inconsistency_type == "effect_size_drift":
            # Adjust rates to create effect size mismatch
            reported_p_value = true_p_value
            # We'll handle this by adjusting the reported effect size later
        else:
            # Sample size mismatch - handled by adjusting n values
            n_control = int(n_control * random.uniform(0.5, 1.5))
            n_treatment = int(n_treatment * random.uniform(0.5, 1.5))
            reported_p_value = true_p_value
    
    # Generate metadata
    days_ago = random.randint(1, 1000)
    test_date = datetime.now() - timedelta(days=days_ago)
    
    record = {
        "id": f"B{record_id:05d}",
        "url": f"https://{domain}/ab-test-{record_id}",
        "domain": domain,
        "test_date": test_date.strftime("%Y-%m-%d"),
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "baseline_conversion_rate": round(baseline_rate, 4),
        "treatment_conversion_rate": round(treatment_rate, 4),
        "reported_p_value": round(reported_p_value, 4),
        "reported_effect_size": round(effect_size, 4),
        "reported_confidence_interval": f"({round(effect_size - 1.96*abs(effect_size)*0.1, 4)}, {round(effect_size + 1.96*abs(effect_size)*0.1, 4)})",
        "test_duration_days": random.randint(7, 60),
        "is_consistent": is_consistent,
        "inconsistency_type": None if is_consistent else inconsistency_type
    }
    
    return record

def generate_continuous_test_record(
    is_consistent: bool,
    domain: str,
    record_id: int
) -> Dict[str, Any]:
    """
    Generate a synthetic continuous outcome A/B test record.
    
    Args:
        is_consistent: Whether the record should be statistically consistent
        domain: The domain/source of the test
        record_id: Unique identifier for the record
        
    Returns:
        Dictionary containing all required fields for ABTestSummary
    """
    # Generate base parameters
    n_control = random.randint(500, 20000)
    n_treatment = random.randint(500, 20000)
    
    # Ensure sample sizes are close for most records
    if is_consistent and random.random() > 0.1:
        n_treatment = int(n_control * random.uniform(0.9, 1.1))
    
    baseline_mean = random.uniform(10.0, 100.0)
    baseline_std = random.uniform(baseline_mean * 0.1, baseline_mean * 0.5)
    
    # Decide effect size (Cohen's d)
    if random.random() < 0.7:
        effect_size = random.uniform(-0.2, 0.2)  # Small to medium
    else:
        effect_size = random.uniform(-0.8, 0.8)  # Large
    
    treatment_mean = baseline_mean + (effect_size * baseline_std)
    treatment_std = baseline_std * random.uniform(0.8, 1.2)
    
    # Calculate true p-value using Welch's t-test
    try:
        se_diff = math.sqrt((baseline_std**2 / n_control) + (treatment_std**2 / n_treatment))
        t_stat = (treatment_mean - baseline_mean) / se_diff
        # Approximate degrees of freedom for Welch's t-test
        df_num = ((baseline_std**2 / n_control) + (treatment_std**2 / n_treatment))**2
        df_den = ((baseline_std**2 / n_control)**2 / (n_control - 1)) + ((treatment_std**2 / n_treatment)**2 / (n_treatment - 1))
        df = df_num / df_den if df_den > 0 else 1
        true_p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    except Exception:
        true_p_value = 1.0
    
    if is_consistent:
        reported_p_value = true_p_value
    else:
        # Introduce inconsistency
        inconsistency_type = random.choice(INCONSISTENCY_TYPES)
        if inconsistency_type == "p_value_drift":
            reported_p_value = true_p_value * random.uniform(0.1, 10.0)
            reported_p_value = max(0.001, min(0.999, reported_p_value))
        elif inconsistency_type == "effect_size_drift":
            reported_p_value = true_p_value
        else:
            n_control = int(n_control * random.uniform(0.5, 1.5))
            n_treatment = int(n_treatment * random.uniform(0.5, 1.5))
            reported_p_value = true_p_value
    
    # Generate metadata
    days_ago = random.randint(1, 1000)
    test_date = datetime.now() - timedelta(days=days_ago)
    
    record = {
        "id": f"C{record_id:05d}",
        "url": f"https://{domain}/ab-test-{record_id}",
        "domain": domain,
        "test_date": test_date.strftime("%Y-%m-%d"),
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "baseline_mean": round(baseline_mean, 4),
        "baseline_std": round(baseline_std, 4),
        "treatment_mean": round(treatment_mean, 4),
        "treatment_std": round(treatment_std, 4),
        "reported_p_value": round(reported_p_value, 4),
        "reported_effect_size": round(effect_size, 4),
        "reported_confidence_interval": f"({round(effect_size - 1.96*abs(effect_size)*0.1, 4)}, {round(effect_size + 1.96*abs(effect_size)*0.1, 4)})",
        "test_duration_days": random.randint(7, 60),
        "is_consistent": is_consistent,
        "inconsistency_type": None if is_consistent else inconsistency_type
    }
    
    return record

def write_binary_csv(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write binary test records to CSV."""
    fieldnames = [
        "id", "url", "domain", "test_date", "outcome_type",
        "n_control", "n_treatment", "baseline_conversion_rate",
        "treatment_conversion_rate", "reported_p_value", "reported_effect_size",
        "reported_confidence_interval", "test_duration_days",
        "is_consistent", "inconsistency_type"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Written {len(records)} binary records to {output_path}")

def write_continuous_csv(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write continuous test records to CSV."""
    fieldnames = [
        "id", "url", "domain", "test_date", "outcome_type",
        "n_control", "n_treatment", "baseline_mean", "baseline_std",
        "treatment_mean", "treatment_std", "reported_p_value",
        "reported_effect_size", "reported_confidence_interval",
        "test_duration_days", "is_consistent", "inconsistency_type"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Written {len(records)} continuous records to {output_path}")

def write_combined_json(binary_records: List[Dict[str, Any]], 
                       continuous_records: List[Dict[str, Any]], 
                       output_path: Path) -> None:
    """Write combined dataset to JSON."""
    combined = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_records": len(binary_records) + len(continuous_records),
            "binary_count": len(binary_records),
            "continuous_count": len(continuous_records),
            "consistency_rate": CONSISTENCY_RATE,
            "seed": SEED
        },
        "binary_outcomes": binary_records,
        "continuous_outcomes": continuous_records
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined, f, indent=2)
    
    logger.info(f"Written combined dataset ({len(binary_records) + len(continuous_records)} records) to {output_path}")

def generate_synthetic_dataset(seed: int = SEED) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generate the full synthetic dataset.
    
    Args:
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (binary_records, continuous_records)
    """
    set_seeds(seed)
    
    binary_records = []
    continuous_records = []
    
    # Generate binary records
    logger.info(f"Generating {NUM_BINARY_RECORDS} binary outcome records...")
    for i in range(NUM_BINARY_RECORDS):
        is_consistent = random.random() < CONSISTENCY_RATE
        domain = random.choice(DOMAINS)
        record = generate_binary_test_record(is_consistent, domain, i)
        binary_records.append(record)
    
    # Generate continuous records
    logger.info(f"Generating {NUM_CONTINUOUS_RECORDS} continuous outcome records...")
    for i in range(NUM_CONTINUOUS_RECORDS):
        is_consistent = random.random() < CONSISTENCY_RATE
        domain = random.choice(DOMAINS)
        record = generate_continuous_test_record(is_consistent, domain, i + NUM_BINARY_RECORDS)
        continuous_records.append(record)
    
    logger.info(f"Generated {len(binary_records)} binary and {len(continuous_records)} continuous records")
    
    return binary_records, continuous_records

def main() -> None:
    """Entry point for synthetic valid dataset generation."""
    set_rng_seed(SEED)
    
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting synthetic dataset generation...")
    
    binary_records, continuous_records = generate_synthetic_dataset(SEED)
    
    # Write outputs
    binary_path = output_dir / "ab_summaries_binary.csv"
    continuous_path = output_dir / "ab_summaries_continuous.csv"
    combined_path = output_dir / "ab_summaries_combined.json"
    
    write_binary_csv(binary_records, binary_path)
    write_continuous_csv(continuous_records, continuous_path)
    write_combined_json(binary_records, continuous_records, combined_path)
    
    # Verify record counts
    total_records = len(binary_records) + len(continuous_records)
    if total_records < 10000:
        logger.error(f"Total records {total_records} is less than required 10,000")
        raise ValueError(f"Generated {total_records} records, expected at least 10,000")
    
    logger.info(f"Successfully generated {total_records} synthetic records (≥10,000 requirement met)")
    logger.info(f"Binary records: {len(binary_records)}")
    logger.info(f"Continuous records: {len(continuous_records)}")
    logger.info(f"Consistency rate: {CONSISTENCY_RATE*100:.1f}%")
    logger.info("Synthetic dataset generation complete.")

if __name__ == "__main__":
    main()
