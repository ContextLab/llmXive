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

from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

logger = get_default_logger(__name__)

def set_all_seeds(seed: int = 42) -> None:
    """Seed all random number generators for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

def generate_sample_sizes(min_n: int = 100, max_n: int = 10000, distribution: str = 'lognormal') -> Tuple[int, int]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Returns (n_control, n_treatment).
    """
    if distribution == 'lognormal':
        # Lognormal distribution for more realistic web traffic variance
        n_control = int(np.random.lognormal(mean=6.5, sigma=1.0))
        n_treatment = int(np.random.lognormal(mean=6.5, sigma=1.0))
    else:
        # Uniform distribution fallback
        n_control = random.randint(min_n, max_n)
        n_treatment = random.randint(min_n, max_n)
    
    # Ensure minimum sample size
    n_control = max(min_n, min(n_control, max_n))
    n_treatment = max(min_n, min(n_treatment, max_n))
    
    return n_control, n_treatment

def generate_binary_outcome(n_control: int, n_treatment: int, 
                            baseline_rate: float, 
                            effect_size: float,
                            is_consistent: bool = True) -> Dict[str, Any]:
    """
    Generate binary outcome A/B test data.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_rate: Conversion rate for control group (0-1)
        effect_size: Relative effect size (e.g., 0.1 for 10% increase)
        is_consistent: If True, p-value matches the statistical reality. 
                      If False, introduce inconsistency.
    
    Returns:
        Dictionary with observed metrics and p-value
    """
    # Generate true rates
    control_rate = baseline_rate
    treatment_rate = baseline_rate * (1 + effect_size)
    
    # Ensure rates are valid probabilities
    control_rate = max(0.001, min(0.999, control_rate))
    treatment_rate = max(0.001, min(0.999, treatment_rate))
    
    # Simulate outcomes
    successes_control = np.random.binomial(n_control, control_rate)
    successes_treatment = np.random.binomial(n_treatment, treatment_rate)
    
    # Calculate observed rates
    obs_control_rate = successes_control / n_control
    obs_treatment_rate = successes_treatment / n_treatment
    
    # Calculate effect size from observed data
    obs_effect_size = (obs_treatment_rate - obs_control_rate) / obs_control_rate if obs_control_rate > 0 else 0
    
    # Perform two-proportion z-test
    try:
        pooled_p = (successes_control + successes_treatment) / (n_control + n_treatment)
        se = math.sqrt(pooled_p * (1 - pooled_p) * (1/n_control + 1/n_treatment))
        if se > 0:
            z_stat = (obs_treatment_rate - obs_control_rate) / se
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        else:
            p_value = 1.0
    except Exception:
        p_value = 1.0
    
    # If inconsistent, corrupt the p-value
    if not is_consistent:
        # Introduce a significant discrepancy (> 0.05 absolute difference)
        original_p = p_value
        # Flip significance or add large noise
        if p_value < 0.05:
            p_value = random.uniform(0.15, 0.50)
        else:
            p_value = random.uniform(0.01, 0.04)
        logger.debug(f"Intentionally corrupted p-value: {original_p:.4f} -> {p_value:.4f}")
    
    return {
        'n_control': n_control,
        'n_treatment': n_treatment,
        'successes_control': int(successes_control),
        'successes_treatment': int(successes_treatment),
        'obs_control_rate': round(obs_control_rate, 6),
        'obs_treatment_rate': round(obs_treatment_rate, 6),
        'obs_effect_size': round(obs_effect_size, 6),
        'reported_p_value': round(p_value, 6),
        'true_effect_size': round(effect_size, 6),
        'is_consistent': is_consistent
    }

