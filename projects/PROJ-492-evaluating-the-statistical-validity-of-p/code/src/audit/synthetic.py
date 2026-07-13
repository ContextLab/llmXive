"""
Synthetic dataset generator for A/B test validation (FR-030).

Generates a large-scale synthetic corpus of A/B test summaries with
known ground truth to validate the statistical reconstruction pipeline.
Supports both binary and continuous outcomes with configurable parameters.
"""
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger
from code.src.models.data_models import ABTestSummary

logger = get_default_logger(__name__)


def set_seeds(seed: int = SEED) -> None:
    """Ensure deterministic generation."""
    random.seed(seed)
    np.random.seed(seed)


def generate_binary_summary(
    n: int,
    p_control: float,
    effect_size: float,
    domain: str,
    year: int,
    test_id: str
) -> Tuple[ABTestSummary, Dict[str, Any]]:
    """
    Generate a synthetic binary outcome A/B test summary.

    Args:
        n: Total sample size (split evenly between control and treatment)
        p_control: Baseline conversion rate for control group
        effect_size: True effect size (difference in proportions)
        domain: Source domain (e.g., 'ecommerce', 'saaas')
        year: Publication year
        test_id: Unique identifier for the test

    Returns:
        Tuple of (ABTestSummary object, ground_truth dict)
    """
    n_control = n // 2
    n_treatment = n - n_control

    p_treatment = p_control + effect_size

    # Generate counts using binomial distribution
    successes_control = np.random.binomial(n_control, p_control)
    successes_treatment = np.random.binomial(n_treatment, p_treatment)

    # Calculate observed rates
    rate_control = successes_control / n_control
    rate_treatment = successes_treatment / n_treatment
    observed_diff = rate_treatment - rate_control

    # Calculate p-value using two-proportion z-test
    # Pooled proportion for null hypothesis
    pooled_p = (successes_control + successes_treatment) / (n_control + n_treatment)
    se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_control + 1/n_treatment))
    z_stat = observed_diff / se if se > 0 else 0.0
    p_value = 2 * (1 - abs(np.random.normal(0, 1).cumsum() if False else 0))  # Placeholder
    # Use scipy for accurate p-value
    from scipy import stats
    p_value = 2 * stats.norm.sf(abs(z_stat))

    # Determine significance
    is_significant = p_value < 0.05

    summary = ABTestSummary(
        test_id=test_id,
        domain=domain,
        year=year,
        outcome_type="binary",
        n_control=n_control,
        n_treatment=n_treatment,
        metric_control=rate_control,
        metric_treatment=rate_treatment,
        p_value=p_value,
        is_significant=is_significant,
        effect_size=observed_diff,
        confidence_interval_lower=observed_diff - 1.96 * se,
        confidence_interval_upper=observed_diff + 1.96 * se,
        source_url=f"https://example.com/{domain}/{test_id}",
        extraction_status="complete",
        extraction_errors=[]
    )

    ground_truth = {
        "test_id": test_id,
        "true_effect_size": effect_size,
        "true_p_value": p_value,
        "n_control": n_control,
        "n_treatment": n_treatment,
        "p_control": p_control,
        "p_treatment": p_treatment,
        "outcome_type": "binary"
    }

    return summary, ground_truth


def generate_continuous_summary(
    n: int,
    mean_control: float,
    std_control: float,
    effect_size: float,
    domain: str,
    year: int,
    test_id: str
) -> Tuple[ABTestSummary, Dict[str, Any]]:
    """
    Generate a synthetic continuous outcome A/B test summary.

    Args:
        n: Total sample size (split evenly)
        mean_control: Mean for control group
        std_control: Standard deviation for control group
        effect_size: True difference in means
        domain: Source domain
        year: Publication year
        test_id: Unique identifier

    Returns:
        Tuple of (ABTestSummary object, ground_truth dict)
    """
    n_control = n // 2
    n_treatment = n - n_control

    mean_treatment = mean_control + effect_size

    # Generate samples
    samples_control = np.random.normal(mean_control, std_control, n_control)
    samples_treatment = np.random.normal(mean_treatment, std_control, n_treatment)

    # Calculate statistics
    mean_control_obs = np.mean(samples_control)
    mean_treatment_obs = np.mean(samples_treatment)
    std_control_obs = np.std(samples_control, ddof=1)
    std_treatment_obs = np.std(samples_treatment, ddof=1)

    observed_diff = mean_treatment_obs - mean_control_obs

    # Welch's t-test
    from scipy import stats
    t_stat, p_value = stats.ttest_ind(
        samples_control, samples_treatment, equal_var=False
    )

    # Calculate standard error and confidence interval
    se = np.sqrt((std_control_obs**2 / n_control) + (std_treatment_obs**2 / n_treatment))
    ci_lower = observed_diff - 1.96 * se
    ci_upper = observed_diff + 1.96 * se

    is_significant = p_value < 0.05

    summary = ABTestSummary(
        test_id=test_id,
        domain=domain,
        year=year,
        outcome_type="continuous",
        n_control=n_control,
        n_treatment=n_treatment,
        metric_control=mean_control_obs,
        metric_treatment=mean_treatment_obs,
        p_value=p_value,
        is_significant=is_significant,
        effect_size=observed_diff,
        confidence_interval_lower=ci_lower,
        confidence_interval_upper=ci_upper,
        source_url=f"https://example.com/{domain}/{test_id}",
        extraction_status="complete",
        extraction_errors=[]
    )

    ground_truth = {
        "test_id": test_id,
        "true_effect_size": effect_size,
        "true_p_value": p_value,
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": mean_control,
        "mean_treatment": mean_treatment,
        "std_control": std_control,
        "outcome_type": "continuous"
    }

    return summary, ground_truth


