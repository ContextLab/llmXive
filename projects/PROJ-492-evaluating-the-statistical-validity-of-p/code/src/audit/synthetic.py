"""
Synthetic Dataset Generator for A/B Test Validation (FR-030).

Generates a large corpus of simulated A/B test summaries with both binary
and continuous outcomes to validate the statistical consistency pipeline.
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

# Import project configuration and logging
from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

# Initialize logger
logger: AuditLogger = get_default_logger(__name__)

def set_all_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds set to {seed}")

def generate_sample_sizes(n_total: int = 10000) -> List[Tuple[int, int]]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Returns a list of (n_control, n_treatment) tuples.
    """
    sizes = []
    for _ in range(n_total):
        # Sample sizes between 50 and 5000, skewed towards smaller tests
        n_control = int(np.random.lognormal(mean=5.0, sigma=1.0))
        n_control = max(50, min(n_control, 5000))
        
        # Treatment size often similar to control, sometimes different
        ratio = np.random.beta(2, 2) * 2.0  # Range roughly 0 to 2
        n_treatment = int(n_control * ratio)
        n_treatment = max(50, min(n_treatment, 5000))
        
        sizes.append((n_control, n_treatment))
    return sizes

def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: float,
    effect_size: float,
    is_inconsistent: bool = False
) -> Dict[str, Any]:
    """
    Generate binary outcome data (conversions).
    If is_inconsistent is True, we deliberately introduce a discrepancy
    between the reported p-value and the actual data.
    """
    p_control = baseline_rate
    p_treatment = baseline_rate + effect_size
    p_treatment = max(0.0, min(1.0, p_treatment))

    # Generate actual conversions
    x_control = np.random.binomial(n_control, p_control)
    x_treatment = np.random.binomial(n_treatment, p_treatment)

    # Calculate true statistics
    prop_control = x_control / n_control
    prop_treatment = x_treatment / n_treatment
    
    # Two-proportion z-test
    stat, p_value_true = stats.proportions_ztest(
        [x_control, x_treatment], [n_control, n_treatment]
    )

    # Calculate effect size (absolute difference)
    effect_observed = prop_treatment - prop_control

    # Determine reported values
    if is_inconsistent:
        # Deliberately report a p-value that is significantly different
        # e.g., report 0.01 when it should be 0.5, or vice versa
        if p_value_true < 0.05:
            p_value_reported = 0.45  # Hide significance
        else:
            p_value_reported = 0.01  # Fake significance
        effect_reported = effect_observed * 1.5  # Exaggerate effect
    else:
        p_value_reported = p_value_true
        effect_reported = effect_observed

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "conversions_control": int(x_control),
        "conversions_treatment": int(x_treatment),
        "baseline_rate": p_control,
        "reported_p_value": round(float(p_value_reported), 4),
        "reported_effect_size": round(float(effect_reported), 6),
        "true_p_value": round(float(p_value_true), 6),
        "outcome_type": "binary"
    }

def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    baseline_mean: float,
    baseline_std: float,
    effect_size: float,
    is_inconsistent: bool = False
) -> Dict[str, Any]:
    """
    Generate continuous outcome data (e.g., revenue, time on site).
    """
    mean_control = baseline_mean
    mean_treatment = baseline_mean + effect_size
    std_control = baseline_std
    std_treatment = baseline_std  # Assume equal variance for simplicity

    # Generate samples
    sample_control = np.random.normal(mean_control, std_control, n_control)
    sample_treatment = np.random.normal(mean_treatment, std_treatment, n_treatment)

    # Calculate true statistics
    stat, p_value_true = stats.ttest_ind(sample_control, sample_treatment, equal_var=True)
    
    mean_observed_control = np.mean(sample_control)
    mean_observed_treatment = np.mean(sample_treatment)
    effect_observed = mean_observed_treatment - mean_observed_control

    # Determine reported values
    if is_inconsistent:
        if p_value_true < 0.05:
            p_value_reported = 0.45
        else:
            p_value_reported = 0.01
        effect_reported = effect_observed * 1.5
    else:
        p_value_reported = p_value_true
        effect_reported = effect_observed

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": round(float(mean_observed_control), 4),
        "mean_treatment": round(float(mean_observed_treatment), 4),
        "std_control": round(float(np.std(sample_control)), 4),
        "std_treatment": round(float(np.std(sample_treatment)), 4),
        "baseline_mean": baseline_mean,
        "reported_p_value": round(float(p_value_reported), 4),
        "reported_effect_size": round(float(effect_reported), 6),
        "true_p_value": round(float(p_value_true), 6),
        "outcome_type": "continuous"
    }