def generate_continuous_outcome(n_control: int, n_treatment: int,
                                baseline_mean: float,
                                baseline_std: float,
                                effect_size: float,
                                is_consistent: bool = True) -> Dict[str, Any]:
    """
    Generate continuous outcome A/B test data.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_mean: Mean for control group
        baseline_std: Standard deviation for control group
        effect_size: Cohen's d (standardized effect size)
        is_consistent: If True, p-value matches statistical reality.
    
    Returns:
        Dictionary with observed metrics and p-value
    """
    # Calculate treatment mean based on effect size (Cohen's d)
    treatment_mean = baseline_mean + (effect_size * baseline_std)
    
    # Generate data
    control_data = np.random.normal(baseline_mean, baseline_std, n_control)
    treatment_data = np.random.normal(treatment_mean, baseline_std, n_treatment)
    
    # Calculate observed statistics
    obs_mean_control = np.mean(control_data)
    obs_mean_treatment = np.mean(treatment_data)
    obs_std_control = np.std(control_data, ddof=1)
    obs_std_treatment = np.std(treatment_data, ddof=1)
    
    # Perform Welch's t-test
    try:
        t_stat, p_value = stats.ttest_ind(treatment_data, control_data, equal_var=False)
        p_value = float(p_value)
    except Exception:
        p_value = 1.0
    
    # Calculate observed effect size (Cohen's d)
    pooled_std = math.sqrt((obs_std_control**2 + obs_std_treatment**2) / 2)
    obs_effect_size = (obs_mean_treatment - obs_mean_control) / pooled_std if pooled_std > 0 else 0
    
    # If inconsistent, corrupt the p-value
    if not is_consistent:
        original_p = p_value
        if p_value < 0.05:
            p_value = random.uniform(0.15, 0.50)
        else:
            p_value = random.uniform(0.01, 0.04)
        logger.debug(f"Intentionally corrupted p-value: {original_p:.4f} -> {p_value:.4f}")
    
    return {
        'n_control': n_control,
        'n_treatment': n_treatment,
        'obs_mean_control': round(obs_mean_control, 6),
        'obs_mean_treatment': round(obs_mean_treatment, 6),
        'obs_std_control': round(obs_std_control, 6),
        'obs_std_treatment': round(obs_std_treatment, 6),
        'obs_effect_size': round(obs_effect_size, 6),
        'reported_p_value': round(p_value, 6),
        'true_effect_size': round(effect_size, 6),
        'is_consistent': is_consistent
    }