def generate_synthetic_corpus(
    n_records: int = 10000,
    binary_ratio: float = 0.6,
    output_dir: Path = Path("data/synthetic"),
    seed: int = SEED
) -> Tuple[List[ABTestSummary], List[Dict[str, Any]]]:
    """
    Generate a synthetic corpus of A/B test summaries.

    Args:
        n_records: Total number of records to generate (>= 10,000 required)
        binary_ratio: Proportion of binary outcomes (default 0.6)
        output_dir: Directory to write output files
        seed: Random seed for reproducibility

    Returns:
        Tuple of (list of ABTestSummary, list of ground_truth dicts)
    """
    if n_records < 10000:
        raise ValueError(f"FR-030 requires at least 10,000 records, got {n_records}")

    set_seeds(seed)

    output_dir.mkdir(parents=True, exist_ok=True)

    domains = ["ecommerce", "saaas", "fintech", "healthcare", "education", "media", "gaming"]
    years = list(range(2018, 2025))

    summaries: List[ABTestSummary] = []
    ground_truth: List[Dict[str, Any]] = []

    n_binary = int(n_records * binary_ratio)
    n_continuous = n_records - n_binary

    logger.info(f"Generating {n_binary} binary and {n_continuous} continuous outcomes")

    # Generate binary outcomes
    for i in range(n_binary):
        test_id = f"syn_binary_{i:06d}"
        n = np.random.randint(100, 10000)
        p_control = np.random.uniform(0.05, 0.30)
        # Mix of positive and negative effects, mostly small
        effect_size = np.random.choice([-1, 1]) * np.random.uniform(0.005, 0.05)
        domain = random.choice(domains)
        year = random.choice(years)

        summary, gt = generate_binary_summary(n, p_control, effect_size, domain, year, test_id)
        summaries.append(summary)
        ground_truth.append(gt)

    # Generate continuous outcomes
    for i in range(n_continuous):
        test_id = f"syn_continuous_{i:06d}"
        n = np.random.randint(50, 5000)
        mean_control = np.random.uniform(10.0, 100.0)
        std_control = np.random.uniform(5.0, 20.0)
        # Effect sizes in terms of standard deviation (Cohen's d)
        effect_size = np.random.choice([-1, 1]) * np.random.uniform(0.1, 0.5) * std_control
        domain = random.choice(domains)
        year = random.choice(years)

        summary, gt = generate_continuous_summary(n, mean_control, std_control, effect_size, domain, year, test_id)
        summaries.append(summary)
        ground_truth.append(gt)

    # Shuffle to mix binary and continuous
    combined = list(zip(summaries, ground_truth))
    random.shuffle(combined)
    summaries, ground_truth = zip(*combined)
    summaries = list(summaries)
    ground_truth = list(ground_truth)

    # Write synthetic summaries to JSON
    summaries_path = output_dir / "synthetic_summaries.json"
    summaries_data = [
        {
            "test_id": s.test_id,
            "domain": s.domain,
            "year": s.year,
            "outcome_type": s.outcome_type,
            "n_control": s.n_control,
            "n_treatment": s.n_treatment,
            "metric_control": s.metric_control,
            "metric_treatment": s.metric_treatment,
            "p_value": s.p_value,
            "is_significant": s.is_significant,
            "effect_size": s.effect_size,
            "confidence_interval_lower": s.confidence_interval_lower,
            "confidence_interval_upper": s.confidence_interval_upper,
            "source_url": s.source_url,
            "extraction_status": s.extraction_status,
            "extraction_errors": s.extraction_errors
        }
        for s in summaries
    ]

    with open(summaries_path, "w", encoding="utf-8") as f:
        json.dump(summaries_data, f, indent=2)

    # Write ground truth to JSON
    ground_truth_path = output_dir / "ground_truth.json"
    with open(ground_truth_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    # Write metadata
    metadata = {
        "total_records": n_records,
        "binary_count": n_binary,
        "continuous_count": n_continuous,
        "domains": domains,
        "year_range": [min(years), max(years)],
        "generation_timestamp": datetime.now().isoformat(),
        "seed": seed,
        "output_files": {
            "summaries": str(summaries_path),
            "ground_truth": str(ground_truth_path)
        }
    }

    metadata_path = output_dir / "synthetic_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Generated {len(summaries)} synthetic records to {output_dir}")
    logger.info(f"  - Summaries: {summaries_path}")
    logger.info(f"  - Ground Truth: {ground_truth_path}")
    logger.info(f"  - Metadata: {metadata_path}")

    return summaries, ground_truth


def main() -> None:
    """Entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation (FR-030)")

    output_dir = Path("data/synthetic")
    n_records = 10000

    try:
        summaries, ground_truth = generate_synthetic_corpus(
            n_records=n_records,
            output_dir=output_dir,
            seed=SEED
        )
        logger.info(f"Successfully generated {len(summaries)} records")
    except Exception as e:
        logger.error(f"Failed to generate synthetic corpus: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
