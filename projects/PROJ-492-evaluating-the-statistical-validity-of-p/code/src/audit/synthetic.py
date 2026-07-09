"""
Synthetic Dataset Generator (FR-030)

Generates a synthetic dataset of at least 10,000 simulated A/B test summaries.
Includes both binary and continuous outcomes with realistic statistical properties.
Outputs are written to data/synthetic/ directory.
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

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

# Constants for synthetic data generation
MIN_SAMPLE_SIZE = 100
MAX_SAMPLE_SIZE = 50000
BASELINE_PROB_MIN = 0.01
BASELINE_PROB_MAX = 0.50
EFFECT_SIZE_MIN = 0.01
EFFECT_SIZE_MAX = 0.20
CONTINUOUS_MEAN_MIN = 1.0
CONTINUOUS_MEAN_MAX = 100.0
CONTINUOUS_STD_MIN = 0.5
CONTINUOUS_STD_MAX = 20.0

# Output paths
SYNTHETIC_DATA_DIR = Path("code/data/synthetic")
SYNTHETIC_CSV_PATH = SYNTHETIC_DATA_DIR / "synthetic_summaries.csv"
SYNTHETIC_JSON_PATH = SYNTHETIC_DATA_DIR / "synthetic_summaries.json"
METADATA_PATH = SYNTHETIC_DATA_DIR / "synthetic_metadata.json"

logger = get_default_logger(__name__)

def set_all_seeds(seed: int = SEED) -> None:
    """Set all random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed}")

def generate_sample_sizes(n: int = 2) -> Tuple[int, int]:
    """Generate a pair of sample sizes for control and treatment groups."""
    n_control = random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
    n_treatment = random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
    return n_control, n_treatment

def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_prob: float,
    effect_size: float
) -> Tuple[int, int, float, float]:
    """
    Generate binary outcome data.
    
    Returns:
        successes_control, successes_treatment, p_value, effect_size_observed
    """
    # Apply effect size to baseline to get treatment probability
    p_treatment = baseline_prob + effect_size
    p_treatment = max(0.0, min(1.0, p_treatment))  # Clamp to [0, 1]
    
    # Generate successes
    successes_control = np.random.binomial(n_control, baseline_prob)
    successes_treatment = np.random.binomial(n_treatment, p_treatment)
    
    # Calculate observed proportions
    prop_control = successes_control / n_control
    prop_treatment = successes_treatment / n_treatment
    effect_size_observed = prop_treatment - prop_control
    
    # Perform two-proportion z-test
    if n_control > 0 and n_treatment > 0:
        pooled_p = (successes_control + successes_treatment) / (n_control + n_treatment)
        se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_control + 1/n_treatment))
        if se > 0:
            z_stat = (prop_treatment - prop_control) / se
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        else:
            p_value = 1.0
    else:
        p_value = 1.0
    
    return int(successes_control), int(successes_treatment), p_value, effect_size_observed

def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    mean_control: float,
    std_control: float,
    effect_size: float,
    std_treatment: Optional[float] = None
) -> Tuple[float, float, float, float]:
    """
    Generate continuous outcome data.
    
    Returns:
        mean_control, mean_treatment, p_value, effect_size_observed (Cohen's d)
    """
    if std_treatment is None:
        std_treatment = std_control * random.uniform(0.8, 1.2)
    
    mean_treatment = mean_control + effect_size * std_control
    
    # Generate samples
    sample_control = np.random.normal(mean_control, std_control, n_control)
    sample_treatment = np.random.normal(mean_treatment, std_treatment, n_treatment)
    
    # Calculate observed statistics
    mean_control_obs = np.mean(sample_control)
    mean_treatment_obs = np.mean(sample_treatment)
    std_control_obs = np.std(sample_control, ddof=1)
    std_treatment_obs = np.std(sample_treatment, ddof=1)
    
    # Welch's t-test
    if std_control_obs > 0 and std_treatment_obs > 0:
        se = np.sqrt(std_control_obs**2 / n_control + std_treatment_obs**2 / n_treatment)
        if se > 0:
            t_stat = (mean_treatment_obs - mean_control_obs) / se
            # Welch-Satterthwaite degrees of freedom
            df_num = (std_control_obs**2 / n_control + std_treatment_obs**2 / n_treatment)**2
            df_den = (std_control_obs**2 / n_control)**2 / (n_control - 1) + (std_treatment_obs**2 / n_treatment)**2 / (n_treatment - 1)
            df = df_num / df_den if df_den > 0 else 1
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
        else:
            p_value = 1.0
    else:
        p_value = 1.0
    
    # Cohen's d
    pooled_std = np.sqrt((std_control_obs**2 + std_treatment_obs**2) / 2)
    effect_size_observed = (mean_treatment_obs - mean_control_obs) / pooled_std if pooled_std > 0 else 0.0
    
    return float(mean_control_obs), float(mean_treatment_obs), p_value, float(effect_size_observed)