def generate_synthetic_dataset(
    n_records: int = 10000,
    output_dir: Path = None,
    inconsistency_rate: float = 0.15
) -> List[Dict[str, Any]]:
    """
    Generate the full synthetic dataset.
    Mixes binary and continuous outcomes.
    """
    if output_dir is None:
        output_dir = Path("code/data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    set_all_seeds()
    logger.info(f"Generating {n_records} synthetic summaries...")

    records = []
    domains = ["ecommerce", "media", "fintech", "healthtech", "saas"]
    years = list(range(2018, 2025))

    for i in range(n_records):
        # Determine outcome type (50/50 split)
        is_binary = np.random.rand() > 0.5
        is_inconsistent = np.random.rand() < inconsistency_rate

        # Generate sample sizes
        n_control, n_treatment = random.choice(generate_sample_sizes(1)[0])

        record_id = f"syn_{i:05d}"
        domain = random.choice(domains)
        year = random.choice(years)

        if is_binary:
            baseline = np.random.uniform(0.05, 0.30)
            effect = np.random.choice([-0.05, -0.02, 0.02, 0.05], p=[0.2, 0.3, 0.3, 0.2])
            data = generate_binary_outcome(
                n_control, n_treatment, baseline, effect, is_inconsistent
            )
        else:
            baseline = np.random.uniform(10.0, 100.0)
            effect = np.random.choice([-5.0, -2.0, 2.0, 5.0], p=[0.2, 0.3, 0.3, 0.2])
            data = generate_continuous_outcome(
                n_control, n_treatment, baseline, baseline * 0.2, effect, is_inconsistent
            )

        record = {
            "id": record_id,
            "domain": domain,
            "year": year,
            "outcome_type": data["outcome_type"],
            "n_control": data["n_control"],
            "n_treatment": data["n_treatment"],
            "reported_p_value": data["reported_p_value"],
            "reported_effect_size": data["reported_effect_size"],
            "true_p_value": data["true_p_value"], # Hidden ground truth
            "is_inconsistent": is_inconsistent,  # Hidden ground truth
            "generated_at": datetime.now().isoformat()
        }
        
        # Add specific fields based on type for downstream compatibility
        if is_binary:
            record["conversions_control"] = data["conversions_control"]
            record["conversions_treatment"] = data["conversions_treatment"]
        else:
            record["mean_control"] = data["mean_control"]
            record["mean_treatment"] = data["mean_treatment"]
            record["std_control"] = data["std_control"]
            record["std_treatment"] = data["std_treatment"]

        records.append(record)

    logger.info(f"Generated {len(records)} records.")
    return records

def verify_outcome_types(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Verify that both binary and continuous outcomes are present.
    Returns (count_binary, count_continuous).
    """
    binary_count = sum(1 for r in records if r["outcome_type"] == "binary")
    continuous_count = sum(1 for r in records if r["outcome_type"] == "continuous")
    
    logger.info(f"Verification: Binary={binary_count}, Continuous={continuous_count}")
    
    if binary_count == 0:
        raise ValueError("No binary outcomes generated.")
    if continuous_count == 0:
        raise ValueError("No continuous outcomes generated.")
        
    return binary_count, continuous_count

def write_csv_output(records: List[Dict[str, Any]], path: Path) -> None:
    """Write records to CSV."""
    if not records:
        return
    
    fieldnames = list(records[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    logger.info(f"Wrote CSV to {path}")

def write_json_output(records: List[Dict[str, Any]], path: Path) -> None:
    """Write records to JSON."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
    logger.info(f"Wrote JSON to {path}")

def write_metadata(records: List[Dict[str, Any]], path: Path) -> None:
    """Write metadata about the generated dataset."""
    binary, continuous = verify_outcome_types(records)
    metadata = {
        "total_records": len(records),
        "binary_count": binary,
        "continuous_count": continuous,
        "generation_timestamp": datetime.now().isoformat(),
        "seed": SEED,
        "inconsistency_rate": 0.15
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Wrote metadata to {path}")

def main() -> None:
    """Main entry point for the synthetic dataset generator."""
    output_dir = Path("code/data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / "synthetic_summaries.csv"
    json_path = output_dir / "synthetic_summaries.json"
    meta_path = output_dir / "synthetic_metadata.json"
    
    try:
        records = generate_synthetic_dataset(n_records=10000, output_dir=output_dir)
        
        # Verify requirements
        binary_count, continuous_count = verify_outcome_types(records)
        total_count = len(records)
        
        if total_count < 10000:
            logger.error(f"Generated {total_count} records, expected >= 10000")
            raise ValueError(f"Insufficient records: {total_count}")
        
        logger.info(f"SUCCESS: Generated {total_count} records "
                    f"(Binary: {binary_count}, Continuous: {continuous_count})")
        
        # Write outputs
        write_csv_output(records, csv_path)
        write_json_output(records, json_path)
        write_metadata(records, meta_path)
        
        logger.info("Synthetic dataset generation complete.")
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
