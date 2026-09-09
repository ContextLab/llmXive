"""
Post-hoc power analysis for the mindfulness training impact study.

This module implements post-hoc power analysis using statsmodels to determine
whether the achieved sample size was sufficient to detect the observed effect sizes
with adequate statistical power (target ≥80%).

The analysis uses TTestPower from statsmodels.stats.power to compute:
- Achieved power for the observed effect size
- Required sample size to achieve 80% power
- Minimum detectable effect size for the current sample

Output is written to data/results/power_analysis_report.md for inclusion in methods.
"""

import os
import math
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

import numpy as np
from statsmodels.stats.power import TTestPower, TTestIndPower

from src.config.env import get_data_dir, get_config
from src.utils.logging import get_logger
from src.utils.seeding import set_seed

logger = get_logger(__name__)


@dataclass
class PowerAnalysisResult:
    """Container for power analysis results."""
    effect_size: float
    sample_size_pre: int
    sample_size_post: int
    achieved_power: float
    required_sample_size: int
    alpha: float
    target_power: float
    connection: str
    test_type: str  # 'paired' or 'independent'


def calculate_effect_size_cohens_d(
    mean_pre: float,
    mean_post: float,
    std_pre: float,
    std_post: float,
    n: int,
    paired: bool = True
) -> float:
    """
    Calculate Cohen's d effect size.

    For paired samples: d = (mean_post - mean_pre) / pooled_std
    For independent samples: d = (mean1 - mean2) / pooled_std

    Args:
        mean_pre: Mean of pre-intervention scores
        mean_post: Mean of post-intervention scores
        std_pre: Standard deviation of pre-intervention scores
        std_post: Standard deviation of post-intervention scores
        n: Sample size (number of subjects)
        paired: Whether this is a paired (within-subject) design

    Returns:
        Cohen's d effect size
    """
    if paired:
        # For paired design, we need the correlation to compute correctly
        # Using a conservative estimate of r=0.5 if not available
        # Pooled standard deviation for paired: sqrt((std1^2 + std2^2 - 2*r*std1*std2)/2)
        # Simplified: use average std
        pooled_std = (std_pre + std_post) / 2
    else:
        # For independent samples
        pooled_std = math.sqrt(((n - 1) * std_pre**2 + (n - 1) * std_post**2) / (2 * n - 2))

    if pooled_std == 0:
        return 0.0

    d = (mean_post - mean_pre) / pooled_std
    return d


def compute_post_hoc_power(
    effect_size: float,
    sample_size: int,
    alpha: float = 0.05,
    target_power: float = 0.80,
    paired: bool = True
) -> Tuple[float, int, float]:
    """
    Compute post-hoc power analysis.

    Args:
        effect_size: Cohen's d effect size
        sample_size: Number of subjects
        alpha: Significance level (default 0.05)
        target_power: Target power level (default 0.80)
        paired: Whether this is a paired t-test design

    Returns:
        Tuple of (achieved_power, required_sample_size, minimum_detectable_effect)
    """
    if paired:
        power_analysis = TTestPower()
    else:
        power_analysis = TTestIndPower()

    # Calculate achieved power
    achieved_power = power_analysis.solve_power(
        effect_size=effect_size,
        nobs1=sample_size,
        alpha=alpha,
        power=None,
        ratio=1.0
    )

    # Calculate required sample size for target power
    required_sample_size = power_analysis.solve_power(
        effect_size=effect_size,
        nobs1=None,
        alpha=alpha,
        power=target_power,
        ratio=1.0
    )

    # Calculate minimum detectable effect size for current sample
    minimum_detectable_effect = power_analysis.solve_power(
        effect_size=None,
        nobs1=sample_size,
        alpha=alpha,
        power=target_power,
        ratio=1.0
    )

    return achieved_power, int(np.ceil(required_sample_size)), minimum_detectable_effect


def run_power_analysis(
    results_data: Dict[str, Dict[str, Any]],
    alpha: float = 0.05,
    target_power: float = 0.80
) -> list:
    """
    Run post-hoc power analysis for all connectivity results.

    Args:
        results_data: Dictionary containing connectivity results with effect sizes
                     Format: {connection_name: {'effect_size': float, 'n': int, ...}}
        alpha: Significance level
        target_power: Target power level

    Returns:
        List of PowerAnalysisResult objects
    """
    set_seed(42)
    results = []

    for connection, data in results_data.items():
        effect_size = data.get('effect_size', 0.0)
        sample_size = data.get('n', 0)

        if sample_size == 0 or effect_size == 0:
            logger.warning(f"Skipping {connection}: insufficient data")
            continue

        achieved_power, required_n, min_effect = compute_post_hoc_power(
            effect_size=effect_size,
            sample_size=sample_size,
            alpha=alpha,
            target_power=target_power,
            paired=True  # This study uses paired design (pre/post)
        )

        result = PowerAnalysisResult(
            effect_size=effect_size,
            sample_size_pre=sample_size,
            sample_size_post=sample_size,
            achieved_power=achieved_power,
            required_sample_size=required_n,
            alpha=alpha,
            target_power=target_power,
            connection=connection,
            test_type='paired'
        )
        results.append(result)

        logger.info(
            f"Connection: {connection}, Effect size: {effect_size:.3f}, "
            f"Achieved power: {achieved_power:.3f}, Required N: {required_n}"
        )

    return results


