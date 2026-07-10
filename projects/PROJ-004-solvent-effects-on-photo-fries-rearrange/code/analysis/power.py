"""
Power analysis for kinetic lifetime measurements.

This module implements a post-hoc power analysis for the experimental design
with n=3 replicates per solvent condition. It estimates the detectable effect
size given the observed variance and documents the statistical power of the
study to satisfy SC-007.

Given the low sample size (n=3), this analysis primarily serves to:
1. Quantify the minimum detectable effect size (MDES) at standard power levels.
2. Document the limitations of the study for the final report.
3. Provide a basis for future sample size calculations if effect sizes are confirmed.
"""
import os
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import t as t_dist

from config import get_processed_data_path, ensure_directories
from utils.logging import setup_logging

logger = logging.getLogger(__name__)


def calculate_effect_size(
    mean1: float, mean2: float, std1: float, std2: float, n1: int, n2: int
) -> Tuple[float, str]:
    """
    Calculate Cohen's d effect size for two independent groups.

    Args:
        mean1: Mean of group 1
        mean2: Mean of group 2
        std1: Standard deviation of group 1
        std2: Standard deviation of group 2
        n1: Sample size of group 1
        n2: Sample size of group 2

    Returns:
        Tuple of (Cohen's d, interpretation)
    """
    # Pooled standard deviation
    df1 = n1 - 1
    df2 = n2 - 1
    pooled_std = np.sqrt(((df1 * std1**2) + (df2 * std2**2)) / (df1 + df2))

    if pooled_std == 0:
        return 0.0, "undefined (zero variance)"

    cohens_d = abs(mean1 - mean2) / pooled_std

    # Interpretation guidelines (Cohen, 1988)
    if cohens_d < 0.2:
        interpretation = "negligible"
    elif cohens_d < 0.5:
        interpretation = "small"
    elif cohens_d < 0.8:
        interpretation = "medium"
    else:
        interpretation = "large"

    return cohens_d, interpretation


def estimate_mdes(
    n: int, alpha: float = 0.05, power: float = 0.80, two_tailed: bool = True
) -> float:
    """
    Estimate the Minimum Detectable Effect Size (MDES) for a given sample size.

    For a two-sample t-test with equal sample sizes.

    Args:
        n: Sample size per group
        alpha: Significance level
        power: Desired statistical power
        two_tailed: Whether the test is two-tailed

    Returns:
        MDES in terms of Cohen's d
    """
    df = 2 * n - 2
    t_alpha = t_dist.ppf(1 - alpha / 2, df) if two_tailed else t_dist.ppf(1 - alpha, df)
    t_beta = t_dist.ppf(power, df)

    # Approximation for MDES (Cohen's d)
    # d = (t_alpha + t_beta) * sqrt(2/n)
    mdes = (t_alpha + t_beta) * np.sqrt(2 / n)

    return mdes


def calculate_post_hoc_power(
    cohens_d: float, n: int, alpha: float = 0.05, two_tailed: bool = True
) -> float:
    """
    Calculate post-hoc power given observed effect size.

    Args:
        cohens_d: Observed Cohen's d effect size
        n: Sample size per group
        alpha: Significance level
        two_tailed: Whether the test is two-tailed

    Returns:
        Statistical power (probability of rejecting null hypothesis)
    """
    df = 2 * n - 2
    t_alpha = t_dist.ppf(1 - alpha / 2, df) if two_tailed else t_dist.ppf(1 - alpha, df)

    # Non-centrality parameter
    ncp = cohens_d * np.sqrt(n / 2)

    # Power calculation
    if two_tailed:
        # Power = P(T > t_alpha | ncp) + P(T < -t_alpha | ncp)
        # Using survival function and CDF
        power = 1 - t_dist.cdf(t_alpha, df, ncp) + t_dist.cdf(-t_alpha, df, ncp)
    else:
        power = 1 - t_dist.cdf(t_alpha, df, ncp)

    return max(0.0, min(1.0, power))