def generate_synthetic_dataset(
    n_records: int = 10000,
    binary_ratio: float = 0.5,
    seed: int = SEED
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.
    
    Args:
        n_records: Total number of records to generate (default: 10000)
        binary_ratio: Proportion of binary outcomes (default: 0.5)
        seed: Random seed for reproducibility
    
    Returns:
        List of dictionaries representing A/B test summaries
    """
    set_all_seeds(seed)
    
    summaries = []
    n_binary = int(n_records * binary_ratio)
    n_continuous = n_records - n_binary
    
    domains = ["ecommerce", "social_media", "news", "health", "finance", "education", "gaming", "travel"]
    test_types = ["A/B", "A/B/n", "Multivariate", "Factorial"]
    
    logger.info(f"Generating {n_binary} binary outcome records...")
    for i in range(n_binary):
        n_control, n_treatment = generate_sample_sizes()
        baseline_prob = random.uniform(BASELINE_PROB_MIN, BASELINE_PROB_MAX)
        effect_size = random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX) * random.choice([-1, 1])
        
        successes_control, successes_treatment, p_value, effect_size_obs = generate_binary_outcome(
            n_control, n_treatment, baseline_prob, effect_size
        )
        
        summary = {
            "id": f"synthetic_binary_{i:06d}",
            "url": f"https://example.com/test/binary_{i}",
            "domain": random.choice(domains),
            "test_type": random.choice(test_types),
            "outcome_type": "binary",
            "n_control": n_control,
            "n_treatment": n_treatment,
            "successes_control": successes_control,
            "successes_treatment": successes_treatment,
            "baseline_rate": baseline_prob,
            "treatment_rate": successes_treatment / n_treatment if n_treatment > 0 else 0.0,
            "reported_p_value": p_value,
            "effect_size": effect_size_obs,
            "statistical_test": "two_proportion_z_test",
            "year": random.randint(2015, 2024),
            "source": "synthetic_generator"
        }
        summaries.append(summary)
    
    logger.info(f"Generating {n_continuous} continuous outcome records...")
    for i in range(n_continuous):
        n_control, n_treatment = generate_sample_sizes()
        mean_control = random.uniform(CONTINUOUS_MEAN_MIN, CONTINUOUS_MEAN_MAX)
        std_control = random.uniform(CONTINUOUS_STD_MIN, CONTINUOUS_STD_MAX)
        effect_size = random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX) * random.choice([-1, 1])
        
        mean_control_obs, mean_treatment_obs, p_value, effect_size_obs = generate_continuous_outcome(
            n_control, n_treatment, mean_control, std_control, effect_size
        )
        
        summary = {
            "id": f"synthetic_continuous_{i:06d}",
            "url": f"https://example.com/test/continuous_{i}",
            "domain": random.choice(domains),
            "test_type": random.choice(test_types),
            "outcome_type": "continuous",
            "n_control": n_control,
            "n_treatment": n_treatment,
            "mean_control": mean_control_obs,
            "mean_treatment": mean_treatment_obs,
            "std_control": std_control,
            "std_treatment": random.uniform(std_control * 0.8, std_control * 1.2),
            "reported_p_value": p_value,
            "effect_size": effect_size_obs,
            "statistical_test": "welch_t_test",
            "year": random.randint(2015, 2024),
            "source": "synthetic_generator"
        }
        summaries.append(summary)
    
    # Shuffle to mix binary and continuous records
    random.shuffle(summaries)
    
    return summaries

def verify_outcome_types(summaries: List[Dict[str, Any]]) -> Dict[str, int]:
    """Verify that both outcome types are present in the dataset."""
    counts = {"binary": 0, "continuous": 0}
    for summary in summaries:
        outcome_type = summary.get("outcome_type")
        if outcome_type in counts:
            counts[outcome_type] += 1
        else:
            logger.warning(f"Unknown outcome type: {outcome_type}")
    
    logger.info(f"Outcome type distribution: {counts}")
    
    if counts["binary"] == 0:
        raise ValueError("No binary outcomes found in synthetic dataset")
    if counts["continuous"] == 0:
        raise ValueError("No continuous outcomes found in synthetic dataset")
    
    return counts

def write_metadata(counts: Dict[str, int], total_records: int, seed: int, output_path: Path) -> None:
    """Write metadata about the synthetic dataset."""
    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "seed": seed,
        "total_records": total_records,
        "outcome_type_counts": counts,
        "file_paths": {
            "csv": str(SYNTHETIC_CSV_PATH),
            "json": str(SYNTHETIC_JSON_PATH)
        },
        "generation_parameters": {
            "min_sample_size": MIN_SAMPLE_SIZE,
            "max_sample_size": MAX_SAMPLE_SIZE,
            "baseline_prob_range": [BASELINE_PROB_MIN, BASELINE_PROB_MAX],
            "effect_size_range": [EFFECT_SIZE_MIN, EFFECT_SIZE_MAX]
        }
    }
    
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Metadata written to {output_path}")

def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation...")
    
    # Ensure output directory exists
    SYNTHETIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate dataset
    summaries = generate_synthetic_dataset(n_records=10000, binary_ratio=0.5, seed=SEED)
    
    # Verify outcome types
    counts = verify_outcome_types(summaries)
    
    # Write CSV output
    if summaries:
        fieldnames = list(summaries[0].keys())
        with open(SYNTHETIC_CSV_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summaries)
        logger.info(f"CSV written to {SYNTHETIC_CSV_PATH} with {len(summaries)} records")
    
    # Write JSON output
    with open(SYNTHETIC_JSON_PATH, "w") as f:
        json.dump(summaries, f, indent=2)
    logger.info(f"JSON written to {SYNTHETIC_JSON_PATH}")
    
    # Write metadata
    write_metadata(counts, len(summaries), SEED, METADATA_PATH)
    
    # Final verification
    if len(summaries) >= 10000 and counts["binary"] > 0 and counts["continuous"] > 0:
        logger.info(f"SUCCESS: Generated {len(summaries)} records with {counts['binary']} binary and {counts['continuous']} continuous outcomes.")
    else:
        logger.error(f"FAILED: Requirements not met. Records: {len(summaries)}, Binary: {counts['binary']}, Continuous: {counts['continuous']}")
        raise RuntimeError("Synthetic dataset generation failed to meet requirements")

if __name__ == "__main__":
    main()
