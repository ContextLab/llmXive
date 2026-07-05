"""
Synthetic Dataset Generator for A/B Test Audit Validation (FR-030).

Generates at least 10,000 simulated A/B test summaries containing both
binary and continuous outcomes with realistic statistical properties.
Ensures reproducibility via seeded RNGs and deterministic output.
"""
import csv
import json
import logging
import random
import math
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger()

# Configuration constants
MIN_BINARY_COUNT = 5000
MIN_CONTINUOUS_COUNT = 5000
TOTAL_MIN_COUNT = 10000
OUTPUT_DIR = Path("data")
SYNTHETIC_CSV_PATH = OUTPUT_DIR / "synthetic_summaries.csv"
SYNTHETIC_JSON_PATH = OUTPUT_DIR / "synthetic_summaries.json"
METADATA_PATH = OUTPUT_DIR / "synthetic_metadata.json"

# Statistical parameters for generation
# Binary outcomes: baseline rates and effect sizes
BINARY_BASELINE_RATES = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50]
BINARY_EFFECT_SIZES = [-0.05, -0.02, 0.0, 0.02, 0.05, 0.10]  # Relative differences

# Continuous outcomes: means and standard deviations
CONTINUOUS_MEANS = [10.0, 25.0, 50.0, 100.0, 500.0]
CONTINUOUS_STD_DEVS = [2.0, 5.0, 10.0, 20.0, 50.0]
CONTINUOUS_EFFECT_SIZES = [-0.1, -0.05, 0.0, 0.05, 0.1, 0.2]  # Cohen's d

# Sample size distributions
SAMPLE_SIZE_MIN = 100
SAMPLE_SIZE_MAX = 5000
SAMPLE_SIZE_MEAN = 1000
SAMPLE_SIZE_STD = 300

# Domain distribution for realism
DOMAINS = [
    "tech-news", "e-commerce", "finance", "health", "social-media",
    "education", "gaming", "entertainment", "politics", "science"
]
DOMAIN_WEIGHTS = [0.20, 0.20, 0.15, 0.10, 0.10, 0.08, 0.05, 0.05, 0.04, 0.03]

# Year distribution (recent 5 years)
YEARS = list(range(2020, 2026))
YEAR_WEIGHTS = [0.05, 0.10, 0.15, 0.25, 0.30, 0.15]