def generate_methods_documentation(results: list, output_path: Path) -> None:
    """
    Generate sample-size requirements documentation for methods section.

    Args:
        results: List of PowerAnalysisResult objects
        output_path: Path to write the markdown documentation
    """
    if not results:
        logger.warning("No power analysis results to document")
        return

    # Determine overall sample size adequacy
    sufficient_power_count = sum(1 for r in results if r.achieved_power >= r.target_power)
    total_connections = len(results)

    # Calculate average achieved power
    avg_power = np.mean([r.achieved_power for r in results])
    max_required_n = max([r.required_sample_size for r in results])

    doc_content = f"""# Power Analysis Methodology and Sample Size Requirements

## Overview

This study conducted a post-hoc power analysis to evaluate whether the achieved sample
size was sufficient to detect the observed effect sizes in DMN functional connectivity
changes following mindfulness training.

## Statistical Power Parameters

- **Target Power**: 80% (0.80)
- **Significance Level (α)**: 0.05
- **Statistical Test**: Paired samples t-test (within-subject design)
- **Effect Size Metric**: Cohen's d

## Sample Size Adequacy

- **Total Subjects Analyzed**: {results[0].sample_size_pre if results else 0}
- **Average Achieved Power**: {avg_power:.1%}
- **Connections with Sufficient Power (≥80%)**: {sufficient_power_count}/{total_connections}
- **Maximum Required Sample Size**: {max_required_n} subjects

## Per-Connection Power Analysis

| Connection | Effect Size (d) | Achieved Power | Required N | Sufficient? |
|------------|-----------------|----------------|------------|-------------|
"""

    for r in results:
        sufficient = "Yes" if r.achieved_power >= r.target_power else "No"
        doc_content += f"| {r.connection} | {r.effect_size:.3f} | {r.achieved_power:.1%} | {r.required_sample_size} | {sufficient} |\n"

    doc_content += f"""

## Interpretation

{'The sample size of this study was sufficient to detect the observed effect sizes with adequate power (≥80%) for the majority of DMN connections.' if sufficient_power_count > total_connections / 2 else 'The sample size of this study provided adequate power (≥80%) for only a subset of DMN connections. Larger samples would be needed to detect smaller effect sizes with sufficient power.'}

For connections where achieved power fell below 80%, the required sample size to achieve
adequate power ranges from {min([r.required_sample_size for r in results])} to {max_required_n} subjects.

## Limitations

This post-hoc power analysis is based on the observed effect sizes from the current
sample. Future studies should consider:

1. **A priori power analysis**: Conduct power calculations before data collection
   based on expected effect sizes from previous literature.
2. **Multiple comparison correction**: The power analysis above does not account for
   multiple testing corrections. Adjusted significance thresholds would require larger
   sample sizes.
3. **Effect size variability**: Observed effect sizes may not generalize to other
   populations or intervention protocols.

## References

- Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences (2nd ed.).
- Lenth, R. V. (2001). Some Practical Guidelines for Effective Sample-Size Determination.
  The American Statistician, 55(3), 187-193.
"""

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write documentation
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(doc_content)

    logger.info(f"Power analysis documentation written to: {output_path}")


def main():
    """
    Main entry point for power analysis script.

    This script:
    1. Loads connectivity analysis results from data/results/
    2. Computes post-hoc power for each connection
    3. Generates sample-size requirements documentation
    4. Outputs report to data/results/power_analysis_report.md
    """
    set_seed(42)

    data_dir = Path(get_data_dir())
    results_dir = data_dir / "results"

    # Check for existing connectivity results
    results_file = results_dir / "connectivity_results.json"

    if not results_file.exists():
        logger.warning(
            f"Results file not found: {results_file}. "
            "Please run connectivity analysis first (T023-T027)."
        )
        # Create a minimal mock structure for demonstration if file doesn't exist
        # In production, this should fail loudly
        raise FileNotFoundError(
            f"Connectivity results not found at {results_file}. "
            "Run the connectivity analysis pipeline first."
        )

    # Load results
    import json
    with open(results_file, 'r', encoding='utf-8') as f:
        results_data = json.load(f)

    # Run power analysis
    power_results = run_power_analysis(results_data)

    if not power_results:
        logger.error("No power analysis results generated. Check input data.")
        return

    # Generate documentation
    output_path = results_dir / "power_analysis_report.md"
    generate_methods_documentation(power_results, output_path)

    # Also save raw results as JSON for programmatic access
    raw_results_path = results_dir / "power_analysis_results.json"
    raw_data = [
        {
            'connection': r.connection,
            'effect_size': r.effect_size,
            'sample_size': r.sample_size_pre,
            'achieved_power': r.achieved_power,
            'required_sample_size': r.required_sample_size,
            'alpha': r.alpha,
            'target_power': r.target_power,
            'test_type': r.test_type
        }
        for r in power_results
    ]

    with open(raw_results_path, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2)

    logger.info(f"Power analysis complete. Report saved to: {output_path}")
    logger.info(f"Raw results saved to: {raw_results_path}")


if __name__ == "__main__":
    main()