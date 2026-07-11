"""
Synthetic dataset generator for FR-030.
Generates ≥10,000 synthetic A/B test summaries with binary and continuous outcomes.
Ensures constraint preservation for statistical validity testing.
"""
import csv
import json
import logging
import math
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)

# Constants for synthetic data generation
MIN_SAMPLE_SIZE = 100
MAX_SAMPLE_SIZE = 50000
BASELINE_RATE_MIN = 0.05
BASELINE_RATE_MAX = 0.50
EFFECT_SIZE_MIN = 0.01
EFFECT_SIZE_MAX = 0.20
CONTINUOUS_MEAN_MIN = 0.0
CONTINUOUS_MEAN_MAX = 100.0
CONTINUOUS_STD_MIN = 5.0
CONTINUOUS_STD_MAX = 30.0

def set_all_seeds(seed: int = SEED) -> None:
    """Set all random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    set_rng_seed(seed)
    logger.info(f"All random seeds set to {seed}")

def generate_sample_sizes(n_records: int) -> List[Tuple[int, int]]:
    """Generate sample sizes for control and treatment groups."""
    sizes = []
    for _ in range(n_records):
        # Vary sample sizes to create realistic diversity
        base_size = random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
        # Treatment group size varies between 80% and 120% of control
        control_size = base_size
        treatment_size = int(base_size * random.uniform(0.8, 1.2))
        sizes.append((control_size, treatment_size))
    return sizes

def generate_binary_outcome(
    n_records: int,
    sample_sizes: List[Tuple[int, int]],
    include_inconsistent: bool = True,
    inconsistency_rate: float = 0.15
) -> List[Dict[str, Any]]:
    """
    Generate binary outcome A/B test summaries.
    
    Args:
        n_records: Number of records to generate
        sample_sizes: List of (control_size, treatment_size) tuples
        include_inconsistent: Whether to include statistically inconsistent records
        inconsistency_rate: Proportion of records that should be inconsistent
        
    Returns:
        List of dictionaries containing synthetic summary data
    """
    records = []
    n_inconsistent = int(n_records * inconsistency_rate)
    
    for i in range(n_records):
        control_size, treatment_size = sample_sizes[i]
        
        # Determine if this record should be inconsistent
        is_inconsistent = i < n_inconsistent
        
        # Generate baseline conversion rate
        baseline_rate = random.uniform(BASELINE_RATE_MIN, BASELINE_RATE_MAX)
        
        # Generate effect size
        if is_inconsistent:
            # For inconsistent records, use a larger effect that won't match the p-value
            true_effect = random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX)
            reported_effect = random.uniform(EFFECT_SIZE_MIN * 0.5, EFFECT_SIZE_MAX * 1.5)
        else:
            true_effect = random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX)
            reported_effect = true_effect
        
        # Calculate actual conversion rates
        control_rate = baseline_rate
        treatment_rate = baseline_rate + true_effect
        treatment_rate = min(max(treatment_rate, 0.0), 1.0)
        
        # Generate observed successes
        control_successes = int(control_size * control_rate)
        treatment_successes = int(treatment_size * treatment_rate)
        
        # Calculate true p-value using two-proportion z-test
        try:
            pooled_rate = (control_successes + treatment_successes) / (control_size + treatment_size)
            se = math.sqrt(pooled_rate * (1 - pooled_rate) * (1/control_size + 1/treatment_size))
            if se > 0:
                z_stat = (treatment_rate - control_rate) / se
                true_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
            else:
                true_p_value = 1.0
        except Exception:
            true_p_value = 1.0
        
        # For inconsistent records, report a different p-value
        if is_inconsistent:
            # Report a p-value that doesn't match the observed data
            reported_p_value = random.uniform(0.001, 0.5)
        else:
            reported_p_value = true_p_value
        
        # Calculate confidence interval for effect size
        se_effect = math.sqrt(
            (control_rate * (1 - control_rate) / control_size) +
            (treatment_rate * (1 - treatment_rate) / treatment_size)
        )
        ci_lower = reported_effect - 1.96 * se_effect
        ci_upper = reported_effect + 1.96 * se_effect
        
        record = {
            'outcome_type': 'binary',
            'control_sample_size': control_size,
            'treatment_sample_size': treatment_size,
            'control_successes': control_successes,
            'treatment_successes': treatment_successes,
            'baseline_rate': round(control_rate, 6),
            'effect_size': round(reported_effect, 6),
            'p_value': round(reported_p_value, 6),
            'ci_lower': round(ci_lower, 6),
            'ci_upper': round(ci_upper, 6),
            'is_inconsistent': is_inconsistent,
            'true_p_value': round(true_p_value, 6)
        }
        records.append(record)
    
    return records

def generate_continuous_outcome(
    n_records: int,
    sample_sizes: List[Tuple[int, int]],
    include_inconsistent: bool = True,
    inconsistency_rate: float = 0.15
) -> List[Dict[str, Any]]:
    """
    Generate continuous outcome A/B test summaries.
    
    Args:
        n_records: Number of records to generate
        sample_sizes: List of (control_size, treatment_size) tuples
        include_inconsistent: Whether to include statistically inconsistent records
        inconsistency_rate: Proportion of records that should be inconsistent
        
    Returns:
        List of dictionaries containing synthetic summary data
    """
    records = []
    n_inconsistent = int(n_records * inconsistency_rate)
    
    for i in range(n_records):
        control_size, treatment_size = sample_sizes[i]
        
        # Determine if this record should be inconsistent
        is_inconsistent = i < n_inconsistent
        
        # Generate baseline mean and standard deviation
        baseline_mean = random.uniform(CONTINUOUS_MEAN_MIN, CONTINUOUS_MEAN_MAX)
        baseline_std = random.uniform(CONTINUOUS_STD_MIN, CONTINUOUS_STD_MAX)
        
        # Generate effect size (difference in means)
        if is_inconsistent:
            true_effect = random.uniform(EFFECT_SIZE_MIN * baseline_std, EFFECT_SIZE_MAX * baseline_std)
            reported_effect = random.uniform(EFFECT_SIZE_MIN * baseline_std * 0.5, 
                                             EFFECT_SIZE_MAX * baseline_std * 1.5)
        else:
            true_effect = random.uniform(EFFECT_SIZE_MIN * baseline_std, EFFECT_SIZE_MAX * baseline_std)
            reported_effect = true_effect
        
        # Calculate actual means
        control_mean = baseline_mean
        treatment_mean = baseline_mean + true_effect
        
        # Generate observed data (simulate samples to get realistic statistics)
        control_data = np.random.normal(control_mean, baseline_std, control_size)
        treatment_data = np.random.normal(treatment_mean, baseline_std, treatment_size)
        
        # Calculate observed statistics
        control_obs_mean = float(np.mean(control_data))
        control_obs_std = float(np.std(control_data, ddof=1))
        treatment_obs_mean = float(np.mean(treatment_data))
        treatment_obs_std = float(np.std(treatment_data, ddof=1))
        
        # Calculate true p-value using Welch's t-test
        try:
            t_stat, true_p_value = stats.ttest_ind_from_stats(
                control_obs_mean, control_obs_std, control_size,
                treatment_obs_mean, treatment_obs_std, treatment_size,
                equal_var=False
            )
        except Exception:
            true_p_value = 1.0
        
        # For inconsistent records, report a different p-value
        if is_inconsistent:
            reported_p_value = random.uniform(0.001, 0.5)
        else:
            reported_p_value = true_p_value
        
        # Calculate confidence interval for effect size
        se_effect = math.sqrt(
            (control_obs_std ** 2 / control_size) + 
            (treatment_obs_std ** 2 / treatment_size)
        )
        ci_lower = reported_effect - 1.96 * se_effect
        ci_upper = reported_effect + 1.96 * se_effect
        
        record = {
            'outcome_type': 'continuous',
            'control_sample_size': control_size,
            'treatment_sample_size': treatment_size,
            'control_mean': round(control_obs_mean, 6),
            'control_std': round(control_obs_std, 6),
            'treatment_mean': round(treatment_obs_mean, 6),
            'treatment_std': round(treatment_obs_std, 6),
            'effect_size': round(reported_effect, 6),
            'p_value': round(reported_p_value, 6),
            'ci_lower': round(ci_lower, 6),
            'ci_upper': round(ci_upper, 6),
            'is_inconsistent': is_inconsistent,
            'true_p_value': round(true_p_value, 6)
        }
        records.append(record)
    
    return records

def generate_synthetic_dataset(
    n_records: int = 10000,
    binary_ratio: float = 0.5,
    output_dir: Path = Path("data/synthetic"),
    seed: int = SEED
) -> Tuple[Path, Path]:
    """
    Generate a synthetic dataset with both binary and continuous outcomes.
    
    Args:
        n_records: Total number of records to generate (minimum 10,000)
        binary_ratio: Proportion of records that are binary outcomes
        output_dir: Directory to write output files
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (synthetic_data_path, metadata_path)
    """
    if n_records < 10000:
        n_records = 10000
        logger.warning(f"Minimum record count enforced: {n_records}")
    
    set_all_seeds(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate sample sizes
    sample_sizes = generate_sample_sizes(n_records)
    
    # Calculate record counts for each outcome type
    n_binary = int(n_records * binary_ratio)
    n_continuous = n_records - n_binary
    
    logger.info(f"Generating {n_binary} binary and {n_continuous} continuous records")
    
    # Generate binary outcomes
    binary_records = generate_binary_outcome(n_binary, sample_sizes[:n_binary])
    
    # Generate continuous outcomes
    continuous_records = generate_continuous_outcome(
        n_continuous, 
        sample_sizes[n_binary:]
    )
    
    # Combine all records
    all_records = binary_records + continuous_records
    
    # Shuffle to mix outcome types
    random.shuffle(all_records)
    
    # Write synthetic data to CSV
    synthetic_data_path = output_dir / "synthetic_ab_tests.csv"
    write_summaries_to_csv(all_records, synthetic_data_path)
    
    # Write metadata
    metadata = {
        'generated_at': datetime.utcnow().isoformat(),
        'seed': seed,
        'total_records': len(all_records),
        'binary_records': len(binary_records),
        'continuous_records': len(continuous_records),
        'binary_ratio': binary_ratio,
        'inconsistency_rate': 0.15,
        'sample_size_range': [MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE],
        'constraints': {
            'min_sample_size': MIN_SAMPLE_SIZE,
            'max_sample_size': MAX_SAMPLE_SIZE,
            'baseline_rate_range': [BASELINE_RATE_MIN, BASELINE_RATE_MAX],
            'effect_size_range': [EFFECT_SIZE_MIN, EFFECT_SIZE_MAX]
        }
    }
    metadata_path = output_dir / "synthetic_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Generated {len(all_records)} synthetic records")
    logger.info(f"Synthetic data written to {synthetic_data_path}")
    logger.info(f"Metadata written to {metadata_path}")
    
    return synthetic_data_path, metadata_path

def verify_outcome_types(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """Verify that records contain both binary and continuous outcomes."""
    counts = {'binary': 0, 'continuous': 0, 'other': 0}
    for record in records:
        outcome_type = record.get('outcome_type', 'other')
        if outcome_type in counts:
            counts[outcome_type] += 1
        else:
            counts['other'] += 1
    return counts

def write_summaries_to_csv(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic records to CSV file."""
    if not records:
        logger.warning("No records to write")
        return
    
    # Get all field names from the first record
    fieldnames = list(records[0].keys())
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def write_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """Write metadata to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation")
    
    # Default parameters
    n_records = 10000
    binary_ratio = 0.5
    output_dir = Path("data/synthetic")
    seed = SEED
    
    # Parse command line arguments if provided
    import sys
    if len(sys.argv) > 1:
        n_records = int(sys.argv[1])
    if len(sys.argv) > 2:
        binary_ratio = float(sys.argv[2])
    if len(sys.argv) > 3:
        output_dir = Path(sys.argv[3])
    if len(sys.argv) > 4:
        seed = int(sys.argv[4])
    
    try:
        synthetic_path, metadata_path = generate_synthetic_dataset(
            n_records=n_records,
            binary_ratio=binary_ratio,
            output_dir=output_dir,
            seed=seed
        )
        
        # Verify output
        if not synthetic_path.exists():
            raise FileNotFoundError(f"Synthetic data file not created: {synthetic_path}")
        
        # Count records
        with open(synthetic_path, 'r') as f:
            reader = csv.DictReader(f)
            record_count = sum(1 for _ in reader)
        
        if record_count < 10000:
            raise ValueError(f"Generated {record_count} records, expected ≥10000")
        
        logger.info(f"Successfully generated {record_count} records")
        logger.info(f"Output files: {synthetic_path}, {metadata_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}")
        raise

if __name__ == "__main__":
    main()