def analyze_kinetic_power(
    kinetic_data_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform power analysis on kinetic lifetime data.

    Reads processed kinetic metrics and performs power analysis for:
    1. Comparing lifetimes across solvent conditions
    2. Estimating detectable effect sizes for n=3
    3. Documenting limitations

    Args:
        kinetic_data_path: Path to kinetic_metrics.csv. If None, uses default path.

    Returns:
        Dictionary containing power analysis results
    """
    if kinetic_data_path is None:
        processed_path = get_processed_data_path()
        kinetic_data_path = processed_path / "kinetic_metrics.csv"

    if not os.path.exists(kinetic_data_path):
        logger.warning(f"Kinetic data not found at {kinetic_data_path}. "
                     "Performing theoretical power analysis only.")
        return {
            "status": "theoretical_only",
            "message": "No kinetic data found. Providing theoretical MDES for n=3.",
            "theoretical_mdes_80_power": estimate_mdes(n=3, power=0.80),
            "theoretical_mdes_90_power": estimate_mdes(n=3, power=0.90),
            "sample_size": 3,
            "limitations": [
                "With n=3 replicates, the study has low power to detect small effects.",
                "Only large effect sizes (Cohen's d > ~1.7) can be detected with 80% power.",
                "Results should be interpreted as preliminary/exploratory.",
                "Future studies should increase sample size based on observed variance."
            ]
        }

    df = pd.read_csv(kinetic_data_path)

    # Group by solvent and calculate statistics
    grouped = df.groupby('solvent')['lifetime_ns'].agg(['mean', 'std', 'count']).reset_index()

    results = {
        "status": "completed",
        "analysis_date": datetime.now(timezone.utc).isoformat(),
        "sample_size_per_group": int(grouped['count'].mean()) if not grouped.empty else 3,
        "groups_analyzed": len(grouped),
        "pairwise_comparisons": [],
        "theoretical_mdes_80_power": estimate_mdes(n=3, power=0.80),
        "theoretical_mdes_90_power": estimate_mdes(n=3, power=0.90),
        "limitations": [
            "With n=3 replicates, the study has low power to detect small effects.",
            "Only large effect sizes (Cohen's d > ~1.7) can be detected with 80% power.",
            "Results should be interpreted as preliminary/exploratory.",
            "Future studies should increase sample size based on observed variance."
        ]
    }

    # Perform pairwise comparisons
    solvents = grouped['solvent'].tolist()
    for i in range(len(solvents)):
        for j in range(i + 1, len(solvents)):
            s1 = solvents[i]
            s2 = solvents[j]

            row1 = grouped[grouped['solvent'] == s1].iloc[0]
            row2 = grouped[grouped['solvent'] == s2].iloc[0]

            cohens_d, interpretation = calculate_effect_size(
                row1['mean'], row2['mean'],
                row1['std'], row2['std'],
                row1['count'], row2['count']
            )

            power = calculate_post_hoc_power(cohens_d, min(row1['count'], row2['count']))

            results["pairwise_comparisons"].append({
                "solvent_1": s1,
                "solvent_2": s2,
                "mean_1": float(row1['mean']),
                "mean_2": float(row2['mean']),
                "std_1": float(row1['std']),
                "std_2": float(row2['std']),
                "n_1": int(row1['count']),
                "n_2": int(row2['count']),
                "cohens_d": float(cohens_d),
                "effect_size_interpretation": interpretation,
                "post_hoc_power": float(power),
                "detectable_with_current_n": "Yes" if power >= 0.80 else "No (underpowered)"
            })

    return results


def write_power_report(results: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Write power analysis results to a JSON report file.

    Args:
        results: Power analysis results dictionary
        output_path: Path for output file. If None, uses default path.

    Returns:
        Path to the written report
    """
    if output_path is None:
        processed_path = get_processed_data_path()
        output_path = processed_path / "power_analysis_report.json"
    else:
        output_path = Path(output_path)

    ensure_directories([output_path.parent])

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Power analysis report written to {output_path}")
    return str(output_path)


def main() -> None:
    """Main entry point for power analysis."""
    parser = argparse.ArgumentParser(
        description="Perform power analysis for kinetic lifetime measurements"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to kinetic_metrics.csv (default: auto-detect)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path for power analysis report (default: data/processed/power_analysis_report.json)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    logger.info("Starting power analysis for kinetic lifetime measurements")
    logger.info(f"Sample size: n=3 replicates per solvent condition")

    results = analyze_kinetic_power(args.input)

    output_path = write_power_report(results, args.output)

    # Print summary
    print("\n" + "=" * 60)
    print("POWER ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Status: {results['status']}")
    print(f"Sample size per group: {results['sample_size_per_group']}")
    print(f"Groups analyzed: {results['groups_analyzed']}")
    print(f"\nTheoretical MDES (80% power): {results['theoretical_mdes_80_power']:.3f} (Cohen's d)")
    print(f"Theoretical MDES (90% power): {results['theoretical_mdes_90_power']:.3f} (Cohen's d)")

    if results['pairwise_comparisons']:
        print(f"\nPairwise Comparisons ({len(results['pairwise_comparisons'])} pairs):")
        for comp in results['pairwise_comparisons']:
            print(f"  {comp['solvent_1']} vs {comp['solvent_2']}:")
            print(f"    Cohen's d = {comp['cohens_d']:.3f} ({comp['effect_size_interpretation']})")
            print(f"    Post-hoc power = {comp['post_hoc_power']:.2%}")
            print(f"    Detectable with n=3: {comp['detectable_with_current_n']}")

    print(f"\nReport saved to: {output_path}")
    print("=" * 60)

    if results.get('limitations'):
        print("\nLIMITATIONS (per SC-007):")
        for lim in results['limitations']:
            print(f"  - {lim}")

    logger.info("Power analysis completed successfully")


if __name__ == "__main__":
    main()
