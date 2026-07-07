"""
Synthetic dataset generator for A/B test validation (FR-030).
Generates at least 10,000 simulated summaries with both binary and continuous outcomes.
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

# Ensure output directories exist
OUTPUT_DIR = Path("data/synthetic")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger: AuditLogger = get_default_logger()

def set_all_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    set_rng_seed(seed)
    logger.info(f"Random seeds set to {seed}")

def generate_sample_sizes(min_n: int = 100, max_n: int = 50000) -> Tuple[int, int]:
    """Generate realistic sample sizes for control and treatment groups."""
    # Log-normal distribution for more realistic sample sizes
    n_control = int(np.random.lognormal(mean=9.0, sigma=1.5))
    n_control = max(min_n, min(n_control, max_n))
    
    # Treatment size usually similar but can vary
    ratio = np.random.uniform(0.8, 1.2)
    n_treatment = int(n_control * ratio)
    n_treatment = max(min_n, min(n_treatment, max_n))
    
    return n_control, n_treatment

def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: Optional[float] = None,
    effect_size: Optional[float] = None,
    inject_inconsistency: bool = False
) -> Dict[str, Any]:
    """
    Generate binary outcome data and compute statistics.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_rate: Conversion rate for control (default: random 0.05-0.30)
        effect_size: True effect size (default: small random)
        inject_inconsistency: If True, intentionally create statistical inconsistency
    
    Returns:
        Dictionary with observed metrics and true parameters
    """
    if baseline_rate is None:
        baseline_rate = np.random.uniform(0.05, 0.30)
    
    if effect_size is None:
        # Most tests have small effects, some have none
        if np.random.random() < 0.7:
            effect_size = np.random.uniform(-0.02, 0.02)
        else:
            effect_size = np.random.choice([-1, 1]) * np.random.uniform(0.02, 0.15)
    
    treatment_rate = baseline_rate + effect_size
    treatment_rate = max(0.01, min(0.99, treatment_rate))
    
    # Generate actual successes
    successes_control = np.random.binomial(n_control, baseline_rate)
    successes_treatment = np.random.binomial(n_treatment, treatment_rate)
    
    # Calculate observed rates
    p_control = successes_control / n_control
    p_treatment = successes_treatment / n_treatment
    observed_effect = p_treatment - p_control
    
    # Calculate pooled proportion for z-test
    pooled_p = (successes_control + successes_treatment) / (n_control + n_treatment)
    se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_control + 1/n_treatment))
    
    # Calculate z-statistic and p-value
    if se > 0:
        z_stat = (p_treatment - p_control) / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    else:
        z_stat = 0.0
        p_value = 1.0
    
    # Optionally inject inconsistency
    if inject_inconsistency:
        # Corrupt the p-value slightly to create inconsistency
        p_value = p_value * np.random.uniform(0.5, 2.0)
        p_value = max(0.001, min(0.999, p_value))
    
    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "baseline_rate": round(baseline_rate, 4),
        "treatment_rate": round(treatment_rate, 4),
        "observed_effect": round(observed_effect, 4),
        "p_value": round(p_value, 6),
        "z_statistic": round(z_stat, 4),
        "outcome_type": "binary"
    }

def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    baseline_mean: Optional[float] = None,
    baseline_std: Optional[float] = None,
    effect_size: Optional[float] = None,
    inject_inconsistency: bool = False
) -> Dict[str, Any]:
    """
    Generate continuous outcome data and compute statistics.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_mean: Mean for control group (default: random 10-100)
        baseline_std: Standard deviation for control (default: 10-30% of mean)
        effect_size: True effect size (default: small random)
        inject_inconsistency: If True, intentionally create statistical inconsistency
    
    Returns:
        Dictionary with observed metrics and true parameters
    """
    if baseline_mean is None:
        baseline_mean = np.random.uniform(10.0, 100.0)
    
    if baseline_std is None:
        baseline_std = baseline_mean * np.random.uniform(0.1, 0.3)
    
    if effect_size is None:
        # Most tests have small effects
        if np.random.random() < 0.7:
            effect_size = np.random.uniform(-0.05, 0.05) * baseline_mean
        else:
            effect_size = np.random.choice([-1, 1]) * np.random.uniform(0.05, 0.20) * baseline_mean
    
    treatment_mean = baseline_mean + effect_size
    
    # Generate sample data
    control_data = np.random.normal(baseline_mean, baseline_std, n_control)
    treatment_data = np.random.normal(treatment_mean, baseline_std, n_treatment)
    
    # Calculate observed statistics
    obs_mean_control = np.mean(control_data)
    obs_mean_treatment = np.mean(treatment_data)
    obs_std_control = np.std(control_data, ddof=1)
    obs_std_treatment = np.std(treatment_data, ddof=1)
    observed_effect = obs_mean_treatment - obs_mean_control
    
    # Welch's t-test
    if obs_std_control > 0 or obs_std_treatment > 0:
        se_diff = np.sqrt((obs_std_control**2 / n_control) + (obs_std_treatment**2 / n_treatment))
        if se_diff > 0:
            t_stat = observed_effect / se_diff
            # Approximate degrees of freedom for Welch's t-test
            df_num = (obs_std_control**2 / n_control + obs_std_treatment**2 / n_treatment)**2
            df_den = ((obs_std_control**2 / n_control)**2 / (n_control - 1)) + \
                     ((obs_std_treatment**2 / n_treatment)**2 / (n_treatment - 1))
            df = df_num / df_den if df_den > 0 else n_control + n_treatment - 2
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
        else:
            t_stat = 0.0
            p_value = 1.0
    else:
        t_stat = 0.0
        p_value = 1.0
    
    # Optionally inject inconsistency
    if inject_inconsistency:
        p_value = p_value * np.random.uniform(0.5, 2.0)
        p_value = max(0.001, min(0.999, p_value))
    
    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": round(obs_mean_control, 4),
        "mean_treatment": round(obs_mean_treatment, 4),
        "std_control": round(obs_std_control, 4),
        "std_treatment": round(obs_std_treatment, 4),
        "baseline_mean": round(baseline_mean, 4),
        "treatment_mean": round(treatment_mean, 4),
        "observed_effect": round(observed_effect, 4),
        "p_value": round(p_value, 6),
        "t_statistic": round(t_stat, 4),
        "outcome_type": "continuous"
    }

def generate_synthetic_dataset(
    total_records: int = 10000,
    binary_ratio: float = 0.5,
    inconsistency_rate: float = 0.15,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.
    
    Args:
        total_records: Total number of records to generate (minimum 10,000 per FR-030)
        binary_ratio: Proportion of binary outcomes (default 0.5)
        inconsistency_rate: Proportion of records with intentional inconsistencies
        output_path: Path to write CSV (default: data/synthetic/summaries.csv)
    
    Returns:
        List of generated summary dictionaries
    """
    if total_records < 10000:
        logger.warning(f"Requested {total_records} records, but FR-030 requires at least 10,000. Adjusting to 10,000.")
        total_records = 10000
    
    set_all_seeds()
    
    records = []
    binary_count = int(total_records * binary_ratio)
    continuous_count = total_records - binary_count
    inconsistent_count = int(total_records * inconsistency_rate)
    
    logger.info(f"Generating {total_records} synthetic records:")
    logger.info(f"  - Binary outcomes: {binary_count}")
    logger.info(f"  - Continuous outcomes: {continuous_count}")
    logger.info(f"  - Inconsistent records: {inconsistent_count}")
    
    # Generate binary records
    for i in range(binary_count):
        inject_inconsistency = (i < inconsistent_count // 2)
        n_control, n_treatment = generate_sample_sizes()
        record = generate_binary_outcome(
            n_control, n_treatment,
            inject_inconsistency=inject_inconsistency
        )
        record["id"] = f"syn_binary_{i:05d}"
        record["domain"] = np.random.choice(
            ["ecommerce", "tech", "finance", "health", "media"]
        )
        record["year"] = np.random.randint(2018, 2025)
        records.append(record)
    
    # Generate continuous records
    for i in range(continuous_count):
        inject_inconsistency = (i + binary_count < inconsistent_count)
        n_control, n_treatment = generate_sample_sizes()
        record = generate_continuous_outcome(
            n_control, n_treatment,
            inject_inconsistency=inject_inconsistency
        )
        record["id"] = f"syn_continuous_{i:05d}"
        record["domain"] = np.random.choice(
            ["ecommerce", "tech", "finance", "health", "media"]
        )
        record["year"] = np.random.randint(2018, 2025)
        records.append(record)
    
    # Shuffle records
    random.shuffle(records)
    
    # Write to CSV
    if output_path is None:
        output_path = OUTPUT_DIR / "summaries.csv"
    
    write_csv_output(records, output_path)
    
    # Write metadata
    metadata = {
        "total_records": len(records),
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "inconsistent_count": inconsistent_count,
        "generated_at": datetime.now().isoformat(),
        "seed": SEED,
        "output_path": str(output_path)
    }
    
    metadata_path = OUTPUT_DIR / "synthetic_metadata.json"
    write_metadata(metadata, metadata_path)
    
    logger.info(f"Generated {len(records)} records to {output_path}")
    logger.info(f"Metadata written to {metadata_path}")
    
    return records

def verify_outcome_types(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Verify that both binary and continuous outcomes are present.
    
    Args:
        records: List of generated records
    
    Returns:
        Tuple of (binary_count, continuous_count)
    """
    binary_count = sum(1 for r in records if r.get("outcome_type") == "binary")
    continuous_count = sum(1 for r in records if r.get("outcome_type") == "continuous")
    
    logger.info(f"Verification: {binary_count} binary, {continuous_count} continuous")
    
    if binary_count == 0:
        raise ValueError("No binary outcomes found in generated dataset")
    if continuous_count == 0:
        raise ValueError("No continuous outcomes found in generated dataset")
    
    return binary_count, continuous_count

def write_csv_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write records to CSV file."""
    if not records:
        raise ValueError("No records to write")
    
    # Flatten nested dictionaries if any (currently none in our structure)
    fieldnames = list(records[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def write_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """Write metadata to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation (T026)")
    
    try:
        # Generate at least 10,000 records as required by FR-030
        records = generate_synthetic_dataset(
            total_records=10000,
            binary_ratio=0.5,
            inconsistency_rate=0.15
        )
        
        # Verify both outcome types are present
        binary_count, continuous_count = verify_outcome_types(records)
        
        total_count = len(records)
        logger.info(f"Synthetic dataset generation complete:")
        logger.info(f"  - Total records: {total_count}")
        logger.info(f"  - Binary outcomes: {binary_count}")
        logger.info(f"  - Continuous outcomes: {continuous_count}")
        
        if total_count < 10000:
            raise RuntimeError(f"Generated {total_count} records, but FR-030 requires at least 10,000")
        
        logger.info("T026 completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}")
        raise

if __name__ == "__main__":
    main()