def set_all_seeds(seed: int = SEED) -> None:
    """Set all random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed} for reproducibility")

def generate_sample_sizes(n: int) -> List[int]:
    """Generate sample sizes for n tests, ensuring reasonable distribution."""
    sizes = np.random.normal(SAMPLE_SIZE_MEAN, SAMPLE_SIZE_STD, n)
    sizes = np.clip(sizes, SAMPLE_SIZE_MIN, SAMPLE_SIZE_MAX).astype(int)
    return sizes.tolist()

def generate_binary_outcome(
    n: int,
    baseline_rate: float,
    effect_size: float,
    true_inconsistent: bool = False
) -> Dict[str, Any]:
    """
    Generate a synthetic binary outcome A/B test.
    
    Args:
        n: Total sample size
        baseline_rate: Control group conversion rate
        effect_size: Relative effect size (positive = improvement)
        true_inconsistent: If True, deliberately create statistical inconsistency
        
    Returns:
        Dictionary with binary test metrics
    """
    # Determine sample sizes for control and treatment
    n_control = n // 2
    n_treatment = n - n_control
    
    # Calculate rates
    control_rate = baseline_rate
    treatment_rate = baseline_rate * (1 + effect_size)
    
    # Ensure rates are valid probabilities
    control_rate = max(0.001, min(0.999, control_rate))
    treatment_rate = max(0.001, min(0.999, treatment_rate))
    
    # Generate outcomes
    control_conversions = np.random.binomial(n_control, control_rate)
    treatment_conversions = np.random.binomial(n_treatment, treatment_rate)
    
    # Calculate observed rates
    obs_control_rate = control_conversions / n_control
    obs_treatment_rate = treatment_conversions / n_treatment
    
    # Calculate p-value using two-proportion z-test
    if n_control > 0 and n_treatment > 0:
        pooled_rate = (control_conversions + treatment_conversions) / n
        if pooled_rate > 0 and pooled_rate < 1:
            se = math.sqrt(pooled_rate * (1 - pooled_rate) * (1/n_control + 1/n_treatment))
            z_stat = (obs_treatment_rate - obs_control_rate) / se
            p_value = 2 * (1 - abs(stats.norm.cdf(z_stat)))
        else:
            p_value = 1.0
    else:
        p_value = 1.0
    
    # Calculate effect size (relative difference)
    if obs_control_rate > 0:
        rel_effect = (obs_treatment_rate - obs_control_rate) / obs_control_rate
    else:
        rel_effect = 0.0
    
    # If marked inconsistent, deliberately corrupt the p-value
    if true_inconsistent:
        # Make p-value significantly different from what it should be
        p_value = abs(p_value + np.random.uniform(0.1, 0.3)) % 1.0
    
    return {
        "outcome_type": "binary",
        "n_control": int(n_control),
        "n_treatment": int(n_treatment),
        "control_conversions": int(control_conversions),
        "treatment_conversions": int(treatment_conversions),
        "obs_control_rate": round(obs_control_rate, 6),
        "obs_treatment_rate": round(obs_treatment_rate, 6),
        "reported_p_value": round(p_value, 6),
        "reported_effect_size": round(rel_effect, 6),
        "true_baseline_rate": round(control_rate, 6),
        "true_effect_size": round(effect_size, 6)
    }

def generate_continuous_outcome(
    n: int,
    mean: float,
    std_dev: float,
    effect_size: float,
    true_inconsistent: bool = False
) -> Dict[str, Any]:
    """
    Generate a synthetic continuous outcome A/B test.
    
    Args:
        n: Total sample size
        mean: Control group mean
        std_dev: Standard deviation
        effect_size: Cohen's d effect size
        true_inconsistent: If True, deliberately create statistical inconsistency
        
    Returns:
        Dictionary with continuous test metrics
    """
    # Determine sample sizes for control and treatment
    n_control = n // 2
    n_treatment = n - n_control
    
    # Calculate treatment mean
    treatment_mean = mean + effect_size * std_dev
    
    # Generate samples
    control_samples = np.random.normal(mean, std_dev, n_control)
    treatment_samples = np.random.normal(treatment_mean, std_dev, n_treatment)
    
    # Calculate statistics
    control_mean = float(np.mean(control_samples))
    treatment_mean = float(np.mean(treatment_samples))
    control_std = float(np.std(control_samples, ddof=1))
    treatment_std = float(np.std(treatment_samples, ddof=1))
    
    # Calculate Welch's t-test
    if control_std > 0 and treatment_std > 0:
        se = math.sqrt((control_std**2 / n_control) + (treatment_std**2 / n_treatment))
        t_stat = (treatment_mean - control_mean) / se
        # Approximate degrees of freedom
        df_num = (control_std**2/n_control + treatment_std**2/n_treatment)**2
        df_den = ((control_std**2/n_control)**2/(n_control-1)) + ((treatment_std**2/n_treatment)**2/(n_treatment-1))
        df = df_num / df_den if df_den > 0 else n - 2
        p_value = 2 * (1 - abs(stats.t.cdf(t_stat, df)))
    else:
        p_value = 1.0
    
    # Calculate Cohen's d
    pooled_std = math.sqrt(((n_control-1)*control_std**2 + (n_treatment-1)*treatment_std**2) / (n_control + n_treatment - 2))
    if pooled_std > 0:
        cohens_d = (treatment_mean - control_mean) / pooled_std
    else:
        cohens_d = 0.0
    
    # If marked inconsistent, deliberately corrupt the p-value
    if true_inconsistent:
        p_value = abs(p_value + np.random.uniform(0.1, 0.3)) % 1.0
    
    return {
        "outcome_type": "continuous",
        "n_control": int(n_control),
        "n_treatment": int(n_treatment),
        "control_mean": round(control_mean, 6),
        "treatment_mean": round(treatment_mean, 6),
        "control_std": round(control_std, 6),
        "treatment_std": round(treatment_std, 6),
        "reported_p_value": round(p_value, 6),
        "reported_effect_size": round(cohens_d, 6),
        "true_mean": round(mean, 6),
        "true_std": round(std_dev, 6),
        "true_effect_size": round(effect_size, 6)
    }

def generate_synthetic_dataset(
    total_count: int = TOTAL_MIN_COUNT,
    binary_ratio: float = 0.5,
    inconsistent_ratio: float = 0.15
) -> List[Dict[str, Any]]:
    """
    Generate a complete synthetic dataset of A/B test summaries.
    
    Args:
        total_count: Total number of summaries to generate
        binary_ratio: Proportion of binary outcomes (default 0.5)
        inconsistent_ratio: Proportion of deliberately inconsistent tests
        
    Returns:
        List of synthetic summary dictionaries
    """
    set_all_seeds(SEED)
    
    binary_count = int(total_count * binary_ratio)
    continuous_count = total_count - binary_count
    
    # Generate sample sizes
    all_sizes = generate_sample_sizes(total_count)
    
    summaries = []
    current_size_idx = 0
    
    # Generate binary outcomes
    for i in range(binary_count):
        n = all_sizes[current_size_idx]
        current_size_idx += 1
        
        baseline = random.choice(BINARY_BASELINE_RATES)
        effect = random.choice(BINARY_EFFECT_SIZES)
        is_inconsistent = random.random() < inconsistent_ratio
        
        summary = generate_binary_outcome(n, baseline, effect, is_inconsistent)
        
        # Add metadata
        summary["test_id"] = f"synthetic_binary_{i:06d}"
        summary["domain"] = random.choices(DOMAINS, DOMAIN_WEIGHTS)[0]
        summary["year"] = random.choices(YEARS, YEAR_WEIGHTS)[0]
        summary["is_intentionally_inconsistent"] = is_inconsistent
        
        summaries.append(summary)
    
    # Generate continuous outcomes
    for i in range(continuous_count):
        n = all_sizes[current_size_idx]
        current_size_idx += 1
        
        mean = random.choice(CONTINUOUS_MEANS)
        std = random.choice(CONTINUOUS_STD_DEVS)
        effect = random.choice(CONTINUOUS_EFFECT_SIZES)
        is_inconsistent = random.random() < inconsistent_ratio
        
        summary = generate_continuous_outcome(n, mean, std, effect, is_inconsistent)
        
        # Add metadata
        summary["test_id"] = f"synthetic_continuous_{i:06d}"
        summary["domain"] = random.choices(DOMAINS, DOMAIN_WEIGHTS)[0]
        summary["year"] = random.choices(YEARS, YEAR_WEIGHTS)[0]
        summary["is_intentionally_inconsistent"] = is_inconsistent
        
        summaries.append(summary)
    
    # Shuffle to mix binary and continuous
    random.shuffle(summaries)
    
    logger.info(f"Generated {len(summaries)} synthetic summaries")
    return summaries

def write_csv_output(summaries: List[Dict[str, Any]], path: Path) -> None:
    """Write synthetic summaries to CSV format."""
    if not summaries:
        raise ValueError("No summaries to write")
    
    # Flatten nested dictionaries for CSV
    flat_summaries = []
    for s in summaries:
        flat = {}
        for k, v in s.items():
            if isinstance(v, (dict, list)):
                flat[k] = json.dumps(v)
            else:
                flat[k] = v
        flat_summaries.append(flat)
    
    # Write CSV
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=flat_summaries[0].keys())
        writer.writeheader()
        writer.writerows(flat_summaries)
    
    logger.info(f"Wrote {len(summaries)} records to {path}")

def write_json_output(summaries: List[Dict[str, Any]], path: Path) -> None:
    """Write synthetic summaries to JSON format."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(summaries, f, indent=2, default=str)
    
    logger.info(f"Wrote {len(summaries)} records to {path}")

