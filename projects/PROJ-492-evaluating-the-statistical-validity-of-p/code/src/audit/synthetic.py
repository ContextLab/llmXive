"""
Synthetic Dataset Generator for A/B Test Validity Audit (FR-030).

Generates a large-scale synthetic dataset of A/B test summaries with known ground truth
to evaluate the inconsistency detection pipeline. Produces both binary and continuous
outcome types with controlled statistical properties.
"""
import csv
import json
import logging
import random
import math
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from scipy import stats

# Import project configuration and logging
from code.src.config import set_rng_seed, get_config_summary
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Constants
DEFAULT_SEED = 42
DEFAULT_TOTAL_RECORDS = 10000
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
MIN_SAMPLE_SIZE = 100
MAX_SAMPLE_SIZE = 50000
BASELINE_RANGE = (0.01, 0.30)  # Baseline conversion rate range for binary
MEAN_RANGE = (50.0, 200.0)  # Mean range for continuous
STD_RANGE = (10.0, 50.0)  # Standard deviation range for continuous
EFFECT_SIZE_RANGE = (0.0, 0.15)  # Relative effect size range
CONSISTENT_RATIO = 0.85  # 85% of records should be statistically consistent

# Initialize logger
logger = get_default_logger(__name__)
audit_logger = AuditLogger(logger)

def set_all_seeds(seed: int = DEFAULT_SEED) -> None:
    """Set all random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds set to {seed} for reproducibility")

def generate_sample_sizes(n: int) -> List[int]:
    """Generate sample sizes for control and treatment groups."""
    # Sample sizes follow a log-normal distribution to mimic real-world variability
    log_mean = math.log(5000)
    log_std = 0.8
    sizes = np.random.lognormal(log_mean, log_std, n).astype(int)
    sizes = np.clip(sizes, MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
    return sizes.tolist()

def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: float,
    effect_size: float,
    is_consistent: bool
) -> Tuple[int, int, int, int, float, float]:
    """
    Generate binary outcome data (success/failure counts).
    
    Returns:
        control_successes, control_total, treatment_successes, treatment_total,
        reported_p_value, true_p_value
    """
    # Calculate treatment rate
    treatment_rate = baseline_rate * (1 + effect_size)
    treatment_rate = min(max(treatment_rate, 0.001), 0.999)
    
    # Generate actual successes
    control_successes = int(np.random.binomial(n_control, baseline_rate))
    treatment_successes = int(np.random.binomial(n_treatment, treatment_rate))
    
    # Calculate true p-value using two-proportion z-test
    p_pool = (control_successes + treatment_successes) / (n_control + n_treatment)
    se = math.sqrt(p_pool * (1 - p_pool) * (1/n_control + 1/n_treatment))
    if se == 0:
        true_p_value = 1.0
    else:
        z_stat = (treatment_rate - baseline_rate) / se
        true_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    # Determine reported p-value based on consistency
    if is_consistent:
        # Reported p-value should be close to true p-value (within 5% absolute difference)
        noise = np.random.normal(0, 0.01)  # Small noise
        reported_p_value = max(0.0001, min(0.9999, true_p_value + noise))
    else:
        # Introduce inconsistency: report a p-value that differs significantly
        # or report a p-value that contradicts the effect direction
        if true_p_value < 0.05:
            # True effect is significant, report non-significant
            reported_p_value = np.random.uniform(0.06, 0.50)
        else:
            # True effect is not significant, report significant
            reported_p_value = np.random.uniform(0.001, 0.04)
    
    return (
        control_successes, n_control,
        treatment_successes, n_treatment,
        round(reported_p_value, 6),
        round(true_p_value, 6)
    )

def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    mean_control: float,
    std_control: float,
    effect_size: float,
    is_consistent: bool
) -> Tuple[float, float, float, float, float, float]:
    """
    Generate continuous outcome data (means and standard deviations).
    
    Returns:
        mean_control, std_control, mean_treatment, std_treatment,
        reported_p_value, true_p_value
    """
    # Calculate treatment mean
    mean_treatment = mean_control * (1 + effect_size)
    
    # Generate sample statistics (simulating what would be observed)
    # Add small noise to standard deviations
    std_treatment = std_control * (1 + np.random.uniform(-0.1, 0.1))
    
    # Calculate true p-value using Welch's t-test
    se_diff = math.sqrt((std_control**2 / n_control) + (std_treatment**2 / n_treatment))
    if se_diff == 0:
        true_p_value = 1.0
    else:
        t_stat = (mean_treatment - mean_control) / se_diff
        # Approximate degrees of freedom for Welch's t-test
        df_num = (std_control**2/n_control + std_treatment**2/n_treatment)**2
        df_den = (std_control**2/n_control)**2/(n_control-1) + (std_treatment**2/n_treatment)**2/(n_treatment-1)
        df = df_num / df_den
        true_p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    
    # Determine reported p-value based on consistency
    if is_consistent:
        noise = np.random.normal(0, 0.01)
        reported_p_value = max(0.0001, min(0.9999, true_p_value + noise))
    else:
        if true_p_value < 0.05:
            reported_p_value = np.random.uniform(0.06, 0.50)
        else:
            reported_p_value = np.random.uniform(0.001, 0.04)
    
    return (
        round(mean_control, 4),
        round(std_control, 4),
        round(mean_treatment, 4),
        round(std_treatment, 4),
        round(reported_p_value, 6),
        round(true_p_value, 6)
    )

def generate_synthetic_dataset(
    total_records: int = DEFAULT_TOTAL_RECORDS,
    seed: int = DEFAULT_SEED
) -> List[Dict[str, Any]]:
    """
    Generate the full synthetic dataset.
    
    Returns:
        List of dictionaries containing synthetic A/B test summaries
    """
    set_all_seeds(seed)
    
    records = []
    n_binary = int(total_records * BINARY_RATIO)
    n_continuous = total_records - n_binary
    
    # Generate sample sizes
    all_sample_sizes = generate_sample_sizes(total_records)
    
    for i in range(total_records):
        is_binary = i < n_binary
        n_control = all_sample_sizes[i * 2]
        n_treatment = all_sample_sizes[i * 2 + 1] if i * 2 + 1 < len(all_sample_sizes) else n_control
        
        # Determine if this record should be consistent
        is_consistent = np.random.random() < CONSISTENT_RATIO
        
        # Generate effect size
        effect_size = np.random.uniform(EFFECT_SIZE_RANGE[0], EFFECT_SIZE_RANGE[1])
        if not is_consistent and np.random.random() < 0.3:
            # Sometimes flip the effect direction for inconsistency
            effect_size = -effect_size
        
        if is_binary:
            baseline_rate = np.random.uniform(BASELINE_RANGE[0], BASELINE_RANGE[1])
            (
                control_successes, control_total,
                treatment_successes, treatment_total,
                reported_p, true_p
            ) = generate_binary_outcome(
                n_control, n_treatment, baseline_rate, effect_size, is_consistent
            )
            
            record = {
                "id": f"synthetic_{i:06d}",
                "outcome_type": "binary",
                "is_consistent": is_consistent,
                "baseline_rate": round(baseline_rate, 4),
                "control_successes": control_successes,
                "control_total": control_total,
                "treatment_successes": treatment_successes,
                "treatment_total": treatment_total,
                "reported_p_value": reported_p,
                "true_p_value": true_p,
                "effect_size": round(effect_size, 4),
                "domain": np.random.choice(["tech", "health", "finance", "education", "retail"]),
                "year": np.random.choice([2020, 2021, 2022, 2023, 2024])
            }
        else:
            mean_control = np.random.uniform(MEAN_RANGE[0], MEAN_RANGE[1])
            std_control = np.random.uniform(STD_RANGE[0], STD_RANGE[1])
            
            (
                mean_c, std_c,
                mean_t, std_t,
                reported_p, true_p
            ) = generate_continuous_outcome(
                n_control, n_treatment, mean_control, std_control, effect_size, is_consistent
            )
            
            record = {
                "id": f"synthetic_{i:06d}",
                "outcome_type": "continuous",
                "is_consistent": is_consistent,
                "baseline_mean": mean_c,
                "baseline_std": std_c,
                "control_mean": mean_c,
                "control_std": std_c,
                "treatment_mean": mean_t,
                "treatment_std": std_t,
                "control_total": n_control,
                "treatment_total": n_treatment,
                "reported_p_value": reported_p,
                "true_p_value": true_p,
                "effect_size": round(effect_size, 4),
                "domain": np.random.choice(["tech", "health", "finance", "education", "retail"]),
                "year": np.random.choice([2020, 2021, 2022, 2023, 2024])
            }
        
        records.append(record)
    
    return records

def write_csv_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic records to CSV file."""
    if not records:
        raise ValueError("No records to write")
    
    # Flatten nested structures if any (our records are flat)
    fieldnames = list(records[0].keys())
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Wrote {len(records)} records to {output_path}")