def generate_synthetic_dataset(num_records: int = 10000, 
                               binary_ratio: float = 0.5,
                               seed: int = 42,
                               inconsistency_rate: float = 0.15) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.
    
    Args:
        num_records: Total number of records to generate
        binary_ratio: Proportion of binary outcomes (0.0 to 1.0)
        seed: Random seed for reproducibility
        inconsistency_rate: Proportion of records with inconsistent p-values
    
    Returns:
        List of dictionaries containing synthetic A/B test summaries
    """
    set_all_seeds(seed)
    
    records = []
    num_binary = int(num_records * binary_ratio)
    num_continuous = num_records - num_binary
    
    # Generate binary outcomes
    for i in range(num_binary):
        n_control, n_treatment = generate_sample_sizes()
        baseline_rate = random.uniform(0.01, 0.30)
        effect_size = random.uniform(-0.3, 0.5)
        is_consistent = random.random() > inconsistency_rate
        
        record = generate_binary_outcome(
            n_control, n_treatment, baseline_rate, effect_size, is_consistent
        )
        record['outcome_type'] = 'binary'
        record['id'] = f'BIN_{i:05d}'
        record['domain'] = random.choice(['tech', 'finance', 'health', 'retail', 'education'])
        record['year'] = random.choice([2020, 2021, 2022, 2023, 2024])
        records.append(record)
    
    # Generate continuous outcomes
    for i in range(num_continuous):
        n_control, n_treatment = generate_sample_sizes()
        baseline_mean = random.uniform(10.0, 100.0)
        baseline_std = baseline_mean * random.uniform(0.1, 0.5)
        effect_size = random.uniform(-0.8, 0.8)
        is_consistent = random.random() > inconsistency_rate
        
        record = generate_continuous_outcome(
            n_control, n_treatment, baseline_mean, baseline_std, effect_size, is_consistent
        )
        record['outcome_type'] = 'continuous'
        record['id'] = f'CONT_{i:05d}'
        record['domain'] = random.choice(['tech', 'finance', 'health', 'retail', 'education'])
        record['year'] = random.choice([2020, 2021, 2022, 2023, 2024])
        records.append(record)
    
    # Shuffle the records
    random.shuffle(records)
    
    return records

def write_csv_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic records to CSV file."""
    if not records:
        raise ValueError("No records to write")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define CSV columns
    fieldnames = [
        'id', 'outcome_type', 'domain', 'year',
        'n_control', 'n_treatment',
        # Binary specific
        'successes_control', 'successes_treatment',
        'obs_control_rate', 'obs_treatment_rate',
        # Continuous specific
        'obs_mean_control', 'obs_mean_treatment',
        'obs_std_control', 'obs_std_treatment',
        # Common
        'obs_effect_size', 'true_effect_size', 'reported_p_value', 'is_consistent'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Wrote {len(records)} records to {output_path}")

def write_json_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write ground truth metadata to JSON file."""
    if not records:
        raise ValueError("No records to write")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate summary statistics for ground truth
    binary_records = [r for r in records if r['outcome_type'] == 'binary']
    continuous_records = [r for r in records if r['outcome_type'] == 'continuous']
    consistent_records = [r for r in records if r['is_consistent']]
    inconsistent_records = [r for r in records if not r['is_consistent']]
    
    ground_truth = {
        'metadata': {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'total_records': len(records),
            'binary_count': len(binary_records),
            'continuous_count': len(continuous_records),
            'consistent_count': len(consistent_records),
            'inconsistent_count': len(inconsistent_records),
            'inconsistency_rate': len(inconsistent_records) / len(records) if records else 0,
            'seed_used': 42
        },
        'domain_distribution': {},
        'year_distribution': {}
    }
    
    # Calculate domain distribution
    for domain in ['tech', 'finance', 'health', 'retail', 'education']:
        count = sum(1 for r in records if r['domain'] == domain)
        ground_truth['domain_distribution'][domain] = {
            'count': count,
            'percentage': round(count / len(records) * 100, 2) if records else 0
        }
    
    # Calculate year distribution
    for year in [2020, 2021, 2022, 2023, 2024]:
        count = sum(1 for r in records if r['year'] == year)
        ground_truth['year_distribution'][str(year)] = {
            'count': count,
            'percentage': round(count / len(records) * 100, 2) if records else 0
        }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2)
    
    logger.info(f"Wrote ground truth metadata to {output_path}")

def verify_outcome_types(records: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, int]]:
    """
    Verify that both binary and continuous outcomes are present.
    
    Returns:
        Tuple of (success, counts_dict)
    """
    counts = {
        'binary': sum(1 for r in records if r['outcome_type'] == 'binary'),
        'continuous': sum(1 for r in records if r['outcome_type'] == 'continuous')
    }
    
    success = counts['binary'] > 0 and counts['continuous'] > 0
    
    if not success:
        logger.error(f"Verification failed: binary={counts['binary']}, continuous={counts['continuous']}")
    else:
        logger.info(f"Verification passed: binary={counts['binary']}, continuous={counts['continuous']}")
    
    return success, counts

def main():
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation for T026")
    
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    output_dir = base_dir / 'data' / 'synthetic'
    csv_path = output_dir / 'synthetic_validation.csv'
    json_path = output_dir / 'synthetic_ground_truth.json'
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Generate dataset
        records = generate_synthetic_dataset(
            num_records=10000,
            binary_ratio=0.5,
            seed=42,
            inconsistency_rate=0.15
        )
        
        # Verify outcome types
        success, counts = verify_outcome_types(records)
        if not success:
            logger.error("Failed to generate both outcome types")
            raise RuntimeError("Synthetic dataset generation failed: missing outcome types")
        
        # Write outputs
        write_csv_output(records, csv_path)
        write_json_output(records, json_path)
        
        # Final verification
        if not csv_path.exists() or not json_path.exists():
            raise RuntimeError("Output files were not created")
        
        if len(records) < 10000:
            raise RuntimeError(f"Generated {len(records)} records, expected >= 10000")
        
        logger.info(f"Successfully generated {len(records)} synthetic records")
        logger.info(f"CSV output: {csv_path}")
        logger.info(f"JSON ground truth: {json_path}")
        logger.info(f"Outcome types - Binary: {counts['binary']}, Continuous: {counts['continuous']}")
        
    except Exception as e:
        logger.error(f"Error during synthetic dataset generation: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