def verify_outcome_types(summaries: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Verify that both binary and continuous outcomes are present.
    
    Returns:
        Tuple of (binary_count, continuous_count)
    """
    binary_count = sum(1 for s in summaries if s.get("outcome_type") == "binary")
    continuous_count = sum(1 for s in summaries if s.get("outcome_type") == "continuous")
    
    logger.info(f"Outcome type verification: {binary_count} binary, {continuous_count} continuous")
    
    if binary_count == 0:
        raise ValueError("No binary outcomes found in synthetic dataset")
    if continuous_count == 0:
        raise ValueError("No continuous outcomes found in synthetic dataset")
    if binary_count + continuous_count < TOTAL_MIN_COUNT:
        raise ValueError(f"Total count {binary_count + continuous_count} is less than required {TOTAL_MIN_COUNT}")
    
    return binary_count, continuous_count

def write_metadata(summaries: List[Dict[str, Any]], path: Path) -> None:
    """Write generation metadata to JSON."""
    binary_count, continuous_count = verify_outcome_types(summaries)
    
    metadata = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_count": len(summaries),
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "seed": SEED,
        "inconsistent_ratio": sum(1 for s in summaries if s.get("is_intentionally_inconsistent")) / len(summaries),
        "domains": list(set(s["domain"] for s in summaries)),
        "years": list(set(s["year"] for s in summaries)),
        "output_files": {
            "csv": str(SYNTHETIC_CSV_PATH),
            "json": str(SYNTHETIC_JSON_PATH)
        }
    }
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Wrote metadata to {path}")

def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation for T026")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate dataset
    summaries = generate_synthetic_dataset(
        total_count=TOTAL_MIN_COUNT,
        binary_ratio=0.5,
        inconsistent_ratio=0.15
    )
    
    # Write outputs
    write_csv_output(summaries, SYNTHETIC_CSV_PATH)
    write_json_output(summaries, SYNTHETIC_JSON_PATH)
    write_metadata(summaries, METADATA_PATH)
    
    # Final verification
    binary_count, continuous_count = verify_outcome_types(summaries)
    logger.info(f"SUCCESS: Generated {binary_count} binary and {continuous_count} continuous outcomes")
    logger.info(f"Total records: {len(summaries)} (≥ {TOTAL_MIN_COUNT} required)")
    
    print(f"Synthetic dataset generated successfully:")
    print(f"  - Binary outcomes: {binary_count}")
    print(f"  - Continuous outcomes: {continuous_count}")
    print(f"  - Total records: {len(summaries)}")
    print(f"  - CSV output: {SYNTHETIC_CSV_PATH}")
    print(f"  - JSON output: {SYNTHETIC_JSON_PATH}")
    print(f"  - Metadata: {METADATA_PATH}")

if __name__ == "__main__":
    main()