def write_json_output(
    records: List[Dict[str, Any]],
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Write synthetic records and metadata to JSON file."""
    if not records:
        raise ValueError("No records to write")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare ground truth structure
    ground_truth = {
        "metadata": metadata or {
            "generated_at": datetime.now().isoformat(),
            "total_records": len(records),
            "seed": DEFAULT_SEED,
            "consistent_ratio": CONSISTENT_RATIO
        },
        "records": records
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2)
    
    logger.info(f"Wrote ground truth to {output_path}")

def verify_outcome_types(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Verify that both binary and continuous outcome types are present.
    
    Returns:
        Tuple of (binary_count, continuous_count)
    """
    binary_count = sum(1 for r in records if r.get("outcome_type") == "binary")
    continuous_count = sum(1 for r in records if r.get("outcome_type") == "continuous")
    
    logger.info(f"Verification: {binary_count} binary, {continuous_count} continuous records")
    
    if binary_count == 0:
        audit_logger.error("ERR-901", "No binary outcome records found in synthetic dataset")
    if continuous_count == 0:
        audit_logger.error("ERR-902", "No continuous outcome records found in synthetic dataset")
    
    return binary_count, continuous_count

def main():
    """Main entry point for synthetic dataset generation."""
    # Define paths
    base_path = Path(__file__).parent.parent.parent.parent  # code/
    output_dir = base_path / "data" / "synthetic"
    csv_path = output_dir / "synthetic_validation.csv"
    json_path = output_dir / "synthetic_ground_truth.json"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting synthetic dataset generation")
    
    # Generate dataset
    records = generate_synthetic_dataset(
        total_records=DEFAULT_TOTAL_RECORDS,
        seed=DEFAULT_SEED
    )
    
    # Verify outcome types
    binary_count, continuous_count = verify_outcome_types(records)
    
    if binary_count == 0 or continuous_count == 0:
        raise RuntimeError("Synthetic dataset missing required outcome types")
    
    # Write outputs
    write_csv_output(records, csv_path)
    write_json_output(
        records,
        json_path,
        metadata={
            "generated_at": datetime.now().isoformat(),
            "total_records": len(records),
            "binary_count": binary_count,
            "continuous_count": continuous_count,
            "seed": DEFAULT_SEED,
            "consistent_ratio": CONSISTENT_RATIO
        }
    )
    
    logger.info(f"Synthetic dataset generation complete: {len(records)} records")
    logger.info(f"  - CSV: {csv_path}")
    logger.info(f"  - JSON: {json_path}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
