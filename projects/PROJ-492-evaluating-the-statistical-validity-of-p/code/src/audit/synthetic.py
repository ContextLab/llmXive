"""
Synthetic Dataset Generator for A/B Test Validity Audit.

Implements FR-030: Generates at least 10,000 simulated A/B test summaries
covering both binary and continuous outcomes.

Outputs:
  - data/synthetic/binary_summaries.csv
  - data/synthetic/continuous_summaries.csv
  - data/synthetic/metadata.json
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)

# Output paths relative to project root
DATA_DIR = Path("data")
SYNTHETIC_DIR = DATA_DIR / "synthetic"
BINARY_CSV = SYNTHETIC_DIR / "binary_summaries.csv"
CONTINUOUS_CSV = SYNTHETIC_DIR / "continuous_summaries.csv"
METADATA_JSON = SYNTHETIC_DIR / "metadata.json"

# Configuration for generation
MIN_RECORDS = 10000
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
DOMAINS = ["tech", "health", "finance", "retail", "education"]
YEARS = list(range(2018, 2025))


def set_all_seeds(seed: int = SEED) -> None:
    """Initialize random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds initialized with value {seed}")


def generate_sample_sizes(min_n: int = 50, max_n: int = 50000) -> Tuple[int, int]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Uses a log-uniform distribution to simulate varying experiment sizes.
    """
    n_control = int(np.random.lognormal(mean=8, sigma=1.5))
    n_treatment = int(np.random.lognormal(mean=8, sigma=1.5))
    
    # Enforce bounds
    n_control = max(min_n, min(max_n, n_control))
    n_treatment = max(min_n, min(max_n, n_treatment))
    
    return n_control, n_treatment


def generate_binary_outcome() -> Dict[str, Any]:
    """
    Generate a synthetic binary outcome A/B test summary.
    Includes baseline rate, uplift, and calculated p-value.
    """
    n_control, n_treatment = generate_sample_sizes()
    
    # Baseline conversion rate (random between 0.05 and 0.50)
    baseline_rate = np.random.uniform(0.05, 0.50)
    
    # Uplift: mostly small positive, some negative, some near zero
    # Distribution centered near 0 with skew
    uplift = np.random.normal(loc=0.02, scale=0.04)
    treatment_rate = baseline_rate + uplift
    
    # Clamp rates to valid probability range
    treatment_rate = max(0.01, min(0.99, treatment_rate))
    
    # Calculate successes
    successes_control = int(n_control * baseline_rate)
    successes_treatment = int(n_treatment * treatment_rate)
    
    # Calculate two-proportion z-statistic and p-value
    p_pooled = (successes_control + successes_treatment) / (n_control + n_treatment)
    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))
    if se == 0:
        se = 1e-9
        
    z_stat = (treatment_rate - baseline_rate) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    # Add some noise to p-value to simulate real-world reporting variance
    noise = np.random.normal(0, 0.005)
    p_value = max(0.001, min(0.999, p_value + noise))
    
    return {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "baseline_rate": round(baseline_rate, 4),
        "treatment_rate": round(treatment_rate, 4),
        "uplift": round(treatment_rate - baseline_rate, 4),
        "p_value": round(p_value, 4),
        "domain": random.choice(DOMAINS),
        "year": random.choice(YEARS),
        "is_significant": p_value < 0.05
    }


def generate_continuous_outcome() -> Dict[str, Any]:
    """
    Generate a synthetic continuous outcome A/B test summary.
    Includes means, standard deviations, and t-test p-value.
    """
    n_control, n_treatment = generate_sample_sizes(min_n=100, max_n=10000)
    
    # Baseline mean (e.g., time on site, revenue per user)
    baseline_mean = np.random.uniform(10.0, 100.0)
    
    # Standard deviation
    baseline_std = baseline_mean * np.random.uniform(0.3, 0.8)
    
    # Uplift in terms of standard deviations (Cohen's d)
    d_effect = np.random.normal(loc=0.1, scale=0.15)
    treatment_mean = baseline_mean + (d_effect * baseline_std)
    
    # Assume similar variance for both groups for simplicity
    treatment_std = baseline_std * np.random.uniform(0.9, 1.1)
    
    # Calculate Welch's t-statistic
    se_diff = np.sqrt((baseline_std**2 / n_control) + (treatment_std**2 / n_treatment))
    if se_diff == 0:
        se_diff = 1e-9
        
    t_stat = (treatment_mean - baseline_mean) / se_diff
    
    # Degrees of freedom for Welch's t-test
    df_num = (baseline_std**2 / n_control + treatment_std**2 / n_treatment)**2
    df_den = ((baseline_std**2 / n_control)**2 / (n_control - 1)) + \
             ((treatment_std**2 / n_treatment)**2 / (n_treatment - 1))
    df = df_num / df_den if df_den > 0 else 1
    
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    
    # Add noise
    noise = np.random.normal(0, 0.005)
    p_value = max(0.001, min(0.999, p_value + noise))
    
    return {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "baseline_mean": round(baseline_mean, 4),
        "baseline_std": round(baseline_std, 4),
        "treatment_mean": round(treatment_mean, 4),
        "treatment_std": round(treatment_std, 4),
        "p_value": round(p_value, 4),
        "domain": random.choice(DOMAINS),
        "year": random.choice(YEARS),
        "is_significant": p_value < 0.05
    }


def generate_synthetic_dataset(target_count: int = MIN_RECORDS) -> Tuple[List[Dict], List[Dict]]:
    """
    Generate the full synthetic dataset.
    Returns binary and continuous records separately.
    """
    set_all_seeds()
    
    binary_records = []
    continuous_records = []
    
    total_generated = 0
    binary_target = int(target_count * BINARY_RATIO)
    continuous_target = target_count - binary_target
    
    logger.info(f"Generating {binary_target} binary and {continuous_target} continuous records...")
    
    while len(binary_records) < binary_target or len(continuous_records) < continuous_target:
        # Decide which type to generate to balance the output
        if len(binary_records) < binary_target and (len(continuous_records) >= continuous_target or random.random() < BINARY_RATIO):
            record = generate_binary_outcome()
            binary_records.append(record)
        else:
            record = generate_continuous_outcome()
            continuous_records.append(record)
        
        total_generated += 1
        
        if total_generated % 5000 == 0:
            logger.info(f"Generated {total_generated} records...")
    
    logger.info(f"Generation complete. Total: {total_generated}, Binary: {len(binary_records)}, Continuous: {len(continuous_records)}")
    return binary_records, continuous_records


def verify_outcome_types(binary_records: List[Dict], continuous_records: List[Dict]) -> bool:
    """
    Verify that both outcome types are present and counts meet minimum requirements.
    """
    if len(binary_records) < 1000:
        logger.error(f"Binary records {len(binary_records)} below minimum threshold.")
        return False
    
    if len(continuous_records) < 1000:
        logger.error(f"Continuous records {len(continuous_records)} below minimum threshold.")
        return False
    
    # Verify content
    has_binary = any(r["outcome_type"] == "binary" for r in binary_records)
    has_continuous = any(r["outcome_type"] == "continuous" for r in continuous_records)
    
    if not has_binary or not has_continuous:
        logger.error("Missing required outcome types in generated data.")
        return False
    
    logger.info(f"Verification passed: Binary={len(binary_records)}, Continuous={len(continuous_records)}")
    return True


def write_csv_output(records: List[Dict], filepath: Path) -> None:
    """Write records to CSV file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    if not records:
        logger.warning(f"No records to write to {filepath}")
        return
    
    fieldnames = list(records[0].keys())
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Wrote {len(records)} records to {filepath}")


def write_metadata(binary_count: int, continuous_count: int, filepath: Path) -> None:
    """Write generation metadata to JSON."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "total_records": binary_count + continuous_count,
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "seed": SEED,
        "domains": DOMAINS,
        "year_range": [min(YEARS), max(YEARS)]
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Wrote metadata to {filepath}")


def main() -> int:
    """Main entry point for synthetic dataset generation."""
    try:
        # Ensure output directory exists
        SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
        
        # Generate data
        binary_data, continuous_data = generate_synthetic_dataset(MIN_RECORDS)
        
        # Verify
        if not verify_outcome_types(binary_data, continuous_data):
            logger.error("Verification failed. Aborting.")
            return 1
        
        # Write outputs
        write_csv_output(binary_data, BINARY_CSV)
        write_csv_output(continuous_data, CONTINUOUS_CSV)
        write_metadata(len(binary_data), len(continuous_data), METADATA_JSON)
        
        logger.info("Synthetic dataset generation completed successfully.")
        return 0
        
    except Exception as e:
        logger.exception(f"Fatal error during generation: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
